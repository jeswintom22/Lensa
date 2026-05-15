## Getting Started (First Time Setup)

Complete these steps in order before running the app.

### 1. Install Python dependencies
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt

### 2. Run the data pipeline
python build_pipeline.py --limit 100

### 3. Copy generated assets into Flutter
mkdir -p assets/database assets/audio
cp museum_guide.db assets/database/museum_guide.db
cp audio/*.mp3 assets/audio/

### 4. Set up Flutter
flutter create .
flutter pub get

### 5. Start the bridge server (keep this running)
python bridge_server.py

### 6. Run the app
flutter run

## Contributing

If you'd like to contribute or set up the project locally, follow the copy-paste commands below for your platform. These reproduce the steps in "Getting Started" with exact commands.

Windows (PowerShell):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# generate or update the local DB (run from repo root)
python build_pipeline.py --limit 100

# copy generated assets into Flutter
mkdir assets\database assets\audio
copy museum_guide.db assets\database\museum_guide.db
copy audio\*.mp3 assets\audio\

# create Flutter project files (only needed once)
d:\projects\Lensa\flutter\bin\flutter.bat create --project-name lensa .
d:\projects\Lensa\flutter\bin\flutter.bat pub get

# start bridge server (keep running)
python bridge_server.py

# run app
d:\projects\Lensa\flutter\bin\flutter.bat run
```

macOS / Linux (bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# generate or update the local DB
python build_pipeline.py --limit 100

# copy generated assets into Flutter
mkdir -p assets/database assets/audio
cp museum_guide.db assets/database/museum_guide.db
cp audio/*.mp3 assets/audio/

# create Flutter project files (only needed once)
/path/to/flutter/bin/flutter create --project-name lensa .
/path/to/flutter/bin/flutter pub get

# start bridge server (keep running)
python bridge_server.py

# run app
/path/to/flutter/bin/flutter run
```

Tips:
- Replace `/path/to/flutter` with your Flutter SDK path if `flutter` isn't on your PATH.
- The `assets/database` and `assets/audio` folders are tracked only with placeholder `.gitkeep` files; copy the generated `museum_guide.db` and audio files into those folders locally.

# Lensa

Lensa is a free mobile museum guide for The Metropolitan Museum of Art.
It recognizes artworks with on-device computer vision (ORB feature matching) and shows metadata/audio without paid AI APIs.

## Core Stack

- Flutter (mobile app)
- OpenCV ORB (image recognition)
- SQLite (local storage)
- gTTS + Flutter audioplayers (audio narration)
- The Met Collection API (data source)

## Current Files

- `met_data_pipeline.py`: pulls artwork metadata and downloads images
- `artwork_recognition.py`: extracts ORB features and performs matching
- `audio_generator.py`: generates narration audio
- `bridge_server.py`: FastAPI bridge server for Flutter -> recognition
- `build_pipeline.py`: runs data -> features -> audio in sequence
- `verify_db.py`: checks DB + media health
- `benchmark_recognition.py`: self-consistency recognition benchmark
- `flutter_app_structure.dart`: legacy Flutter skeleton (reference only)
- `lib/` + `pubspec.yaml`: Flutter app implementation (created for this repo)
- `images/`: artwork image files (tracked)
- `audio/`: narration MP3s (tracked)

Note: `museum_guide.db` is treated as a local/generated artifact and is ignored by git (use the pipeline to regenerate it).

## Quickstart (Local)

### 1) Python backend (bridge server)

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python bridge_server.py
```

Health check:

```bash
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

### 2) Copy DB + audio into Flutter assets

Flutter reads a bundled SQLite file and audio assets at runtime.

```bash
New-Item -ItemType Directory -Force -Path assets\database, assets\audio | Out-Null
Copy-Item museum_guide.db assets\database\museum_guide.db -Force
Copy-Item audio\*.mp3 assets\audio\ -Force
```

### 3) Run the Flutter app

This repo does not include the Flutter platform shell folders by default. Create them once:

```bash
flutter create .
flutter pub get
flutter run
```

## Setup

```bash
pip install -r requirements.txt
```

## Data Pipeline

Fetch artworks + images:

```bash
python met_data_pipeline.py --limit 100 --db-path museum_guide.db --images-dir images
```

## Recognition Pipeline

Build ORB features from `images/` into SQLite:

```bash
python artwork_recognition.py --build --db-path museum_guide.db --images-dir images
```

Recognize a query image:

```bash
python artwork_recognition.py --query "path/to/query.jpg" --db-path museum_guide.db
```

Useful query options:

- `--confidence-threshold 0.18`
- `--ratio-test 0.75`
- `--min-good-matches 12`

If confidence is below threshold, the script returns `None`.

## Notes

- Recognition quality depends on lighting, angle, and image clarity.
- The pipeline is designed to run locally and avoid cloud inference costs.

## Generate DB + assets (optional)

Run everything end-to-end:

```bash
python build_pipeline.py --limit 100 --db-path museum_guide.db --images-dir images --audio-dir audio
```

Verify DB/media:

```bash
python verify_db.py --db-path museum_guide.db --images-dir images --audio-dir audio
```

Benchmark recognition (self-consistency test):

```bash
python benchmark_recognition.py --images-dir images --db-path museum_guide.db
```
