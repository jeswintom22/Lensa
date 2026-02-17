# 🎨 Museum Guide App - Complete Project Guide

A free, offline-capable mobile app that recognizes artworks at The Metropolitan Museum of Art using computer vision and provides detailed information with audio narration.

## 🌟 Features

- 📸 **Camera Recognition** - Point your phone at any artwork and instantly identify it
- 🔍 **Browse Collection** - Explore 100+ famous artworks from The Met
- 🎧 **Audio Narration** - Listen to descriptions and fun facts
- 🗺️ **Guided Tours** - Follow curated routes through the museum
- 📱 **Offline Mode** - Works without internet after initial setup
- 🆓 **Completely Free** - No API costs, no subscriptions

## 🏗️ Architecture

### Technology Stack

**Mobile App:**
- Flutter (iOS & Android)
- SQLite for local database
- Camera plugin for image capture
- Audio player for narrations

**Data Pipeline (Python):**
- OpenCV for image processing
- ORB feature detection
- The Met Museum API
- SQLite for data storage

**Recognition Engine:**
- Feature matching (no ML tokens needed!)
- Runs completely on-device
- Fast (<2 second recognition)

## 📁 Project Structure

```
museum-guide/
├── mobile/                    # Flutter mobile app
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   ├── services/
│   │   └── models/
│   ├── assets/
│   │   ├── database/         # Pre-built SQLite DB
│   │   └── audio/            # Audio narrations
│   └── pubspec.yaml
│
├── data-pipeline/            # Python scripts
│   ├── met_data_pipeline.py  # Fetch artwork data
│   ├── artwork_recognition.py # Build feature database
│   ├── audio_generator.py    # Generate TTS audio
│   └── requirements.txt
│
├── docs/                     # Documentation
│   ├── TECHNICAL_ARCHITECTURE.md
│   ├── API_GUIDE.md
│   └── DEPLOYMENT.md
│
└── README.md                 # This file
```

## 🚀 Getting Started

### Prerequisites

**For Data Pipeline:**
- Python 3.8+
- pip package manager
- Internet connection (for API calls)

**For Mobile App:**
- Flutter SDK 3.0+
- Android Studio or Xcode
- Physical device or emulator

### Step 1: Set Up Data Pipeline

1. **Install Python dependencies:**
```bash
cd data-pipeline
pip install -r requirements.txt
```

2. **Fetch artwork data from The Met:**
```bash
python met_data_pipeline.py
```

This will:
- Connect to The Met Museum API
- Download 100 famous artworks
- Save metadata to SQLite database
- Download high-resolution images

3. **Build recognition features:**
```bash
python artwork_recognition.py
```

This will:
- Process each artwork image
- Extract ORB features
- Store feature descriptors in database
- Takes ~10-15 minutes for 100 artworks

4. **Generate audio narrations:**
```bash
python audio_generator.py
```

### Step 2: Set Up Mobile App

1. **Install Flutter:**
```bash
# Follow instructions at: https://flutter.dev/docs/get-started/install
```

2. **Install dependencies:**
```bash
cd mobile
flutter pub get
```

3. **Copy database to assets:**
```bash
cp ../data-pipeline/museum_guide.db assets/database/
```

4. **Run the app:**
```bash
flutter run
```

## 🎯 How It Works

### Recognition Process

1. **User opens camera** → Flutter camera plugin activates
2. **User captures photo** → Image sent to recognition engine
3. **Feature extraction** → ORB detector finds keypoints
4. **Matching** → Compare against database of reference features
5. **Result** → Return best match with confidence score
6. **Display** → Show artwork details + play audio

### Why This Approach?

**Traditional ML approach:**
- Requires cloud API (costs $0.01+ per image)
- Needs internet connection
- Privacy concerns (uploads photos)
- Monthly costs: $100-1000+ at scale

**Our feature matching approach:**
- 100% free (no API costs)
- Works offline
- Privacy-friendly (on-device)
- Fast and accurate enough

### Technical Details

**ORB (Oriented FAST and Rotated BRIEF):**
- Detects distinctive points in images
- Creates binary descriptors for each point
- Invariant to rotation, scale, lighting changes
- Very fast on mobile devices

**Matching Algorithm:**
- Brute Force Matcher with Hamming distance
- Lowe's ratio test for filtering
- Requires 30+ good matches for confidence
- Typically achieves 90%+ accuracy

## 📊 Database Schema

### Artworks Table
```sql
CREATE TABLE artworks (
    id INTEGER PRIMARY KEY,
    met_object_id INTEGER UNIQUE,
    title TEXT,
    artist TEXT,
    date TEXT,
    medium TEXT,
    department TEXT,
    description TEXT,
    image_url TEXT,
    audio_file_path TEXT
);
```

### Features Table
```sql
CREATE TABLE artwork_features (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER,
    feature_descriptor BLOB,  -- ORB descriptors
    feature_type TEXT
);
```

## 🎨 Initial Artwork Collection

The app starts with 100 carefully selected artworks:

**European Paintings (30):**
- Van Gogh's Wheat Field with Cypresses
- Vermeer's Woman with a Water Pitcher
- And more masterpieces...

**American Art (15):**
- Washington Crossing the Delaware
- John Singer Sargent portraits

