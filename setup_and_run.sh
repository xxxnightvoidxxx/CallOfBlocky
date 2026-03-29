#!/bin/bash
# Venvy setup script for Linux

echo "========================================="
echo "Call of Blocky: Duel Protocol - Setup"
echo "========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    echo "On Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "On Fedora: sudo dnf install python3 python3-virtualenv python3-pip"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Installing..."
    python3 -m ensurepip --upgrade
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install pygame
echo "Installing pygame..."
pip install pygame

# Check if assets directory exists
if [ ! -d "assets" ]; then
    echo ""
    echo "WARNING: assets directory not found!"
    echo "The game expects sound files in:"
    echo "  assets/sound/fireplayer/ - Player gunshot sounds"
    echo "  assets/sound/firenpc/ - NPC gunshot sounds"
    echo "  assets/sound/matchresults.mp3 - End game music"
    echo ""
    echo "The game will still run without sounds, but for full experience"
    echo "please add these sound files."
    echo ""
    read -p "Press Enter to continue..."
fi

# Run the game
echo ""
echo "Starting Call of Blocky: Duel Protocol..."
echo "Controls:"
echo "  WASD or Arrow Keys - Move player"
echo "  SPACE - Shoot"
echo "  R - Restart after match ends"
echo "========================================="
echo ""

python3 call_of_blocky.py

# Deactivate virtual environment on exit
deactivate