#!/usr/bin/env python3
"""
Improved MCP Server for AI-Powered Kids Storyteller with Voice Narration
Enhanced with better error handling and audio support
"""

import asyncio
import json
import logging
import os
import tempfile
import platform
import subprocess
import random
import sys
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

# MCP imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        CallToolRequestParams,
        CallToolResult,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("❌ MCP not available. Install with: pip install mcp")

# Voice synthesis imports with better error handling
voice_engines = {}

def check_pyttsx3():
    try:
        import pyttsx3
        # Test if pyttsx3 can actually initialize
        engine = pyttsx3.init()
        if engine:
            engine.stop()
            return True
    except Exception as e:
        print(f"pyttsx3 check failed: {e}")
    return False

def check_gtts():
    try:
        from gtts import gTTS
        return True
    except ImportError:
        return False

def check_edge_tts():
    try:
        import edge_tts
        return True
    except ImportError:
        return False

# Check availability
voice_engines['pyttsx3'] = check_pyttsx3()
voice_engines['gtts'] = check_gtts()
voice_engines['edge_tts'] = check_edge_tts()

# Claude integration
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class VoiceProfile:
    """Represents a voice profile with characteristics."""
    id: str
    name: str
    engine: str
    language: str = "en"
    gender: str = "neutral"
    age_group: str = "adult"
    style: str = "friendly"
    speed: float = 1.0
    pitch: float = 1.0
    system_voice_id: Optional[str] = None

@dataclass
class Story:
    """Represents a story with metadata."""
    title: str
    content: str
    moral: str
    length: int
    score: float = 0.0
    agent_id: str = ""
    generation_method: str = "template"

