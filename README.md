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
- `flutter_app_structure.dart`: Flutter app skeleton
- `museum_guide.db`: SQLite database
- `images/`: artwork image files

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

   
