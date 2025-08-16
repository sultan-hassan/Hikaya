#!/usr/bin/env python3
"""
Real MCP Server for AI-Powered Kids Storyteller with Voice Narration
Implements the official Model Context Protocol specification
"""

import asyncio
import json
import logging
import os
import tempfile
import platform
import subprocess
import random
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import sys

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

# Voice synthesis imports
voice_engines = {}
try:
    import pyttsx3
    voice_engines['pyttsx3'] = True
except ImportError:
    voice_engines['pyttsx3'] = False

try:
    from gtts import gTTS
    voice_engines['gtts'] = True
except ImportError:
    voice_engines['gtts'] = False

try:
    import edge_tts
    voice_engines['edge_tts'] = True
except ImportError:
    voice_engines['edge_tts'] = False

# Claude integration
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    """Cross-platform audio player."""
    
    @staticmethod
    def play_audio_file(audio_file: str) -> bool:
        """Play audio file using system-appropriate method."""
        if not audio_file or not os.path.exists(audio_file):
            return False
        
        try:
            system = platform.system()
            
            if system == "Darwin":  # macOS
                subprocess.run(["afplay", audio_file], check=True)
                return True
            elif system == "Linux":
                players = ["paplay", "aplay", "play", "mpg123"]
                for player in players:
                    try:
                        subprocess.run([player, audio_file], check=True, 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return True
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                return False
            elif system == "Windows":
                subprocess.run(["start", "/wait", "", audio_file], shell=True)
                return True
            return False
        except Exception:
            return False

class VoiceNarrationEngine:
    """Manages voice synthesis engines."""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.audio_player = AudioPlayer()
        self.voice_profiles = self._create_voice_profiles()
        self._init_pyttsx3()
    
    def _init_pyttsx3(self):
        """Initialize pyttsx3 voices."""
        if voice_engines['pyttsx3']:
            try:
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                if voices:
                    self.pyttsx3_voices = voices
                    logger.info(f"✅ pyttsx3 initialized with {len(voices)} voices")
                engine.stop()
                del engine
            except Exception as e:
                logger.warning(f"⚠️ pyttsx3 init failed: {e}")
                voice_engines['pyttsx3'] = False
    
    def _create_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """Create voice profiles for available engines."""
        profiles = {}
        
        # pyttsx3 profiles
        if voice_engines['pyttsx3']:
            profiles.update({
                "narrator": VoiceProfile("narrator", "Story Narrator", "pyttsx3", 
                                       style="storyteller", speed=0.85),
                "parent": VoiceProfile("parent", "Parent Voice", "pyttsx3", 
                                     style="parent", speed=0.8),
                "child": VoiceProfile("child", "Child Voice", "pyttsx3", 
                                    age_group="child", speed=1.1),
            })
        
        # gTTS profiles
        if voice_engines['gtts']:
            profiles.update({
                "gtts_narrator": VoiceProfile("gtts_narrator", "Professional Narrator", "gtts"),
                "gtts_friendly": VoiceProfile("gtts_friendly", "Friendly Voice", "gtts"),
            })
        
        return profiles
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get available voice profiles."""
        voices_by_engine = {}
        for profile in self.voice_profiles.values():
            engine = profile.engine
            if engine not in voices_by_engine:
                voices_by_engine[engine] = []
            voices_by_engine[engine].append({
                "id": profile.id,
                "name": profile.name,
                "style": profile.style,
                "gender": profile.gender,
                "available": voice_engines.get(profile.engine, False)
            })
        return voices_by_engine
    
    async def narrate_story(self, text: str, voice_id: str = "narrator") -> Dict[str, Any]:
        """Narrate story with specified voice."""
        if voice_id not in self.voice_profiles:
            available = [v for v in self.voice_profiles.values() 
                        if voice_engines.get(v.engine, False)]
            if not available:
                return {"error": "No voices available", "success": False}
            voice_id = available[0].id
        
        profile = self.voice_profiles[voice_id]
        
        try:
            if profile.engine == "pyttsx3":
                return await self._narrate_pyttsx3(text, profile)
            elif profile.engine == "gtts":
                return await self._narrate_gtts(text, profile)
            else:
                return {"error": f"Engine {profile.engine} not supported", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _narrate_pyttsx3(self, text: str, profile: VoiceProfile) -> Dict[str, Any]:
        """Narrate using pyttsx3."""
        def _speak():
            engine = None
            try:
                engine = pyttsx3.init()
                
                # Set properties
                rate = max(150, min(300, int(200 * profile.speed)))
                engine.setProperty('rate', rate)
                engine.setProperty('volume', 0.9)
                
                # Generate audio file
                import time
                audio_file = os.path.join(self.temp_dir, f"story_{int(time.time())}.wav")
                engine.save_to_file(text, audio_file)
                engine.runAndWait()
                
                if os.path.exists(audio_file):
                    return audio_file
                return None
                
            except Exception as e:
                logger.error(f"pyttsx3 error: {e}")
                return None
            finally:
                if engine:
                    try:
                        engine.stop()
                        del engine
                    except:
                        pass
        
        audio_file = await asyncio.to_thread(_speak)
        
        if audio_file:
            return {
                "success": True,
                "engine": "pyttsx3",
                "voice_name": profile.name,
                "audio_file": audio_file,
                "duration": len(text.split()) * 0.6 / profile.speed
            }
        return {"error": "Failed to generate audio", "success": False}
    
    async def _narrate_gtts(self, text: str, profile: VoiceProfile) -> Dict[str, Any]:
        """Narrate using Google TTS."""
        try:
            tts = gTTS(text=text, lang=profile.language)
            import time
            audio_file = os.path.join(self.temp_dir, f"story_{int(time.time())}.mp3")
            
            await asyncio.to_thread(tts.save, audio_file)
            
            return {
                "success": True,
                "engine": "gtts",
                "voice_name": profile.name,
                "audio_file": audio_file,
                "duration": len(text.split()) * 0.6
            }
        except Exception as e:
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

Write only the story, no additional notes."""
        
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
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
                "story": "Maya found an old map leading to treasure. When her friend asked about it, she could have lied and kept it secret. But Maya chose to tell the truth and share the adventure. Together, they discovered that honesty made their friendship the greatest treasure of all."
            },
            "kindness": {
                "title": "The Kind Knight's Quest",
                "story": "Sir Alex was on a quest to save the kingdom. Along the way, they met a lost dragon who was crying. Instead of fighting, Alex showed kindness and helped the dragon find its way home. The grateful dragon became Alex's friend and helped save the kingdom together."
            },
            "courage": {
                "title": "The Brave Little Explorer", 
                "story": "Sam was afraid of the dark forest, but their village needed medicine from the other side. Taking a deep breath, Sam found courage and ventured into the woods. With each brave step, the path became clearer, and Sam returned home a hero."
            }
        }
    
    async def generate_story(self, moral: str, length: int = 75) -> Dict[str, Any]:
        """Generate a story with given moral and length."""
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
        content = f"Once upon a time, there was a child who learned about {moral} through an amazing adventure. They discovered that {moral} is one of the most important values in life."
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
        if len(words) > target_length:
            return " ".join(words[:target_length])
        elif len(words) < target_length:
            # Add simple extensions
            extensions = [
                "The adventure continued with new discoveries.",
                "Friends joined the journey along the way.",
                "Each step brought new understanding and growth."
            ]
            while len(words) < target_length:
                words.extend(random.choice(extensions).split())
            return " ".join(words[:target_length])
        return story

