#!/usr/bin/env python3
"""
AI-Powered Kids Storyteller - Enhanced MCP Server with Voice Narration
Fixed for macOS compatibility - no more Music app launching!
"""

import asyncio
import json
import random
import os
import tempfile
import threading
import subprocess
import platform
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path

# Voice synthesis imports
voice_engines = {}
try:
    import pyttsx3
    voice_engines['pyttsx3'] = True
except ImportError:
    voice_engines['pyttsx3'] = False

try:
    from gtts import gTTS
    # Remove pygame dependency for macOS compatibility
    voice_engines['gtts'] = True
except ImportError:
    voice_engines['gtts'] = False

try:
    import edge_tts
    voice_engines['edge_tts'] = True
except ImportError:
    voice_engines['edge_tts'] = False

# Claude integration imports
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
    age_group: str = "adult"  # child, adult, elderly
    style: str = "friendly"  # friendly, storyteller, parent, child
    speed: float = 1.0
    pitch: float = 1.0

class AudioPlayer:
    """Cross-platform audio player that avoids Music app on macOS."""
    
    @staticmethod
    def play_audio_file(audio_file: str) -> bool:
        """Play audio file using system-appropriate method."""
        if not audio_file or not os.path.exists(audio_file):
            logger.error("Audio file not found")
            return False
        
        try:
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Use afplay instead of open to avoid Music app
                subprocess.run(["afplay", audio_file], check=True)
                logger.info("✅ Playing with afplay (macOS native)")
                return True
                
            elif system == "Linux":
                # Try multiple players in order of preference
                players = ["paplay", "aplay", "play", "mpg123", "ffplay"]
                for player in players:
                    try:
                        subprocess.run([player, audio_file], check=True, 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        logger.info(f"✅ Playing with {player}")
                        return True
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue
                
                # Fallback to xdg-open
                subprocess.run(["xdg-open", audio_file])
                return True
                
            elif system == "Windows":
                # Use Windows Media Player command line
                subprocess.run(["start", "/wait", "", audio_file], shell=True)
                return True
                
            else:
                logger.warning(f"Unknown system: {system}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Audio playback failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected audio error: {e}")
            return False
    
    @staticmethod
    def is_audio_supported() -> Dict[str, bool]:
        """Check which audio playback methods are available."""
        system = platform.system()
        supported = {}
        
        if system == "Darwin":  # macOS
            try:
                subprocess.run(["which", "afplay"], check=True, 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                supported["afplay"] = True
            except:
                supported["afplay"] = False
                
        elif system == "Linux":
            players = ["paplay", "aplay", "play", "mpg123", "ffplay"]
            for player in players:
                try:
                    subprocess.run(["which", player], check=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    supported[player] = True
                except:
                    supported[player] = False
                    
        elif system == "Windows":
            supported["windows_media"] = True  # Usually available
            
        return supported

class VoiceNarrationEngine:
    """Manages multiple voice synthesis engines - macOS compatible."""
    
    def __init__(self):
        self.engines = {}
        self.temp_dir = tempfile.mkdtemp()
        self.audio_player = AudioPlayer()
        self._init_engines()
        self.voice_profiles = self._create_voice_profiles()
        
        # Check audio support
        audio_support = self.audio_player.is_audio_supported()
        logger.info(f"🎵 Audio support: {audio_support}")
        
    def _init_engines(self):
        """Initialize available voice engines."""
        # Initialize pyttsx3 (offline, cross-platform)
        if voice_engines['pyttsx3']:
            try:
                engine = pyttsx3.init()
                self.engines['pyttsx3'] = engine
                logger.info("✅ pyttsx3 engine initialized")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize pyttsx3: {e}")
                voice_engines['pyttsx3'] = False
        
        # No need to initialize pygame - we'll use system audio players
        if voice_engines['gtts']:
            logger.info("✅ gTTS available - will use system audio player")
    
    def _create_voice_profiles(self) -> Dict[str, VoiceProfile]:
        """Create predefined voice profiles for different engines."""
        profiles = {}
        
        # pyttsx3 profiles (offline)
        if voice_engines['pyttsx3']:
            profiles.update({
                "default_narrator": VoiceProfile("default_narrator", "Default Narrator", "pyttsx3", 
                                                style="storyteller", speed=0.85),
                "parent_voice": VoiceProfile("parent_voice", "Parent Voice", "pyttsx3", 
                                            style="parent", speed=0.8, pitch=1.1),
                "child_voice": VoiceProfile("child_voice", "Child Voice", "pyttsx3", 
                                           age_group="child", speed=1.1, pitch=1.3),
                "wise_elder": VoiceProfile("wise_elder", "Wise Elder", "pyttsx3", 
                                          age_group="elderly", speed=0.7, pitch=0.9)
            })
        
        # gTTS profiles (online, high quality)
        if voice_engines['gtts']:
            profiles.update({
                "gtts_storyteller": VoiceProfile("gtts_storyteller", "Professional Storyteller", "gtts",
                                                style="storyteller"),
                "gtts_friendly": VoiceProfile("gtts_friendly", "Friendly Voice", "gtts",
                                             style="friendly")
            })
        
        # Edge TTS profiles (online, Microsoft voices)
        if voice_engines['edge_tts']:
            profiles.update({
                "edge_jenny": VoiceProfile("edge_jenny", "Jenny (US Female)", "edge_tts", 
                                          gender="female", style="friendly"),
                "edge_guy": VoiceProfile("edge_guy", "Guy (US Male)", "edge_tts", 
                                        gender="male", style="storyteller"),
                "edge_aria": VoiceProfile("edge_aria", "Aria (US Female)", "edge_tts", 
                                         gender="female", style="parent"),
                "edge_davis": VoiceProfile("edge_davis", "Davis (US Male)", "edge_tts", 
                                          gender="male", style="friendly")
            })
        
        return profiles
    
    def get_available_voices(self) -> Dict[str, Dict]:
        """Get all available voice profiles organized by engine."""
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
                "age_group": profile.age_group,
                "engine": profile.engine,
                "available": voice_engines.get(profile.engine, False)
            })
        
        return voices_by_engine
    
    async def narrate_story(self, text: str, voice_id: str = "default_narrator", 
                           save_file: bool = True) -> Dict[str, Any]:
        """Narrate a story using the specified voice profile."""
        if voice_id not in self.voice_profiles:
            # Fallback to first available voice
            available_voices = [v for v in self.voice_profiles.values() 
                              if voice_engines.get(v.engine, False)]
            if not available_voices:
                return {"error": "No voice engines available", "audio_file": None, "success": False}
            voice_id = available_voices[0].id
        
        profile = self.voice_profiles[voice_id]
        
        if not voice_engines.get(profile.engine, False):
            return {"error": f"Voice engine {profile.engine} not available", "audio_file": None, "success": False}
        
        try:
            if profile.engine == "pyttsx3":
                return await self._narrate_pyttsx3(text, profile, save_file)
            elif profile.engine == "gtts":
                return await self._narrate_gtts(text, profile, save_file)
            elif profile.engine == "edge_tts":
                return await self._narrate_edge_tts(text, profile, save_file)
            else:
                return {"error": f"Unknown engine: {profile.engine}", "audio_file": None, "success": False}
                
        except Exception as e:
            logger.error(f"❌ Narration failed: {e}")
            return {"error": str(e), "audio_file": None, "success": False}
    
    async def _narrate_pyttsx3(self, text: str, profile: VoiceProfile, save_file: bool) -> Dict[str, Any]:
        """Narrate using pyttsx3 (offline)."""
        def _speak():
            try:
                engine = self.engines['pyttsx3']
                
                # Configure voice properties
                engine.setProperty('rate', int(200 * profile.speed))
                
                # Try to set voice based on profile
                voices = engine.getProperty('voices')
                if voices:
                    if profile.gender == "female" and len(voices) > 1:
                        engine.setProperty('voice', voices[1].id)
                    else:
                        engine.setProperty('voice', voices[0].id)
                
                if save_file:
                    audio_file = os.path.join(self.temp_dir, f"story_{profile.id}.wav")
                    engine.save_to_file(text, audio_file)
                    engine.runAndWait()
                    return audio_file
                else:
                    engine.say(text)
                    engine.runAndWait()
                    return None
                    
            except Exception as e:
                logger.error(f"❌ pyttsx3 error: {e}")
                return None
        
        # Run in thread to avoid blocking
        audio_file = await asyncio.to_thread(_speak)
        
        if audio_file and os.path.exists(audio_file):
            return {
                "success": True,
                "engine": "pyttsx3",
                "voice_name": profile.name,
                "audio_file": audio_file,
                "duration_estimate": len(text.split()) * 0.6 / profile.speed
            }
        else:
            return {"error": "Failed to generate pyttsx3 audio", "success": False}
    
    async def _narrate_gtts(self, text: str, profile: VoiceProfile, save_file: bool) -> Dict[str, Any]:
        """Narrate using Google Text-to-Speech (online) - macOS compatible."""
        try:
            tts = gTTS(text=text, lang=profile.language, slow=profile.speed < 0.9)
            audio_file = os.path.join(self.temp_dir, f"story_{profile.id}.mp3")
            
            # Save audio file
            await asyncio.to_thread(tts.save, audio_file)
            
            if not save_file:
                # Play using system audio player (no pygame/Music app)
                success = await asyncio.to_thread(self.audio_player.play_audio_file, audio_file)
                if not success:
                    logger.warning("⚠️ Audio playback failed, but file saved")
            
            return {
                "success": True,
                "engine": "gtts",
                "voice_name": profile.name,
                "audio_file": audio_file if save_file else None,
                "duration_estimate": len(text.split()) * 0.6,
                "system": platform.system()
            }
            
        except Exception as e:
            logger.error(f"❌ gTTS error: {e}")
            return {"error": str(e), "audio_file": None, "success": False}
    
    async def _narrate_edge_tts(self, text: str, profile: VoiceProfile, save_file: bool) -> Dict[str, Any]:
        """Narrate using Microsoft Edge TTS (online) - macOS compatible."""
        try:
            # Map profile to Edge TTS voice
            voice_map = {
                "edge_jenny": "en-US-JennyNeural",
                "edge_guy": "en-US-GuyNeural", 
                "edge_aria": "en-US-AriaNeural",
                "edge_davis": "en-US-DavisNeural"
            }
            
            voice_name = voice_map.get(profile.id, "en-US-JennyNeural")
            audio_file = os.path.join(self.temp_dir, f"story_{profile.id}.mp3")
            
            # Generate speech
            communicate = edge_tts.Communicate(text, voice_name)
            await communicate.save(audio_file)
            
            if not save_file:
                # Play using system audio player
                success = await asyncio.to_thread(self.audio_player.play_audio_file, audio_file)
                if not success:
                    logger.warning("⚠️ Audio playback failed, but file saved")
            
            return {
                "success": True,
                "engine": "edge_tts",
                "voice_name": profile.name,
                "audio_file": audio_file if save_file else None,
                "duration_estimate": len(text.split()) * 0.5,
                "system": platform.system()
            }
            
        except Exception as e:
            logger.error(f"❌ Edge TTS error: {e}")
            return {"error": str(e), "audio_file": None, "success": False}

# Import original classes with modifications
@dataclass
class Story:
    """Represents a story with metadata for ranking."""
    title: str
    content: str
    moral: str
    length: int
    score: float = 0.0
    agent_id: str = ""
    generation_method: str = "template"

class ClaudeStoryGenerator:
    """Handles Claude API integration for story generation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        self.available = False
        
        if CLAUDE_AVAILABLE and self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.available = True
                logger.info("✅ Claude API initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Claude: {e}")
                self.available = False
        else:
            logger.warning("⚠️ Claude not available - using template fallback")
    
    async def generate_story(self, moral: str, target_length: int, story_type: str = "adventure") -> Optional[str]:
        """Generate a complete story using Claude."""
        if not self.available:
            return None
        
        prompt = self._create_story_prompt(moral, target_length, story_type)
        
        try:
            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.8,
                system="You are a creative children's storyteller who writes engaging, age-appropriate stories that teach important moral lessons. Your stories are designed for children ages 5-10 and are perfect for voice narration.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if response.content and len(response.content) > 0:
                story_text = response.content[0].text.strip()
                logger.info(f"✅ Claude generated {len(story_text.split())} word story for '{moral}'")
                return story_text
            else:
                logger.warning("⚠️ Claude returned empty response")
                return None
                
        except Exception as e:
            logger.error(f"❌ Claude generation failed: {e}")
            return None
    
    def _create_story_prompt(self, moral: str, target_length: int, story_type: str) -> str:
        """Create a prompt for generating a complete story optimized for narration."""
        return f"""Write a children's story that teaches the moral value of "{moral}". 

Requirements:
- Target length: approximately {target_length} words
- Age appropriate for children 5-10 years old
- Story style: {story_type}
- IMPORTANT: Optimize for voice narration with clear pauses, engaging rhythm, and expressive dialogue
- Use natural speech patterns and conversational tone
- Include character voices that are distinct and fun to narrate
- Add emotional cues and descriptive words that enhance audio storytelling
- Structure sentences for easy speaking and listening comprehension
- The moral lesson should be woven naturally into the story
- Create memorable character names that are easy to pronounce
- Please do not add any unnecessary notes about the story meaning at the end, just use the target length to write the story only.
Focus on creating a story that sounds engaging when read aloud and teaches {moral} through compelling characters and situations.

Please write the complete story now:"""

class HybridStoryAgent:
    """Base class for agents that can use both templates and Claude."""
    
    def __init__(self, agent_id: str, specialty: str, story_type: str, claude_generator: ClaudeStoryGenerator):
        self.agent_id = agent_id
        self.specialty = specialty
        self.story_type = story_type
        self.claude = claude_generator
        self.templates = {}
    
    async def generate_story(self, moral: str, target_length: int) -> Story:
        """Generate story using hybrid approach."""
        if moral.lower() in self.templates:
            base_story = await self._generate_from_template(moral, target_length)
            
            if self.claude.available and abs(base_story.length - target_length) > 10:
                enhanced_content = await self.claude.generate_story(moral, target_length, self.story_type)
                if enhanced_content:
                    base_story.content = enhanced_content
                    base_story.length = len(enhanced_content.split())
                    base_story.generation_method = "hybrid"
            
            return base_story
        
        elif self.claude.available:
            claude_content = await self.claude.generate_story(moral, target_length, self.story_type)
            if claude_content:
                title = self._extract_or_generate_title(claude_content, moral)
                
                return Story(
                    title=title,
                    content=claude_content,
                    moral=moral,
                    length=len(claude_content.split()),
                    agent_id=self.agent_id,
                    generation_method="claude"
                )
        
        return await self._generate_fallback_story(moral, target_length)
    
    async def _generate_from_template(self, moral: str, target_length: int) -> Story:
        """Generate story from predefined template."""
        template = self.templates[moral.lower()]
        content = self._adjust_story_length_basic(template["story"], target_length)
        
        return Story(
            title=template["title"],
            content=content,
            moral=moral,
            length=len(content.split()),
            agent_id=self.agent_id,
            generation_method="template"
        )
    
    async def _generate_fallback_story(self, moral: str, target_length: int) -> Story:
        """Generate generic story when template and Claude both unavailable."""
        template = {
            "title": f"The {moral.title()} {self.story_type.title()}",
            "story": f"Once upon a time, a brave child learned the importance of {moral} during an amazing {self.story_type}. Through challenges and friendship, they discovered that {moral} makes every journey worthwhile."
        }
        
        content = self._adjust_story_length_basic(template["story"], target_length)
        
        return Story(
            title=template["title"],
            content=content,
            moral=moral,
            length=len(content.split()),
            agent_id=self.agent_id,
            generation_method="template"
        )
    
    def _extract_or_generate_title(self, content: str, moral: str) -> str:
        """Extract title from Claude content or generate one."""
        lines = content.split('\n')
        first_line = lines[0].strip()
        
        if len(first_line) < 50 and any(char.isupper() for char in first_line):
            return first_line
        
        return f"The {moral.title()} {self.story_type.title()}"
    
    def _adjust_story_length_basic(self, base_story: str, target_length: int) -> str:
        """Basic length adjustment."""
        words = base_story.split()
        current_length = len(words)
        
        if target_length > current_length:
            expansions = self._get_theme_expansions()
            while len(words) < target_length and expansions:
                words.extend(random.choice(expansions).split())
        elif target_length < current_length:
            words = words[:target_length]
            
        return " ".join(words)
    
    def _get_theme_expansions(self) -> List[str]:
        """Get theme-appropriate expansion sentences."""
        return [
            f"The {self.story_type} continued with new challenges.",
            "The character felt more confident with each step.",
            "Friends and allies appeared to offer help."
        ]

class EnhancedAdventureAgent(HybridStoryAgent):
    """Adventure agent with Claude integration."""
    
    def __init__(self, claude_generator: ClaudeStoryGenerator):
        super().__init__("adventure_agent", "Adventure Stories", "adventure", claude_generator)
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

class StoryRanker:
    """Enhanced ranking system."""
    
    @staticmethod
    def score_story(story: Story, target_length: int, moral: str) -> float:
        """Score a story with enhanced metrics."""
        score = 0.0
        
        # Length score (35% weight)
        length_diff = abs(story.length - target_length)
        max_diff = max(target_length, 50)
        length_score = max(0, 1 - (length_diff / max_diff))
        score += length_score * 0.35
        
        # Moral relevance (25% weight)
        moral_words = moral.lower().split()
        content_lower = story.content.lower()
        moral_matches = sum(1 for word in moral_words if word in content_lower)
        moral_score = min(1.0, moral_matches / max(len(moral_words), 1))
        score += moral_score * 0.25
        
        # Story quality (25% weight)
        quality_score = 0.0
        
        if any(word in content_lower for word in ['once', 'story', 'adventure']):
            quality_score += 0.3
        if any(word in content_lower for word in ['realized', 'understood', 'learned']):
            quality_score += 0.3
        if '"' in story.content or "said" in content_lower:
            quality_score += 0.2
        if story.content.count('.') >= 3:
            quality_score += 0.2
        
        score += min(quality_score, 1.0) * 0.25
        
        # Generation method bonus (15% weight)
        method_bonuses = {"claude": 0.9, "hybrid": 0.8, "template": 0.6}
        method_score = method_bonuses.get(story.generation_method, 0.5)
        score += method_score * 0.15
        
        return min(score, 1.0)

class EnhancedStorytellerPipeline:
    """Enhanced pipeline with Claude integration."""
    
    def __init__(self, claude_api_key: Optional[str] = None):
        self.claude = ClaudeStoryGenerator(claude_api_key)
        self.agents = [EnhancedAdventureAgent(self.claude)]
        self.ranker = StoryRanker()
    
    async def generate_story(self, moral: str, target_length: int = 75) -> Dict[str, Any]:
        """Generate and rank stories."""
        stories = await asyncio.gather(*[agent.generate_story(moral, target_length) for agent in self.agents])
        
        for story in stories:
            story.score = self.ranker.score_story(story, target_length, moral)
            
        stories.sort(key=lambda s: s.score, reverse=True)
        winner = stories[0]
        
        return {
            "title": winner.title,
            "content": winner.content,
            "moral": winner.moral,
            "length": winner.length,
            "agent_id": winner.agent_id,
            "score": winner.score,
            "generation_method": winner.generation_method,
            "claude_available": self.claude.available,
        }

class EnhancedMCPServer:
    """Enhanced MCP Server with Voice Narration - macOS Compatible."""
    
    def __init__(self, claude_api_key: Optional[str] = None):
        self.pipeline = EnhancedStorytellerPipeline(claude_api_key)
        self.voice_engine = VoiceNarrationEngine()
        self.tools = {
            "generate_story": {
                "name": "generate_story",
                "description": "Generate a children's story with optional voice narration",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "moral": {"type": "string", "description": "The moral to teach"},
                        "length": {"type": "integer", "description": "Target length in words", "default": 75},
                        "voice_id": {"type": "string", "description": "Voice profile ID for narration", "default": None},
                        "narrate": {"type": "boolean", "description": "Whether to generate voice narration", "default": False}
                    },
                    "required": ["moral"]
                }
            },
            "list_voices": {
                "name": "list_voices",
                "description": "List available voice profiles for narration",
                "parameters": {"type": "object", "properties": {}}
            },
            "narrate_text": {
                "name": "narrate_text", 
                "description": "Narrate any text with specified voice",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to narrate"},
                        "voice_id": {"type": "string", "description": "Voice profile ID", "default": "default_narrator"}
                    },
                    "required": ["text"]
                }
            }
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests with voice capabilities."""
        try:
            if request.get("method") == "tools/list":
                return {"tools": list(self.tools.values())}
            
            elif request.get("method") == "tools/call":
                tool_name = request.get("params", {}).get("name")
                args = request.get("params", {}).get("arguments", {})
                
                if tool_name == "generate_story":
                    moral = args.get("moral")
                    length = args.get("length", 75)
                    voice_id = args.get("voice_id")
                    narrate = args.get("narrate", False)
                    
                    if not moral:
                        return {"error": "Missing required parameter: moral"}
                    
                    # Generate story
                    result = await self.pipeline.generate_story(moral, length)
                    
                    # Add voice narration if requested
                    if narrate and voice_id:
                        logger.info(f"🎙️ Generating voice narration with {voice_id}")
                        narration_result = await self.voice_engine.narrate_story(
                            result["content"], voice_id, save_file=True
                        )
                        result["voice_narration"] = narration_result
                    
                    # Add available voices info
                    result["available_voices"] = self.voice_engine.get_available_voices()
                    
                    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                
                elif tool_name == "list_voices":
                    voices = self.voice_engine.get_available_voices()
                    return {"content": [{"type": "text", "text": json.dumps(voices, indent=2)}]}
                
                elif tool_name == "narrate_text":
                    text = args.get("text")
                    voice_id = args.get("voice_id", "default_narrator")
                    
                    if not text:
                        return {"error": "Missing required parameter: text"}
                    
                    result = await self.voice_engine.narrate_story(text, voice_id, save_file=True)
                    return {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                
                else:
                    return {"error": f"Unknown tool: {tool_name}"}
            
            else:
                return {"error": f"Unknown method: {request.get('method')}"}
                
        except Exception as e:
            logger.error(f"❌ Error handling request: {e}")
            return {"error": str(e)}
    
    async def start_server(self, host: str = "localhost", port: int = 8000):
        """Start the enhanced MCP server with voice capabilities."""
        logger.info(f"🚀 Starting Enhanced Voice-Enabled Storyteller Server on {host}:{port}")
        logger.info(f"🖥️ System: {platform.system()}")
        logger.info(f"🤖 Claude API: {'✅ Available' if self.pipeline.claude.available else '❌ Not Available'}")
        
        # Test voice engines
        logger.info("🎵 Testing voice engines...")
        voices = self.voice_engine.get_available_voices()
        for engine, voice_list in voices.items():
            available_count = sum(1 for v in voice_list if v['available'])
            status = "✅" if available_count > 0 else "❌"
            logger.info(f"  {status} {engine}: {available_count} voices available")
        
        # Test audio support
        audio_support = self.voice_engine.audio_player.is_audio_supported()
        if any(audio_support.values()):
            logger.info("🔊 Audio playback: ✅ Supported")
            for player, supported in audio_support.items():
                if supported:
                    logger.info(f"  - {player}: ✅")
        else:
            logger.warning("🔊 Audio playback: ⚠️ Limited support")
        
        return {
            "status": "Voice-enabled server ready (macOS compatible)", 
            "claude_available": self.pipeline.claude.available,
            "voice_engines": voices,
            "audio_support": audio_support,
            "system": platform.system()
        }

async def main():
    """Main function to run the enhanced server with voice - macOS compatible."""
    print("🎙️ AI STORYTELLER WITH VOICE NARRATION")
    print("🍎 macOS Compatible Version")
    print("=" * 50)
    
    # System info
    system = platform.system()
    print(f"🖥️ System: {system}")
    
    # Check voice dependencies
    print("🔍 Checking voice synthesis dependencies...")
    for engine, available in voice_engines.items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"  {engine}: {status}")
    
    if not any(voice_engines.values()):
        print("\n⚠️ No voice engines available. Install dependencies:")
        print("  pip install pyttsx3 gtts edge-tts")
        print("  Note: pygame is NOT required for this macOS-compatible version!")
    
    # Check audio support
    print(f"\n🔊 Checking audio playback support...")
    audio_player = AudioPlayer()
    audio_support = audio_player.is_audio_supported()
    
    if system == "Darwin":
        if audio_support.get("afplay", False):
            print("  ✅ afplay (macOS native) - No Music app interference!")
        else:
            print("  ⚠️ afplay not found - audio playback may not work")
    else:
        supported_players = [player for player, supported in audio_support.items() if supported]
        if supported_players:
            print(f"  ✅ Audio players: {', '.join(supported_players)}")
        else:
            print("  ⚠️ No audio players found")
    
    print("\n📦 Starting server...")
    server = EnhancedMCPServer()
    result = await server.start_server()
    
    print(f"\nStatus: {result['status']}")
    print(f"Claude: {'✅ Active' if result['claude_available'] else '❌ Template Mode'}")
    print("🎵 Voice engines ready for narration!")
    print("🚫 No more Music app interference on macOS!")
    
    if system == "Darwin":
        print("\n💡 macOS Tips:")
        print("  - Audio will use afplay (native macOS player)")
        print("  - No Music app will open during playback")
        print("  - System volume controls audio output")

if __name__ == "__main__":
    asyncio.run(main())
                
