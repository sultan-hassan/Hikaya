AI-powered Kids Storyteller (generated and powered by Claude) as part of the 'Build the Future with MCP' Hackathon (https://lu.ma/ubc9n92v?tk=nCAZZ0&utm_source=ep-LSmBrViHqG). 



**Ready to create magical stories with UV's blazing speed? Let's get started! ⚡🌟**

### Quick Start Summary
```bash
# The entire setup in 4 commands (Simple Approach):
git clone https://github.com/yourusername/Hikaya.git
cd Hikaya
uv venv && source .venv/bin/activate
uv pip install -r requirements-simple.txt && echo "ANTHROPIC_API_KEY=your_key" > .env

# Run it:
python voice_storyteller_client.py
```

![](./pipeline.png)



# Installation and Setup Guide (Using UV)

## 📋 Prerequisites

- **UV Package Manager** ([Install UV](https://docs.astral.sh/uv/getting-started/installation/))
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Internet Connection** (for Google TTS and Edge TTS engines)
- **Audio Output Device** (speakers or headphones for voice narration)

## ⚡ Super Fast Installation with UV

### 1. Install UV (if not already installed)
```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative: Using pip
pip install uv
```

### 2. Clone and Setup Project
```bash
# Clone the repository
git clone https://github.com/yourusername/hikaya.git
cd hikaya

# Option A: Simple dependency-only install (recommended for most users)
uv pip install -r requirements-simple.txt

# Option B: Full project install with editable mode
uv sync

# Or for development with extra dependencies
uv sync --extra dev
```

### 3. Alternative: Simple Requirements File Approach

If you encounter build issues, use the traditional approach:

Create `requirements-simple.txt`:
```txt
# Core Dependencies
python-dotenv>=1.0.0

# AI and Claude Integration  
anthropic>=0.25.0

# Voice Synthesis Engines
pyttsx3>=2.90
gTTS>=2.4.0
edge-tts>=6.1.9

# Audio Processing and Playback
pygame>=2.5.2
pydub>=0.25.1

# Web and Network
aiohttp>=3.9.1
requests>=2.31.0

# Data Processing
numpy>=1.24.3

# UI and Logging
colorama>=0.4.6
rich>=13.7.0
```

Then install with:
```bash
# Create virtual environment with UV
uv venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv pip install -r requirements-simple.txt
```

### 4. Platform-Specific Audio Dependencies

#### All Platforms (Automatic)
```bash
# If using pyproject.toml approach:
# Install with audio extras
uv sync --extra audio-extra

# Platform-specific extras
# Windows:
uv sync --extra windows --extra audio-extra
# macOS:  
uv sync --extra macos --extra audio-extra

# If using simple requirements approach:
# Additional audio packages
uv pip install simpleaudio pyaudio  # optional enhanced audio
```

#### Linux System Dependencies
```bash
# Install system audio dependencies first
sudo apt update
sudo apt install espeak espeak-data libespeak-dev
sudo apt install portaudio19-dev python3-dev
sudo apt install ffmpeg pulseaudio-utils

# Then install Python packages
uv sync --extra audio-extra
```

### 5. Configure Environment
```bash
# Copy environment template (if available)
cp .env.example .env

# Or create new .env file
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# Edit with your preferred editor if needed
nano .env  # or code .env, vim .env, etc.
```

## 🚀 Running the Application

### Quick Start (Simple Approach)
```bash
# Activate environment if using venv approach
source .venv/bin/activate  # macOS/Linux  
# or .venv\Scripts\activate  # Windows

# Run the storyteller
python voice_storyteller_client.py
```

### Quick Start (Project Install Approach)
```bash
# Run with UV directly
uv run hikaya

# Or run the Python files directly
uv run python voice_storyteller_client.py
```

### Development Mode
```bash
# Install with development dependencies
uv sync --extra dev

# Run with development tools
uv run python voice_storyteller_client.py

# Run tests
uv run pytest

# Format code
uv run black .
uv run ruff check .
```

### Server Mode
```bash
# Run the MCP server (project install)
uv run hikaya-server
# OR direct Python execution
uv run python voice_storyteller_server.py

# Run the MCP server (simple venv)
python voice_storyteller_server.py
```

## 🔧 Troubleshooting Build Issues

### If you get build/hatchling errors:

**Option 1: Use Simple Requirements (Recommended)**
```bash
# Delete any existing virtual environment
rm -rf .venv

# Create fresh environment
uv venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# Install with simple requirements
uv pip install -r requirements-simple.txt

# Run directly
python voice_storyteller_client.py
```

**Option 2: Fix Project Structure**
```bash
# Create proper package structure
mkdir hikaya
mv voice_storyteller_*.py hikaya/
touch hikaya/__init__.py

# Then try uv sync again
uv sync
```

**Option 3: Development Mode**
```bash
# Install in development mode without building
uv pip install -e . --no-build-isolation
```

## 🎯 UV Advantages for This Project

### ⚡ **Lightning Fast Installation**
```bash
# Traditional pip approach (2-3 minutes)
python -m venv venv
source venv/bin/activate  # or Windows equivalent
pip install -r requirements.txt

# UV approach (10-20 seconds!)
uv sync
```

### 🔄 **Dependency Management**
```bash
# Add new dependency
uv add anthropic

# Add development dependency  
uv add --dev pytest

# Update all dependencies
uv sync --upgrade

# Remove dependency
uv remove package-name
```

### 🧪 **Quick Testing & Development**
```bash
# Run tests without activation
uv run pytest

# Try different Python versions
uv run --python 3.9 python voice_storyteller_client.py
uv run --python 3.11 python voice_storyteller_client.py

# Run specific scripts
uv run --with rich python -c "from rich import print; print('[green]Hello![/green]')"
```

### 📦 **Environment Isolation**
```bash
# Each project gets its own isolated environment automatically
# No need for manual venv management!

# Check environment info
uv pip list

# Show dependency tree
uv tree
```

## 🔧 Advanced UV Usage

### Multiple Configurations
```bash
# Install different combinations
uv sync                                    # Basic installation
uv sync --extra dev                       # With development tools
uv sync --extra audio-extra --extra dev   # Full development setup
uv sync --extra windows                   # Windows-specific
```

### Lock File Benefits
```bash
# UV automatically creates uv.lock for reproducible builds
# Commit uv.lock to ensure everyone gets identical dependencies

# Update lock file
uv lock

# Install from lock file (production)
uv sync --frozen
```

### Cross-Platform Testing
```bash
# Test on different Python versions (if installed)
uv run --python 3.8 python voice_storyteller_client.py
uv run --python 3.9 python voice_storyteller_client.py  
uv run --python 3.10 python voice_storyteller_client.py
uv run --python 3.11 python voice_storyteller_client.py
```

## 🐛 Troubleshooting with UV

### Common UV Commands
```bash
# Check UV version
uv --version

# Reinstall all dependencies
uv sync --reinstall

# Clear UV cache
uv cache clean

# Show environment information
uv python list
uv pip list
```

### Audio Issues
```bash
# Reinstall audio packages specifically
uv pip install --reinstall pyttsx3 pygame gTTS

# Install with specific versions
uv add "pyttsx3==2.90" "pygame>=2.5.2"
```

### API Connection Issues
```bash
# Test Claude API quickly
uv run python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('API Key loaded:', bool(os.getenv('ANTHROPIC_API_KEY')))
"
```

## 📱 Usage Examples

### Basic Story Generation
```bash
# Run interactive mode
uv run storyteller

# Or with specific moral
uv run python -c "
import asyncio
from voice_storyteller_client import EnhancedVoiceStorytellerClient

async def quick_story():
    client = EnhancedVoiceStorytellerClient()
    await client.start()
    story = await client.request_story('kindness', 75)
    print(story)
    await client.stop()

asyncio.run(quick_story())
"
```

### Demo Mode
```bash
# Quick demo
uv run python voice_storyteller_client.py
# Choose 'd' for demo mode when prompted
```

## ⚖️ UV vs Traditional Pip

| Feature | Traditional Pip | UV |
|---------|----------------|-----|
| **Installation Speed** | 2-3 minutes | 10-20 seconds |
| **Environment Management** | Manual venv | Automatic |
| **Dependency Resolution** | Basic | Advanced solver |
| **Lock Files** | Manual requirements.txt | Automatic uv.lock |
| **Cross-platform** | Manual handling | Automatic |
| **Python Version Management** | Manual | Built-in |

## 🎉 Why UV is Perfect for AI Projects

1. **Fast Iteration**: Quickly test different AI model versions
2. **Reproducible Builds**: Lock files ensure consistent deployments
3. **Cross-Platform**: Seamlessly works across development environments
4. **Modern Tooling**: Built-in support for pyproject.toml
5. **Dependency Hell Prevention**: Advanced solver handles complex AI library conflicts

## 🆘 Getting Help

- **UV Documentation**: https://docs.astral.sh/uv/
- **Project Issues**: Report bugs on GitHub Issues
- **UV Issues**: https://github.com/astral-sh/uv/issues

---

**Ready to create magical stories with UV's blazing speed? Let's get started! ⚡🌟**

### Quick Start Summary
```bash
# The entire setup in 4 commands (Simple Approach):
git clone https://github.com/yourusername/hikaya.git
cd hikaya  
uv venv && source .venv/bin/activate
uv pip install -r requirements-simple.txt && echo "ANTHROPIC_API_KEY=your_key" > .env

# Run it:
python voice_storyteller_client.py
```

### Create requirements-simple.txt file:
```bash
# Create the simple requirements file
cat > requirements-simple.txt << 'EOF'
# Core Dependencies
python-dotenv>=1.0.0

# AI and Claude Integration  
anthropic>=0.25.0

# Voice Synthesis Engines
pyttsx3>=2.90
gTTS>=2.4.0
edge-tts>=6.1.9

# Audio Processing and Playback
pygame>=2.5.2
pydub>=0.25.1

# Web and Network
aiohttp>=3.9.1
requests>=2.31.0

# Data Processing
numpy>=1.24.3

# UI and Logging
colorama>=0.4.6
rich>=13.7.0
EOF
```