# Real MCP Server Implementation
if not MCP_AVAILABLE:
    print("❌ MCP library not available. Install with: pip install mcp")
    sys.exit(1)

# Initialize components
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
                        "description": "The moral value to teach (e.g., 'honesty', 'kindness', 'courage')"
                    },
                    "length": {
                        "type": "integer",
                        "description": "Target story length in words (default: 75)",
                        "default": 75
                    },
                    "voice_id": {
                        "type": "string",
                        "description": "Voice profile ID for narration (optional)",
                        "default": "narrator"
                    },
                    "include_audio": {
                        "type": "boolean",
                        "description": "Whether to generate voice narration",
                        "default": False
                    }
                },
                "required": ["moral"]
            }
        ),
        Tool(
            name="list_voices",
            description="List available voice profiles for narration",
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
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle MCP tool calls."""
    
    if name == "generate_story":
        moral = arguments.get("moral")
        length = arguments.get("length", 75)
        voice_id = arguments.get("voice_id", "narrator")
        include_audio = arguments.get("include_audio", False)
        
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
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Unknown tool: {name}"}, indent=2)
        )]

async def main():
    """Run the MCP server."""
    logger.info("🚀 Starting Real MCP Storyteller Server")
    logger.info(f"🖥️ System: {platform.system()}")
    logger.info(f"🤖 Claude: {'✅ Available' if story_generator.claude.available else '❌ Not Available'}")
    
    # Log voice engines
    available_engines = [engine for engine, available in voice_engines.items() if available]
    if available_engines:
        logger.info(f"🎵 Voice engines: {', '.join(available_engines)}")
    else:
        logger.warning("⚠️ No voice engines available")
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