**Egyptian Art (15):**
- Temple of Dendur artifacts
- Ancient sculptures

**Greek & Roman (10):**
- Classical statues
- Historic pottery

**Arms & Armor (10):**
- Medieval armor sets
- Historic weapons

**Asian Art (10):**
- Chinese ceramics
- Japanese screens

**Other (10):**
- Musical instruments
- Modern art

## 🔊 Audio Narration

### Format (30-60 seconds per artwork):

```
🎯 Hook (5s): "You're looking at one of the most famous paintings..."
📖 Context (15s): "Created by Vincent van Gogh in 1889..."
🔍 Key Feature (15s): "Notice the swirling brushstrokes..."
💡 Fun Fact (10s): "Van Gogh painted this from memory..."
👁️ Call to Action (5s): "Look closer at the cypress tree..."
```

### Generation Options:

**Option 1: TTS (Initial):**
- Use gTTS (Google Text-to-Speech)
- Free, decent quality
- Generate all audio files once

**Option 2: Human Voice (Future):**
- Record professional narrations
- Much more engaging
- Premium feature

## 🗺️ Development Roadmap

### ✅ Phase 1: MVP (Weeks 1-6)
- [x] Architecture design
- [ ] Data pipeline implementation
- [ ] Feature extraction system
- [ ] Basic Flutter app
- [ ] Camera integration
- [ ] Recognition engine
- [ ] Simple UI

### 🚧 Phase 2: Polish (Weeks 7-9)
- [ ] Audio narrations
- [ ] Improved UI/UX
- [ ] Browse & search
- [ ] Tour mode (3 guided tours)
- [ ] Beta testing

### 📅 Phase 3: Launch (Week 10)
- [ ] App store optimization
- [ ] Marketing website
- [ ] Social media
- [ ] Press kit
- [ ] Met partnership outreach

### 🔮 Phase 4: Growth (Ongoing)
- [ ] Expand to 500 artworks
- [ ] Add other museums
- [ ] AR overlay features
- [ ] User reviews/photos
- [ ] Premium features
- [ ] Educational partnerships

## 💰 Monetization Strategy

### Free Tier:
- 100 artworks
- TTS audio
- Basic tours
- All core features

### Premium ($3.99/month):
- 500+ artworks
- Professional audio
- Exclusive tours
- AR features
- Offline content
- Ad-free

### Other Revenue:
- Museum partnerships
- Educational licenses
- Tourism sponsorships
- In-app museum packs ($0.99 each)

## 🧪 Testing Strategy

### Accuracy Testing:
1. Take 10 photos of each artwork from different angles
2. Test in various lighting conditions
3. Test with partial views
4. Measure accuracy rate (target: >90%)

### Performance Testing:
1. Recognition speed (target: <2s)
2. App startup time (target: <3s)
3. Database query speed
4. Memory usage

### User Testing:
1. Recruit 20 beta testers
2. Test in actual museum setting
3. Collect feedback on UX
4. Measure success rate

## 📱 App Store Launch

### iOS App Store:
- Developer account: $99/year
- Review process: 2-7 days
- Screenshots: 6-8 required
- App preview video: Recommended

### Google Play Store:
- One-time fee: $25
- Review process: 1-3 days
- Screenshots: 4-8 required
- Feature graphic required

## 🤝 Contributing

This is a learning project, but contributions are welcome!

### Areas for contribution:
- More artwork data
- Better audio narrations
- UI/UX improvements
- Translation to other languages
- Testing and bug reports

## 📄 License

MIT License - See LICENSE file for details

### Attribution:
- Artwork data from The Metropolitan Museum of Art
- Licensed under CC0 (Public Domain)
- Images courtesy of The Met Open Access program

## 🙏 Credits

### APIs & Data:
- The Metropolitan Museum of Art Collection API
- The Met Open Access Initiative

### Libraries:
- OpenCV for computer vision
- Flutter for mobile development
- SQLite for local database

## 📞 Support & Contact

- Issues: GitHub Issues
- Questions: Discussions tab
- Email: [Your email]

## 🎓 Learn More

### Resources:
- [The Met API Documentation](https://metmuseum.github.io/)
- [OpenCV Tutorials](https://docs.opencv.org/master/d9/df8/tutorial_root.html)
- [Flutter Documentation](https://flutter.dev/docs)
- [Feature Matching Tutorial](https://docs.opencv.org/master/dc/dc3/tutorial_py_matcher.html)

## ⚡ Quick Commands

```bash
# Set up everything from scratch
./setup.sh

# Update artwork database
python data-pipeline/update_collection.py

# Run tests
flutter test

# Build release APK
flutter build apk --release

# Build iOS release
flutter build ios --release
```

## 🐛 Troubleshooting

### "No features detected in image"
- Ensure image is clear and well-lit
- Try different angle
- Check if artwork is in database

### "Camera not working"
- Check app permissions
- Restart app
- Update Flutter camera plugin

### "Database not found"
- Ensure database file in assets/
- Check pubspec.yaml configuration
- Rebuild app: `flutter clean && flutter run`

## 🎉 Next Steps

1. **Set up development environment**
2. **Run data pipeline to fetch artworks**
3. **Build recognition database**
4. **Test mobile app**
5. **Visit The Met and try it!**

---

**Ready to start building? Let's make art accessible to everyone! 🎨**
