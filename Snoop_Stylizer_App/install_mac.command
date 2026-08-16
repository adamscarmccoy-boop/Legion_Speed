#!/bin/bash
echo "==========================================="
echo "🎙️ Installing Medical Voice Stylizer (Mac)"
echo "==========================================="

# 1. Install Homebrew if not found
if ! command -v brew &> /dev/null
then
    echo "🍺 Homebrew not found. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add brew to PATH for Apple Silicon just in case
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
else
    echo "✅ Homebrew is already installed."
fi

# 2. Install System Dependencies
echo "🎧 Installing PortAudio (required for PyAudio)..."
brew install portaudio

echo "🎛️ Installing BlackHole Virtual Audio Cable (for PowerPoint/Zoom)..."
brew install --cask blackhole-2ch

# 3. Setup Python Virtual Environment
echo "🐍 Setting up Python environment..."
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

echo "📦 Installing Python packages (this might take a few minutes)..."
pip install --upgrade pip
# Install all required Python packages
pip install pyaudio numpy pedalboard torch librosa soundfile yt-dlp PyQt5

# 4. Generate Voice Profiles (Crucial for the app's functionality!)
echo "🧬 Generating initial voice profiles (Snoop, Dolly)... This will download audio clips and calculate math. Please be patient."

echo "🧬 Audio profiles are already bundled. Skipping generation to prevent re-downloading."

# 5. Create Desktop Shortcut
echo "🖥️ Creating Desktop Shortcut..."
SHORTCUT_PATH=~/Desktop/Snoop_Stylizer.command
echo '#!/bin/bash' > "$SHORTCUT_PATH"
echo "cd \"$DIR\"" >> "$SHORTCUT_PATH"
echo 'source .venv/bin/activate' >> "$SHORTCUT_PATH"
echo 'python snoop_voice_app.py' >> "$SHORTCUT_PATH"
chmod +x "$SHORTCUT_PATH"
echo "✅ Shortcut created on Desktop: Snoop_Stylizer.command"

echo "==========================================="
echo "✅ Installation Complete! You can now launch from your Desktop."
echo "🚀 Launching Voice Stylizer for the first time..."
echo "==========================================="

python snoop_voice_app.py
