#!/usr/bin/env python3
"""
AI-Powered Kids Storyteller - Enhanced MCP Client with Voice Narration
Fixed for macOS - no more Music app launching!
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional
import subprocess
import platform

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPClient:
    """Enhanced MCP Client for Claude-powered storyteller with voice."""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 8000):
        self.server_host = server_host
        self.server_port = server_port
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to the enhanced MCP server."""
        try:
            logger.info(f"🔗 Connecting to Enhanced Voice-Enabled MCP server at {self.server_host}:{self.server_port}")
            await asyncio.sleep(0.1)  # Simulate connection delay
            self.connected = True
            logger.info("✅ Successfully connected to enhanced voice server")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.connected:
            logger.info("🔌 Disconnecting from MCP server")
            self.connected = False
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools from the enhanced server."""
        if not self.connected:
            raise ConnectionError("Not connected to server")
        
        request = {"method": "tools/list"}
        
        from voice_storyteller_server import EnhancedMCPServer
        server = EnhancedMCPServer()
        response = await server.handle_request(request)
        
        return response
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the enhanced server."""
        if not self.connected:
            raise ConnectionError("Not connected to server")
        
        request = {
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        from voice_storyteller_server import EnhancedMCPServer
        server = EnhancedMCPServer()
        response = await server.handle_request(request)
        
        return response
    
    async def generate_story(self, moral: str, length: int = 75, voice_id: Optional[str] = None, 
                           narrate: bool = False) -> Optional[Dict[str, Any]]:
        """Generate a story with optional voice narration."""
        try:
            logger.info(f"🎨 Requesting AI-enhanced story for moral: '{moral}', length: {length}")
            if narrate and voice_id:
                logger.info(f"🎙️ Voice narration requested with voice: {voice_id}")
            
            response = await self.call_tool("generate_story", {
                "moral": moral,
                "length": length,
                "voice_id": voice_id,
                "narrate": narrate
            })
            
            if "error" in response:
                logger.error(f"❌ Server returned error: {response['error']}")
                return None
            
            content = response.get("content", [])
            if content and len(content) > 0:
                story_data = json.loads(content[0]["text"])
                method_emoji = {
                    "claude": "🤖",
                    "hybrid": "🔥", 
                    "template": "📚"
                }
                method = story_data.get('generation_method', 'template')
                emoji = method_emoji.get(method, "📖")
                
                logger.info(f"✅ Received story: '{story_data.get('title', 'Untitled')}' {emoji} ({method})")
                
                if story_data.get("voice_narration"):
                    voice_info = story_data["voice_narration"]
                    if voice_info.get("success"):
                        logger.info(f"🎵 Voice narration ready: {voice_info.get('voice_name', 'Unknown Voice')}")
                        logger.info(f"🖥️ Audio system: {voice_info.get('system', 'Unknown')}")
                    else:
                        logger.error(f"❌ Voice narration failed: {voice_info.get('error', 'Unknown error')}")
                
                return story_data
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error generating story: {e}")
            return None
    
    async def list_voices(self) -> Optional[Dict[str, Any]]:
        """Get available voice profiles."""
        try:
            response = await self.call_tool("list_voices", {})
            
            if "error" in response:
                logger.error(f"❌ Error listing voices: {response['error']}")
                return None
            
            content = response.get("content", [])
            if content and len(content) > 0:
                return json.loads(content[0]["text"])
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error listing voices: {e}")
            return None
    
    async def narrate_text(self, text: str, voice_id: str = "default_narrator") -> Optional[Dict[str, Any]]:
        """Narrate arbitrary text with specified voice."""
        try:
            logger.info(f"🎙️ Narrating text with voice: {voice_id}")
            
            response = await self.call_tool("narrate_text", {
                "text": text,
                "voice_id": voice_id
            })
            
            if "error" in response:
                logger.error(f"❌ Narration error: {response['error']}")
                return None
            
            content = response.get("content", [])
            if content and len(content) > 0:
                return json.loads(content[0]["text"])
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error narrating text: {e}")
            return None

class AudioPlayer:
    """Cross-platform audio player that avoids Music app on macOS."""
    
    @staticmethod
    def play_audio_file(audio_file: str) -> bool:
        """Play audio file using system-appropriate method."""
        if not audio_file or not os.path.exists(audio_file):
            print("❌ Audio file not found")
            return False
        
        try:
            system = platform.system()
            
            if system == "Darwin":  # macOS
                # Use afplay instead of open to avoid Music app
                result = subprocess.run(["afplay", audio_file], check=True,
                                      capture_output=True, text=True)
                print("✅ Playing with afplay (macOS native - no Music app!)")
                return True
                
            elif system == "Linux":
                # Try multiple players in order of preference
                players = ["paplay", "aplay", "play", "mpg123", "ffplay"]
                for player in players:
                    try:
                        subprocess.run([player, audio_file], check=True, 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"✅ Playing with {player}")
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
                print(f"⚠️ Unknown system: {system}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Audio playback failed: {e}")
            return False
        except FileNotFoundError:
            if system == "Darwin":
                print("❌ afplay not found. This should be available on all macOS systems.")
                print("💡 Try: which afplay")
            else:
                print(f"❌ No audio player found for {system}")
            return False
        except Exception as e:
            print(f"❌ Unexpected audio error: {e}")
            return False

class EnhancedVoiceStorytellerClient:
    """Enhanced high-level client with voice narration capabilities - macOS compatible."""
    
    def __init__(self):
        self.mcp_client = MCPClient()
        self.audio_player = AudioPlayer()
        self.claude_available = False
        self.available_voices = {}
        self.last_audio_file = None
    
    async def start(self):
        """Initialize the enhanced client with voice capabilities."""
        success = await self.mcp_client.connect()
        if not success:
            raise ConnectionError("Failed to connect to enhanced storyteller server")
        
        # Get available voices
        self.available_voices = await self.mcp_client.list_voices()
        if self.available_voices:
            voice_count = sum(len(voices) for voices in self.available_voices.values())
            logger.info(f"🎵 Found {voice_count} available voices across multiple engines")
        
        # Check Claude availability
        try:
            test_story = await self.mcp_client.generate_story("test", 30)
            if test_story:
                self.claude_available = test_story.get("claude_available", False)
        except Exception:
            pass
    
    async def stop(self):
        """Clean up and disconnect."""
        await self.mcp_client.disconnect()
    
    def _format_voices_display(self) -> str:
        """Format available voices for display."""
        if not self.available_voices:
            return "❌ No voices available"
        
        output = []
        engine_emojis = {
            "pyttsx3": "🖥️",
            "gtts": "🌍",
            "edge_tts": "🎭"
        }
        
        for engine, voices in self.available_voices.items():
            available_voices = [v for v in voices if v['available']]
            if available_voices:
                emoji = engine_emojis.get(engine, "🎵")
                output.append(f"\n{emoji} {engine.upper()} ({len(available_voices)} voices):")
                
                for i, voice in enumerate(available_voices, 1):
                    style_emoji = {
                        "storyteller": "📚",
                        "parent": "👨‍👩‍👧‍👦",
                        "child": "👶",
                        "friendly": "😊"
                    }.get(voice['style'], "🎙️")
                    
                    gender_emoji = {
                        "male": "♂️",
                        "female": "♀️"
                    }.get(voice['gender'], "")
                    
                    output.append(f"   {i}. {style_emoji} {voice['name']} {gender_emoji}")
                    output.append(f"      ID: {voice['id']} | Style: {voice['style']}")
        
        return "\n".join(output) if output else "❌ No voices available"
    
    async def request_story(self, moral: str, length: int = 75, voice_id: Optional[str] = None, 
                          narrate: bool = False, show_details: bool = False) -> str:
        """Request an AI-enhanced story with optional voice narration."""
        story_data = await self.mcp_client.generate_story(moral, length, voice_id, narrate)
        
        if not story_data:
            return "❌ Failed to generate story. Please try again."
        
        # Enhanced formatting with voice indicators
        output = []
        output.append("=" * 70)
        output.append("🌟 AI-POWERED KIDS STORYTELLER WITH VOICE NARRATION 🌟")
        output.append("🍎 macOS Compatible - No Music App Interference!")
        output.append("=" * 70)
        output.append("")
        
        # Story metadata
        method_info = {
            "claude": "🤖 Fully AI-Generated by Claude",
            "hybrid": "🔥 Template Enhanced with Claude AI", 
            "template": "📚 Template-Based Generation"
        }
        
        generation_method = story_data.get('generation_method', 'template')
        method_description = method_info.get(generation_method, "📖 Unknown Method")
        
        output.append(f"📚 Title: {story_data['title']}")
        output.append(f"💛 Moral: {story_data['moral'].title()}")
        output.append(f"📊 Length: {story_data['length']} words")
        output.append(f"🤖 Created by: {story_data['agent_id'].replace('_', ' ').title()}")
        output.append(f"⚡ Generation: {method_description}")
        output.append(f"⭐ Quality Score: {story_data['score']:.2f}/1.00")
        output.append(f"🧠 AI Status: {'🟢 Claude Active' if story_data.get('claude_available') else '🟡 Template Mode'}")
        
        # Voice narration info
        voice_narration = story_data.get("voice_narration")
        if voice_narration:
            if voice_narration.get("success"):
                voice_name = voice_narration.get("voice_name", "Unknown")
                engine = voice_narration.get("engine", "unknown")
                duration = voice_narration.get("duration_estimate", 0)
                system_info = voice_narration.get("system", "Unknown")
                
                output.append(f"🎙️ Voice: {voice_name} ({engine})")
                output.append(f"⏱️ Duration: ~{duration:.1f} seconds")
                output.append(f"🖥️ System: {system_info}")
                
                if voice_narration.get("audio_file"):
                    self.last_audio_file = voice_narration["audio_file"]
                    if system_info == "Darwin":
                        output.append(f"🎵 Audio: Ready to play (afplay - no Music app!)")
                    else:
                        output.append(f"🎵 Audio: Ready to play")
            else:
                output.append(f"❌ Voice Error: {voice_narration.get('error', 'Unknown error')}")
        
        output.append("")
        
        output.append("📖 STORY:")
        output.append("-" * 50)
        
        # Format story for better readability
        story_content = story_data['content']
        if '. ' in story_content:
            sentences = story_content.split('. ')
            formatted_content = ""
            for i, sentence in enumerate(sentences):
                formatted_content += sentence
                if i < len(sentences) - 1:
                    formatted_content += ". "
                    if (i + 1) % 3 == 0:
                        formatted_content += "\n\n"
            story_content = formatted_content
        
        output.append(story_content)
        output.append("-" * 50)
        output.append("")
        
        # Voice controls
        if voice_narration and voice_narration.get("success"):
            output.append("🎵 VOICE CONTROLS:")
            output.append("   Type 'play' to hear the story")
            output.append("   Type 'replay' to play again")
            if platform.system() == "Darwin":
                output.append("   ✅ Uses afplay (no Music app interference)")
            output.append("")
        
        # Enhanced details section
        if show_details:
            output.append("🔍 GENERATION DETAILS:")
            output.append(f"AI Model: {'Claude 3.5 Sonnet' if story_data.get('claude_available') else 'Template System'}")
            output.append(f"Processing Method: {generation_method.title()}")
            output.append(f"System: {platform.system()}")
            
            if self.available_voices:
                output.append(f"Available Voice Engines: {', '.join(self.available_voices.keys())}")
            
            output.append("")
        
        output.append("=" * 70)
        
        return "\n".join(output)
    
    async def interactive_mode(self):
        """Enhanced interactive story generation session with voice."""
        system = platform.system()
        print("🌟 Welcome to the AI-Powered Voice Storyteller! 🌟")
        print("Now enhanced with voice narration capabilities!")
        
        if system == "Darwin":
            print("🍎 macOS Compatible Version - No Music App Interference!")
        
        if self.claude_available:
            print("🤖 ✅ Claude AI is ACTIVE - Stories will be intelligently generated")
        else:
            print("📚 ⚠️ Running in Template Mode - Consider adding ANTHROPIC_API_KEY")
        
        # Display available voices
        print("\n🎵 AVAILABLE VOICES:")
        print(self._format_voices_display())
        
        print("\nGenerate personalized stories with voice narration!\n")
        
        while True:
            try:
                print("\n" + "="*60)
                moral = input("Enter a moral/value to teach (or 'quit' to exit): ").strip()
                
                if moral.lower() in ['quit', 'exit', 'q']:
                    print("👋 Thanks for using the Voice Storyteller! Goodbye!")
                    break
                
                if not moral:
                    print("⚠️ Please enter a moral/value.")
                    continue
                
                # Enhanced length selection
                print("\n📊 Story Length Options:")
                print("   1. Short (50 words) - Quick lesson")
                print("   2. Medium (75 words) - Balanced story [Recommended]") 
                print("   3. Long (100 words) - Detailed narrative")
                print("   4. Custom length")
                
                length_choice = input("Choose length (1-4, or Enter for Medium): ").strip()
                
                length_map = {"1": 50, "2": 75, "3": 100}
                if length_choice in length_map:
                    length = length_map[length_choice]
                elif length_choice == "4":
                    try:
                        length = int(input("Enter custom word count (20-200): ").strip())
                        length = max(20, min(length, 200))
                    except ValueError:
                        length = 75
                        print("Using default length: 75 words")
                else:
                    length = 75
                
                # Voice selection
                use_voice = input("Add voice narration? (Y/n): ").strip().lower()
                narrate = use_voice != 'n'
                voice_id = None
                
                if narrate and self.available_voices:
                    print("\n🎙️ Choose a voice:")
                    print("   0. Default narrator")
                    
                    # Create a flat list of available voices
                    voice_options = []
                    for engine_voices in self.available_voices.values():
                        voice_options.extend([v for v in engine_voices if v['available']])
                    
                    for i, voice in enumerate(voice_options, 1):
                        engine_emoji = {"pyttsx3": "🖥️", "gtts": "🌍", "edge_tts": "🎭"}.get(
                            voice.get('engine', ''), "🎵"
                        )
                        print(f"   {i}. {engine_emoji} {voice['name']}")
                    
                    try:
                        choice = input(f"Select voice (0-{len(voice_options)}, or Enter for default): ").strip()
                        if choice and choice != "0":
                            choice_idx = int(choice) - 1
                            if 0 <= choice_idx < len(voice_options):
                                voice_id = voice_options[choice_idx]['id']
                                print(f"Selected: {voice_options[choice_idx]['name']}")
                        
                        if not voice_id:
                            voice_id = "default_narrator"
                            print("Using default narrator")
                            
                    except (ValueError, IndexError):
                        voice_id = "default_narrator"
                        print("Using default narrator")
                
                show_details = input("Show generation details? (y/N): ").strip().lower() == 'y'
                
                print(f"\n🎨 Generating {length}-word story about '{moral}'...")
                if narrate:
                    print("🎙️ Preparing voice narration...")
                print("⏳ Please wait...")
                
                story_output = await self.request_story(moral, length, voice_id, narrate, show_details)
                print("\n" + story_output)
                
                # Voice controls
                while True:
                    if self.last_audio_file:
                        action = input("\n🎵 Voice controls: 'play', 'replay' | Story options: 'new', 'continue' | Quit: 'q': ").strip().lower()
                    else:
                        action = input("\n📖 Options: 'new' story, 'continue', or 'q' to quit: ").strip().lower()
                    
                    if action in ['q', 'quit', 'continue', '']:
                        break
                    elif action == 'new':
                        break  # Go to outer loop for new story
                    elif action in ['play', 'replay'] and self.last_audio_file:
                        print("🎵 Playing story narration...")
                        if system == "Darwin":
                            print("🍎 Using afplay - no Music app will open!")
                        success = self.audio_player.play_audio_file(self.last_audio_file)
                        if success:
                            print("✅ Audio playback completed")
                        else:
                            print("❌ Could not play audio file")
                    elif action == 'voices':
                        print("\n🎙️ Available Voices:")
                        print(self._format_voices_display())
                    else:
                        print("❓ Unknown command. Try: play, new, continue, or q")
                
                if action == 'new':
                    continue  # Start new story
                elif action in ['q', 'quit']:
                    break  # Exit program
                    
            except KeyboardInterrupt:
                print("\n\n👋 Session interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Please try again.")
    
    async def demo_mode(self):
        """Run voice demonstration mode."""
        system = platform.system()
        print("🎬 Starting Voice Narration Demo Mode")
        if system == "Darwin":
            print("🍎 macOS Demo - No Music App Interference!\n")
        else:
            print()
        
        demo_requests = [
            {
                "moral": "honesty", 
                "length": 80, 
                "voice_id": "default_narrator",
                "note": "Default Narrator Demo"
            },
            {
                "moral": "kindness", 
                "length": 90, 
                "voice_id": "gtts_friendly",
                "note": "Google TTS Demo"
            }
        ]
        
        for i, request in enumerate(demo_requests, 1):
            print(f"🎭 Demo {i}/{len(demo_requests)}: {request['note']}")
            
            story_output = await self.request_story(
                request["moral"], 
                request["length"],
                request["voice_id"],
                narrate=True,
                show_details=True
            )
            print(story_output)
            
            # Auto-play demo audio
            if self.last_audio_file:
                print("🎵 Auto-playing demo narration...")
                if system == "Darwin":
                    print("🍎 Using afplay (macOS native)")
                success = self.audio_player.play_audio_file(self.last_audio_file)
                if success:
                    print("✅ Demo audio completed")
            
            if i < len(demo_requests):
                await asyncio.sleep(3)  # Pause between demos
                print("\n" + "⭐ Next Demo".center(50, " ") + "\n")

async def main():
    """Main function for the enhanced voice client - macOS compatible."""
    client = EnhancedVoiceStorytellerClient()
    system = platform.system()
    
    try:
        # Display startup info
        print("🚀 Starting AI-Powered Voice Storyteller Client")
        print("🎙️ With Multi-Engine Voice Narration Support")
        if system == "Darwin":
            print("🍎 macOS Compatible - No Music App Issues!")
        
        # Check dependencies
        print("\n🔍 Checking voice dependencies...")
        try:
            import pyttsx3
            print("  ✅ pyttsx3 (offline TTS)")
        except ImportError:
            print("  ❌ pyttsx3 - install with: pip install pyttsx3")
        
        try:
            import gtts
            print("  ✅ gTTS (Google TTS)")
        except ImportError:
            print("  ❌ gTTS - install with: pip install gtts")
        
        try:
            import edge_tts
            print("  ✅ Edge TTS (Microsoft voices)")
        except ImportError:
            print("  ❌ Edge TTS - install with: pip install edge-tts")
        
        # Check audio support
        print("\n🔊 Checking audio playback...")
        audio_player = AudioPlayer()
        if system == "Darwin":
            try:
                result = subprocess.run(["which", "afplay"], check=True, 
                                       capture_output=True, text=True)
                print("  ✅ afplay available (macOS native - no Music app!)")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("  ❌ afplay not found (should be available on macOS)")
        elif system == "Linux":
            players = ["paplay", "aplay", "play", "mpg123"]
            found_players = []
            for player in players:
                try:
                    subprocess.run(["which", player], check=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    found_players.append(player)
                except:
                    pass
            if found_players:
                print(f"  ✅ Audio players: {', '.join(found_players)}")
            else:
                print("  ⚠️ Limited audio support")
        elif system == "Windows":
            print("  ✅ Windows Media Player support")
        
        # Check for Claude API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            print("  ✅ Claude API key detected")
        else:
            print("  ⚠️ No Claude API key - template mode only")
        
        print("")
        
        # Connect to server
        await client.start()
        
        # Choice of demo or interactive
        mode = input("Choose mode: (d)emo or (i)nteractive? (default: interactive): ").strip().lower()
        
        if mode.startswith('d'):
            await client.demo_mode()
        
        # Interactive mode
        print("\n🎮 Entering Interactive Voice Mode...")
        await client.interactive_mode()
        
    except KeyboardInterrupt:
        print("\n👋 Session ended by user.")
    except Exception as e:
        print(f"❌ Client error: {e}")
        print("\n💡 Troubleshooting tips:")
        if system == "Darwin":
            print("   🍎 macOS Specific:")
            print("   - Make sure afplay is available (should be built-in)")
            print("   - This version avoids pygame to prevent Music app launching")
        print("   1. Install voice dependencies: pip install pyttsx3 gtts edge-tts")
        print("   2. Make sure the server file is available")
        print("   3. Set Claude API key: export ANTHROPIC_API_KEY='your-key'")
        if system == "Darwin":
            print("   4. No more Music app interference! 🎉")
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