class AudioPlayer:
    """Enhanced cross-platform audio player."""
    
    @staticmethod
    def play_audio_file(audio_file: str) -> bool:
        """Play audio file using system-appropriate method."""
        if not audio_file or not os.path.exists(audio_file):
            logger.error(f"Audio file not found: {audio_file}")
            return False
        
        try:
            system = platform.system()
            logger.info(f"Playing audio on {system}: {audio_file}")
            
            if system == "Darwin":  # macOS
                result = subprocess.run(["afplay", audio_file], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    logger.info("Audio played successfully with afplay")
                    return True
                else:
                    logger.error(f"afplay failed: {result.stderr}")
                    
            elif system == "Linux":
                players = ["paplay", "aplay", "play", "mpg123", "ffplay"]
                for player in players:
                    try:
                        result = subprocess.run([player, audio_file], 
                                              capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            logger.info(f"Audio played successfully with {player}")
                            return True
                    except (subprocess.CalledProcessError, FileNotFoundError) as e:
                        logger.debug(f"{player} failed: {e}")
                        continue
                        
            elif system == "Windows":
                # Use Windows Media Player
                result = subprocess.run(["powershell", "-c", f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"], 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    logger.info("Audio played successfully with PowerShell")
                    return True
                else:
                    # Fallback to start command
                    subprocess.run(["start", "/wait", "", audio_file], shell=True, timeout=30)
                    return True
                    
            logger.error(f"No suitable audio player found for {system}")
            return False
            
        except subprocess.TimeoutExpired:
            logger.error("Audio playback timed out")
            return False
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
            return False

class VoiceNarrationEngine:
    """Enhanced voice synthesis engine."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.audio_player = AudioPlayer()
        self.voice_profiles = self._create_voice_profiles()
        self.system_voices = []
        self._init_system_voices()
        
        logger.info(f"Voice engines available: {[k for k, v in voice_engines.items() if v]}")
        logger.info(f"Voice profiles created: {len(self.voice_profiles)}")
    
    def _init_system_voices(self):
        """Initialize system voices for pyttsx3."""
        if voice_engines['pyttsx3']:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                if voices:
                    self.system_voices = voices
                    logger.info(f"✅ pyttsx3 initialized with {len(voices)} system voices")
                    # Log available voices
                    for i, voice in enumerate(voices[:3]):  # Show first 3
                        logger.info(f"  Voice {i}: {voice.name} ({voice.id})")
                else:
                    logger.warning("No system voices found for pyttsx3")
                engine.stop()
                del engine
            except Exception as e:
                logger.error(f"⚠️ pyttsx3 system voices init failed: {e}")
                voice_engines['pyttsx3'] = False
    
    def _create_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """Create voice profiles for available engines."""
        profiles = {}
        
        # Only create profiles for working engines
        if voice_engines['pyttsx3']:
            profiles.update({
                "narrator": VoiceProfile("narrator", "Story Narrator", "pyttsx3", 
                                       style="storyteller", speed=0.85),
                "parent": VoiceProfile("parent", "Parent Voice", "pyttsx3", 
                                     style="parent", speed=0.8),
                "child": VoiceProfile("child", "Child Voice", "pyttsx3", 
                                    age_group="child", speed=1.1),
            })
        
        if voice_engines['gtts']:
            profiles.update({
                "gtts_narrator": VoiceProfile("gtts_narrator", "Professional Narrator", "gtts"),
                "gtts_friendly": VoiceProfile("gtts_friendly", "Friendly Voice", "gtts"),
            })
        
        if voice_engines['edge_tts']:
            profiles.update({
                "edge_narrator": VoiceProfile("edge_narrator", "Edge Narrator", "edge_tts"),
                "edge_child": VoiceProfile("edge_child", "Edge Child Voice", "edge_tts", age_group="child"),
            })
        
        logger.info(f"Created {len(profiles)} voice profiles")
        return profiles
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get available voice profiles with engine status."""
        voices_by_engine = {}
        engine_status = {}
        
        for engine_name, available in voice_engines.items():
            engine_status[engine_name] = {
                "available": available,
                "reason": "Working" if available else "Not installed or not working"
            }
        
        for profile in self.voice_profiles.values():
            engine = profile.engine
            if engine not in voices_by_engine:
                voices_by_engine[engine] = []
            voices_by_engine[engine].append({
                "id": profile.id,
                "name": profile.name,
                "style": profile.style,
                "gender": profile.gender,
                "age_group": profile.age_group,
                "available": voice_engines.get(profile.engine, False)
            })
        
        return {
            "voices_by_engine": voices_by_engine,
            "engine_status": engine_status,
            "system_info": {
                "platform": platform.system(),
                "temp_dir": self.temp_dir,
                "total_profiles": len(self.voice_profiles),
                "working_engines": len([e for e, available in voice_engines.items() if available])
            }
        }
    
    async def narrate_story(self, text: str, voice_id: str = "narrator") -> Dict[str, Any]:
        """Narrate story with specified voice."""
        logger.info(f"Attempting narration with voice_id: {voice_id}")
        
        if not self.voice_profiles:
            return {
                "error": "No voice profiles available",
                "success": False,
                "debug": {
                    "available_engines": voice_engines,
                    "profiles_count": len(self.voice_profiles)
                }
            }
        
        # Find working voice
        if voice_id not in self.voice_profiles:
            working_profiles = [p for p in self.voice_profiles.values() 
                              if voice_engines.get(p.engine, False)]
            if not working_profiles:
                return {
                    "error": "No working voice engines available",
                    "success": False,
                    "available_engines": voice_engines
                }
            voice_id = working_profiles[0].id
            logger.info(f"Using fallback voice: {voice_id}")
        
        profile = self.voice_profiles[voice_id]
        
        try:
            if profile.engine == "pyttsx3" and voice_engines['pyttsx3']:
                return await self._narrate_pyttsx3(text, profile)
            elif profile.engine == "gtts" and voice_engines['gtts']:
                return await self._narrate_gtts(text, profile)
            elif profile.engine == "edge_tts" and voice_engines['edge_tts']:
                return await self._narrate_edge_tts(text, profile)
            else:
                return {
                    "error": f"Engine {profile.engine} not available",
                    "success": False,
                    "engine_status": voice_engines
                }
        except Exception as e:
            logger.error(f"Narration error: {e}")
            return {"error": str(e), "success": False}
    
    async def _narrate_pyttsx3(self, text: str, profile: VoiceProfile) -> Dict[str, Any]:
        """Narrate using pyttsx3."""
        import pyttsx3
        
        def _generate_audio():
            engine = None
            try:
                engine = pyttsx3.init()
                
                # Set properties
                rate = max(100, min(300, int(200 * profile.speed)))
                engine.setProperty('rate', rate)
                engine.setProperty('volume', 0.9)
                
                # Use first available system voice if available
                if self.system_voices:
                    engine.setProperty('voice', self.system_voices[0].id)
                
                # Generate audio file
                import time
                timestamp = int(time.time())
                audio_file = os.path.join(self.temp_dir, f"story_{timestamp}.wav")
                
                logger.info(f"Generating audio file: {audio_file}")
                engine.save_to_file(text, audio_file)
                engine.runAndWait()
                
                # Verify file was created
                if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                    logger.info(f"Audio file generated successfully: {os.path.getsize(audio_file)} bytes")
                    return audio_file
                else:
                    logger.error("Audio file was not created or is empty")
                    return None
                    
            except Exception as e:
                logger.error(f"pyttsx3 generation error: {e}")
                return None
            finally:
                if engine:
                    try:
                        engine.stop()
                        del engine
                    except:
                        pass
        
        # Generate audio in thread
        audio_file = await asyncio.to_thread(_generate_audio)
        
        if audio_file and os.path.exists(audio_file):
            return {
                "success": True,
                "engine": "pyttsx3",
                "voice_name": profile.name,
                "audio_file": audio_file,
                "file_size": os.path.getsize(audio_file),
                "duration": len(text.split()) * 0.6 / profile.speed,
                "can_play": True
            }
        else:
            return {
                "error": "Failed to generate audio file with pyttsx3",
                "success": False,
                "attempted_file": audio_file if 'audio_file' in locals() else None
            }
    
    async def _narrate_gtts(self, text: str, profile: VoiceProfile) -> Dict[str, Any]:
        """Narrate using Google TTS."""
        try:
            from gtts import gTTS
            
            def _generate_audio():
                tts = gTTS(text=text, lang=profile.language)
                import time
                timestamp = int(time.time())
                audio_file = os.path.join(self.temp_dir, f"story_{timestamp}.mp3")
                tts.save(audio_file)
                return audio_file
            
            audio_file = await asyncio.to_thread(_generate_audio)
            
            if os.path.exists(audio_file):
                return {
                    "success": True,
                    "engine": "gtts",
                    "voice_name": profile.name,
                    "audio_file": audio_file,
                    "file_size": os.path.getsize(audio_file),
                    "duration": len(text.split()) * 0.6
                }
            else:
                return {"error": "Failed to create gTTS audio file", "success": False}
                
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return {"error": str(e), "success": False}
    
    async def _narrate_edge_tts(self, text: str, profile: VoiceProfile) -> Dict[str, Any]:
        """Narrate using Edge TTS."""
        try:
            import edge_tts
            
            async def _generate_audio():
                voice = "en-US-AriaNeural"  # Default Edge voice
                communicate = edge_tts.Communicate(text, voice)
                
                import time
                timestamp = int(time.time())
                audio_file = os.path.join(self.temp_dir, f"story_{timestamp}.mp3")
                
                await communicate.save(audio_file)
                return audio_file
            
            audio_file = await _generate_audio()
            
            if os.path.exists(audio_file):
                return {
                    "success": True,
                    "engine": "edge_tts",
                    "voice_name": profile.name,
                    "audio_file": audio_file,
                    "file_size": os.path.getsize(audio_file),
                    "duration": len(text.split()) * 0.6
                }
            else:
                return {"error": "Failed to create Edge TTS audio file", "success": False}
                
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            return {"error": str(e), "success": False}

class ClaudeStoryGenerator:
    """Claude AI integration for story generation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        self.available = False
        
        if CLAUDE_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.available = True
                logger.info("✅ Claude API initialized")
            except Exception as e:
                logger.error(f"Claude init failed: {e}")
    
    async def generate_story(self, moral: str, length: int) -> Optional[str]:
        """Generate story using Claude."""
        if not self.available:
            return None
        
        prompt = f"""Write a children's story (ages 5-10) that teaches the moral value of "{moral}".

Requirements:
- Approximately {length} words
- Engaging and age-appropriate
- Clear moral lesson woven into the narrative
- Optimized for voice narration with natural speech patterns
- Include dialogue and descriptive language
- Make it fun and memorable

Write only the story, no additional notes."""
        
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.8,
                messages=[{"role": "user", "content": prompt}]
            )
            
            if response.content:
                return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude generation failed: {e}")
        
        return None

class StoryGenerator:
    """Main story generation system."""
    
    def __init__(self):
        self.claude = ClaudeStoryGenerator()
        self.templates = {
            "honesty": {
                "title": "The Truthful Treasure Hunter",
                "story": "Maya found an old map leading to treasure buried deep in the forest. When her best friend Emma asked about the crumpled paper Maya was holding, Maya felt tempted to lie and keep the treasure hunt secret. But Maya took a deep breath and chose to tell the truth. 'It's a treasure map I found in my grandmother's attic,' she said honestly. Emma's eyes lit up with excitement. 'Can we search for it together?' she asked. Maya smiled and nodded. Together, they followed the winding paths through the forest, solved riddles, and dug beneath the old oak tree. When they finally found the small chest, it was filled with shiny coins and a note from Maya's grandmother that read: 'The greatest treasure is a friend you can trust.' Maya realized that by being honest, she had shared an amazing adventure and made their friendship even stronger. From that day on, Maya and Emma knew they could always tell each other the truth."
            },
            "kindness": {
                "title": "The Kind Knight's Quest",
                "story": "Sir Alex rode through the enchanted forest on a very important quest to save the kingdom from a terrible curse. The royal wizard had told Alex that only a brave knight could retrieve the magical crystal from Dragon's Peak before sunset. As Alex hurried along the mountain path, they heard a soft crying sound coming from behind some rocks. Instead of rushing past, Alex stopped to investigate. There, huddled between two boulders, was a small dragon with tears streaming down its scaly cheeks. 'I'm lost and can't find my way home to my family,' the dragon sobbed. Most knights would have been afraid or too busy to help, but Alex had a kind heart. 'Don't worry, little friend. I'll help you,' Alex said gently. Even though it meant taking extra time, Alex helped the grateful dragon find the path back to its cave. The dragon was so thankful that it offered to help Alex with the quest. Together, they flew to Dragon's Peak, retrieved the crystal, and saved the kingdom just before sunset. Alex learned that kindness not only helps others, but often comes back to help us too."
            },
            "courage": {
                "title": "The Brave Little Explorer", 
                "story": "Sam lived in a small village at the edge of the mysterious Whispering Woods. The villagers were very sick and needed special healing herbs that only grew on the other side of the dark forest. Sam had always been afraid of the woods because of the scary stories the grown-ups told about strange sounds and shadows that moved between the trees. But when Sam saw how much pain the villagers were in, including Sam's own grandmother, something brave stirred inside. 'I have to try,' Sam whispered, taking a deep breath and stepping into the forest with a lantern and a basket. At first, every creaking branch and rustling leaf made Sam want to turn back. But with each step forward, Sam discovered that the 'scary' sounds were just owls hooting, rabbits scurrying, and wind blowing through the leaves. The mysterious shadows were simply trees swaying in the moonlight. When Sam reached the clearing where the healing herbs grew, they glowed with a soft, beautiful light. Sam carefully gathered the herbs and hurried back home. The village healer used them to make medicine that cured everyone. Sam realized that courage isn't about not being afraid – it's about doing what's right even when you are scared."
            },
            "friendship": {
                "title": "The Magic of True Friendship",
                "story": "Luna and Ben were the best of friends who loved exploring their neighborhood together. One sunny Saturday, they discovered a mysterious door hidden behind the old library that led to a magical garden where flowers could talk and butterflies painted rainbows in the sky. They promised to keep it their secret special place. But when Luna's family had to move to a different city, both friends felt heartbroken. 'How can we stay friends when we're so far apart?' Luna asked sadly. Ben had an idea. Every day at sunset, they would both go to their favorite spots – Luna to her new garden and Ben to their magical garden – and think about their friendship. Something amazing happened: even though they were miles apart, they both started seeing the same rainbow butterflies and hearing the same singing flowers. They realized that true friendship isn't about being in the same place, but about caring for each other no matter where you are. They wrote letters, shared photos, and visited each other during school breaks. Their friendship grew even stronger because they learned that real friends always find ways to stay connected."
            }
        }
    
    async def generate_story(self, moral: str, length: int = 75) -> Dict[str, Any]:
        """Generate a story with given moral and length."""
        logger.info(f"Generating story for moral: {moral}, length: {length}")
        
        # Try Claude first
        if self.claude.available:
            claude_story = await self.claude.generate_story(moral, length)
            if claude_story:
                return {
                    "title": f"A Story About {moral.title()}",
                    "content": claude_story,
                    "moral": moral,
                    "length": len(claude_story.split()),
                    "method": "claude",
                    "claude_available": True
                }
        
        # Fallback to template
        template = self.templates.get(moral.lower())
        if template:
            content = self._adjust_length(template["story"], length)
            return {
                "title": template["title"],
                "content": content,
                "moral": moral,
                "length": len(content.split()),
                "method": "template",
                "claude_available": self.claude.available
            }
        
        # Generic fallback
        content = f"Once upon a time, in a land not so far away, there lived a young person who was about to learn something very important about {moral}. Through a series of exciting adventures and meeting new friends, they discovered that {moral} is one of the most valuable things in life. They learned that when we practice {moral}, we not only help others but also make ourselves happier and stronger. And from that day forward, they carried this lesson in their heart, sharing it with everyone they met. The end."
        content = self._adjust_length(content, length)
        
        return {
            "title": f"The {moral.title()} Adventure",
            "content": content,
            "moral": moral,
            "length": len(content.split()),
            "method": "generic",
            "claude_available": self.claude.available
        }
    
    def _adjust_length(self, story: str, target_length: int) -> str:
        """Adjust story length."""
        words = story.split()
        current_length = len(words)
        
        if current_length > target_length:
            # Truncate but try to end at a sentence
            truncated = " ".join(words[:target_length])
            # Find last period before target
            last_period = truncated.rfind('.')
            if last_period > target_length * 0.8:  # If we have a sentence ending near target
                return truncated[:last_period + 1]
            return truncated
            
        elif current_length < target_length * 0.8:  # Only extend if significantly short
            extensions = [
                "The adventure taught everyone in the village about the importance of this valuable lesson.",
                "Friends and family gathered to celebrate this wonderful discovery.",
                "The story spread throughout the land, inspiring others to follow this example.",
                "Years later, people still remembered this amazing tale and shared it with their children."
            ]
            while len(words) < target_length and extensions:
                extension = random.choice(extensions)
                words.extend(extension.split())
                extensions.remove(extension)  # Don't repeat the same extension
            return " ".join(words[:target_length])
            
        return story

# Initialize components
if not MCP_AVAILABLE:
    print("❌ MCP library not available. Install with: pip install mcp")
    sys.exit(1)

story_generator = StoryGenerator()
voice_engine = VoiceNarrationEngine()

# Create MCP server
app = Server("storyteller")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="generate_story",
            description="Generate a children's story with optional voice narration",
            inputSchema={
                "type": "object",
                "properties": {
                    "moral": {
                        "type": "string",
                        "description": "The moral value to teach (e.g., 'honesty', 'kindness', 'courage', 'friendship')"
                    },
                    "length": {
                        "type": "integer",
                        "description": "Target story length in words (default: 100)",
                        "default": 100
                    },
                    "voice_id": {
                        "type": "string",
                        "description": "Voice profile ID for narration (optional)",
                        "default": "narrator"
                    },
                    "include_audio": {
                        "type": "boolean",
                        "description": "Whether to generate voice narration",
                        "default": True
                    }
                },
                "required": ["moral"]
            }
        ),
        Tool(
            name="list_voices",
            description="List available voice profiles and engine status",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="narrate_text",
            description="Generate voice narration for any text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to narrate"
                    },
                    "voice_id": {
                        "type": "string",
                        "description": "Voice profile ID",
                        "default": "narrator"
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="test_audio",
            description="Test audio system with a simple message",
            inputSchema={
                "type": "object",
                "properties": {
                    "voice_id": {
                        "type": "string",
                        "description": "Voice profile ID to test",
                        "default": "narrator"
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle MCP tool calls."""
    
    try:
        if name == "generate_story":
            moral = arguments.get("moral")
            length = arguments.get("length", 100)
            voice_id = arguments.get("voice_id", "narrator")
            include_audio = arguments.get("include_audio", True)
            
            if not moral:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Missing required parameter: moral"}, indent=2)
                )]
            
            # Generate story
            story_result = await story_generator.generate_story(moral, length)
            
            # Add voice narration if requested
            if include_audio:
                narration_result = await voice_engine.narrate_story(
                    story_result["content"], voice_id
                )
                story_result["voice_narration"] = narration_result
            
            # Add available voices info
            story_result["available_voices"] = voice_engine.get_available_voices()
            
            return [TextContent(
                type="text",
                text=json.dumps(story_result, indent=2)
            )]
        
        elif name == "list_voices":
            voices = voice_engine.get_available_voices()
            return [TextContent(
                type="text",
                text=json.dumps(voices, indent=2)
            )]
        
        elif name == "narrate_text":
            text = arguments.get("text")
            voice_id = arguments.get("voice_id", "narrator")
            
            if not text:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "Missing required parameter: text"}, indent=2)
                )]
            
            result = await voice_engine.narrate_story(text, voice_id)
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "test_audio":
            voice_id = arguments.get("voice_id", "narrator")
            test_text = "Hello! This is a test of the audio narration system. If you can hear this, the voice engine is working correctly."
            
            result = await voice_engine.narrate_story(test_text, voice_id)
            result["test_message"] = "Audio test completed"
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
            )]
    
    except Exception as e:
        logger.error(f"Tool call error: {e}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Tool execution failed: {str(e)}"}, indent=2)
        )]

