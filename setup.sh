#!/bin/bash

# Museum Guide App - Automated Setup Script
# This script sets up the entire project from scratch

set -e  # Exit on error

echo "╔══════════════════════════════════════════════════════╗"
echo "║   Museum Guide App - Setup Script                   ║"
echo "║   This will set up the entire project               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if Python is installed
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_status "Python ${PYTHON_VERSION} found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip."
    exit 1
fi
print_status "pip3 found"

# Create project directory structure
echo ""
echo "Creating project structure..."
mkdir -p data-pipeline
mkdir -p mobile/assets/database
mkdir -p mobile/assets/audio
mkdir -p docs
mkdir -p tests

print_status "Project directories created"

# Set up Python virtual environment
echo ""
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
print_status "Virtual environment activated"

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

print_status "Python dependencies installed"

# Move Python files to data-pipeline directory
echo ""
echo "Organizing files..."
mv met_data_pipeline.py data-pipeline/ 2>/dev/null || true
mv artwork_recognition.py data-pipeline/ 2>/dev/null || true
mv audio_generator.py data-pipeline/ 2>/dev/null || true
mv requirements.txt data-pipeline/ 2>/dev/null || true

print_status "Files organized"

# Create a simple test script
cat > data-pipeline/test_setup.py << 'EOF'
"""
Quick test to verify setup is working
"""
import cv2
import sqlite3
from gtts import gTTS
import requests

def test_imports():
    """Test that all required modules can be imported"""
    try:
        print("Testing imports...")
        print("  ✓ OpenCV imported")
        print("  ✓ SQLite3 imported")
        print("  ✓ gTTS imported")
        print("  ✓ Requests imported")
        print("\n✓ All imports successful!")
        return True
    except ImportError as e:
        print(f"\n✗ Import failed: {e}")
        return False

def test_met_api():
    """Test connection to Met Museum API"""
    try:
        print("\nTesting Met Museum API...")
        url = "https://collectionapi.metmuseum.org/public/collection/v1/objects/436535"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✓ Successfully fetched: {data.get('title', 'Unknown')}")
            return True
        else:
            print(f"  ✗ API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ API test failed: {e}")
        return False

def test_opencv():
    """Test OpenCV functionality"""
    try:
        print("\nTesting OpenCV...")
        orb = cv2.ORB_create()
        print(f"  ✓ ORB detector created successfully")
        return True
    except Exception as e:
        print(f"  ✗ OpenCV test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Museum Guide App - Setup Verification")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 3
    
    if test_imports():
        tests_passed += 1
    
    if test_opencv():
        tests_passed += 1
    
    if test_met_api():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n✓ Setup verified! You're ready to start building.")
    else:
        print("\n⚠ Some tests failed. Please check error messages above.")
    print("=" * 60)
EOF

# Run verification test
echo ""
echo "Running setup verification..."
python3 data-pipeline/test_setup.py

# Check if Flutter is installed (optional)
echo ""
echo "Checking Flutter installation (optional)..."
if command -v flutter &> /dev/null; then
    FLUTTER_VERSION=$(flutter --version | head -1)
    print_status "${FLUTTER_VERSION}"
else
    print_warning "Flutter not found. Install from https://flutter.dev to build mobile app"
fi

# Create a quick start guide
cat > QUICKSTART.md << 'EOF'
# Quick Start Guide

## 🚀 Getting Started

### 1. Activate Virtual Environment
```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 2. Fetch Artwork Data
```bash
cd data-pipeline
python met_data_pipeline.py
```

This will:
- Download 100+ famous artworks from The Met
- Create SQLite database
- Save high-resolution images

### 3. Build Recognition Database
```bash
python artwork_recognition.py
```

This will:
- Extract ORB features from each artwork
- Build searchable feature database
- Takes ~10-15 minutes

### 4. Generate Audio Narrations
```bash
python audio_generator.py
```

This will:
- Create TTS audio for each artwork
- Save MP3 files
- Takes ~5-10 minutes

### 5. Test Recognition
```bash
python -c "
from artwork_recognition import ArtworkRecognitionEngine
engine = ArtworkRecognitionEngine()
engine.test_recognition('path/to/test/image.jpg')
"
```

## 📱 Mobile App

### Setup Flutter App
```bash
cd mobile
flutter pub get
```

### Copy Database
```bash
cp ../data-pipeline/museum_guide.db assets/database/
```

### Run App
```bash
flutter run
```

## 🎯 Next Steps

1. Visit The Met Museum
2. Try scanning artworks with the app
3. Share feedback and improvements
4. Expand the collection

## 📚 Documentation

- See `README.md` for full documentation
- Check `TECHNICAL_ARCHITECTURE.md` for detailed design
- Browse `docs/` folder for more guides

EOF

print_status "Quick start guide created: QUICKSTART.md"

# Final summary
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║                  Setup Complete!                     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "📁 Project structure:"
echo "   ├── data-pipeline/     Python scripts"
echo "   ├── mobile/            Flutter app"
echo "   ├── docs/              Documentation"
echo "   └── venv/              Python environment"
echo ""
echo "🎯 Next steps:"
echo "   1. cd data-pipeline"
echo "   2. python met_data_pipeline.py"
echo "   3. python artwork_recognition.py"
echo "   4. python audio_generator.py"
echo ""
echo "📖 See QUICKSTART.md for detailed instructions"
echo ""
print_status "Ready to build! 🚀"