async def main():
    """Run the MCP server."""
    logger.info("🚀 Starting Enhanced MCP Storyteller Server")
    logger.info(f"🖥️ System: {platform.system()}")
    logger.info(f"🤖 Claude: {'✅ Available' if story_generator.claude.available else '❌ Not Available'}")
    
    # Log voice engines status
    working_engines = [engine for engine, available in voice_engines.items() if available]
    if working_engines:
        logger.info(f"🎵 Working voice engines: {', '.join(working_engines)}")
    else:
        logger.warning("⚠️ No voice engines available")
        logger.info("📋 To install voice engines:")
        logger.info("   pip install pyttsx3 gtts edge-tts")
    
    # Log voice profiles
    logger.info(f"🎭 Voice profiles available: {len(voice_engine.voice_profiles)}")
    for profile_id, profile in voice_engine.voice_profiles.items():
        status = "✅" if voice_engines.get(profile.engine, False) else "❌"
        logger.info(f"   {status} {profile.name} ({profile.engine})")
    
    # Test basic functionality
    try:
        test_story = await story_generator.generate_story("kindness", 50)
        logger.info(f"✅ Story generation test passed: {test_story['method']}")
    except Exception as e:
        logger.error(f"❌ Story generation test failed: {e}")
    
    logger.info("🎯 Server ready for connections")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Server crashed: {e}")
        sys.exit(1)
                