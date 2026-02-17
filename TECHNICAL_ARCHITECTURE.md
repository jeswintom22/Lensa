# Museum Guide App - Complete Technical Architecture

## 🎯 Project Overview

**Name:** MuseumLens (working title)
**Goal:** Free mobile app that recognizes famous artworks via camera and provides detailed information with audio narration
**Target Museum:** The Metropolitan Museum of Art (expandable to others)
**Platform:** Mobile-first (iOS/Android) with potential web version

---

## 📊 System Architecture

### High-Level Flow
```
User opens app → Points camera at artwork → Image recognition → Match to database → 
Display info + play audio → User can explore more details
```

### Components

#### 1. **Mobile App (Frontend)**
- Framework: **Flutter** (single codebase for iOS/Android)
- Alternative: React Native
- Features:
  - Camera integration
  - Offline-capable database
  - Audio playback
  - Search/browse artworks
  - Tour mode (guided routes)

#### 2. **Image Recognition System**
- **Approach:** Feature matching (not AI/ML tokens!)
- Technology: 
  - OpenCV for feature extraction
  - SIFT/ORB algorithms for image fingerprinting
  - KD-Tree or FLANN for fast matching
- Process:
  1. Extract features from reference images (done once, offline)
  2. User takes photo → extract features
  3. Match against pre-computed database
  4. Return best match with confidence score

#### 3. **Database**
- **Local (on-device):** SQLite
  - Artwork metadata (title, artist, date, description)
  - Pre-computed image features
  - Audio file references
- **Cloud backup:** Firebase/Supabase (for updates)

#### 4. **Content Pipeline**
- Pull data from Met API
- Download high-res images
- Generate image features
- Create/record audio narrations
- Package for app distribution

---

## 🗄️ Database Schema

### Artworks Table
```sql
CREATE TABLE artworks (
    id INTEGER PRIMARY KEY,
    met_object_id INTEGER UNIQUE,
    title TEXT NOT NULL,
    artist TEXT,
    artist_display_name TEXT,
    date TEXT,
    medium TEXT,
    department TEXT,
    culture TEXT,
    period TEXT,
    dynasty TEXT,
    description TEXT,
    fun_fact TEXT,
    location_gallery TEXT,
    image_url TEXT,
    image_small_url TEXT,
    audio_file_path TEXT,
    featured BOOLEAN DEFAULT 0,
    popularity_score INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE artwork_features (
    id INTEGER PRIMARY KEY,
    artwork_id INTEGER,
    feature_descriptor BLOB,  -- Pre-computed SIFT/ORB features
    feature_type TEXT,  -- 'sift', 'orb', etc.
    FOREIGN KEY (artwork_id) REFERENCES artworks(id)
);

CREATE TABLE tours (
    id INTEGER PRIMARY KEY,
    name TEXT,
    description TEXT,
    duration_minutes INTEGER,
    difficulty TEXT  -- 'easy', 'medium', 'hard'
);

CREATE TABLE tour_stops (
    id INTEGER PRIMARY KEY,
    tour_id INTEGER,
    artwork_id INTEGER,
    stop_order INTEGER,
    narration TEXT,
    FOREIGN KEY (tour_id) REFERENCES tours(id),
    FOREIGN KEY (artwork_id) REFERENCES artworks(id)
);
```

---

## 🖼️ Image Recognition Technical Details

### Why Feature Matching (not ML)?
- **No API costs** - runs entirely on-device
- **Works offline** - perfect for museums with poor wifi
- **Fast** - sub-second recognition
- **Proven** - Google Goggles used this approach
- **Accurate enough** - for curated museum collection

### Algorithm Choice: SIFT vs ORB
- **SIFT (Scale-Invariant Feature Transform)**
  - Pro: More accurate, handles scale/rotation
  - Con: Patented (but free for non-commercial use)
  
- **ORB (Oriented FAST and Rotated BRIEF)**
  - Pro: Open-source, very fast
  - Con: Slightly less accurate
  
**Recommendation:** Start with ORB, upgrade to SIFT if needed

### Implementation Approach
```python
# Preprocessing (done once per artwork)
1. Load reference image from Met API
2. Convert to grayscale
3. Detect keypoints using ORB
4. Compute descriptors
5. Store descriptors in database

# Runtime (when user takes photo)
1. Capture image from camera
2. Detect keypoints in user's image
3. Match against database using BFMatcher/FLANN
4. Rank matches by distance
5. If top match > confidence threshold: return artwork
```

---

## 🎨 Initial Artwork Selection (Top 100 Met Highlights)

### Categories to Include:
1. **European Paintings** (30 artworks)
   - Van Gogh, Vermeer, Rembrandt, etc.
   
2. **American Art** (15 artworks)
   - Washington Crossing the Delaware
   - John Singer Sargent portraits
   
3. **Egyptian Art** (15 artworks)
   - Temple of Dendur
   - Mummies and sarcophagi
   
4. **Greek & Roman** (10 artworks)
   - Statues, pottery
   
5. **Asian Art** (10 artworks)
   - Chinese ceramics, Japanese screens
   
6. **Medieval/Arms & Armor** (10 artworks)
   - Knights' armor, swords
   
7. **Musical Instruments** (5 artworks)
   - Historic instruments
   
8. **Modern/Contemporary** (5 artworks)
   - Picasso, Pollock

### Selection Criteria:
- Most photographed/viewed artworks
- Easily recognizable (distinct features)
- Distributed across museum wings
- Cultural significance

---

## 🔊 Audio Narration Strategy

### Options:

**Option 1: Text-to-Speech (Recommended for MVP)**
- Use free TTS engines:
  - Google TTS (free tier)
  - Festival/eSpeak (open-source, offline)
  - Pre-generate all audio files (one-time cost)
- Pros: Scalable, easy to update
- Cons: Less engaging than human voice

**Option 2: Human Narration (Future)**
- Record professional or volunteer narrations
- More engaging, better for tours
- Could be premium feature

### Audio Script Format (30-60 seconds per artwork):
```
Hook (5 sec): "You're looking at one of the most famous paintings in the world."
Context (15 sec): "Created by Vincent van Gogh in 1889..."
Key Feature (15 sec): "Notice the swirling brushstrokes..."
Fun Fact (10 sec): "Van Gogh actually painted this from memory..."
Call to Action (5 sec): "Look closer at the cypress tree on the left..."
```

---

## 🚀 Development Roadmap

### Phase 1: MVP (4-6 weeks)
**Week 1-2: Data Pipeline**
- [ ] Pull 100 artworks from Met API
- [ ] Download images
- [ ] Generate feature descriptors
- [ ] Create SQLite database
- [ ] Write basic descriptions (from Met metadata)

**Week 3-4: Image Recognition**
- [ ] Build feature matching engine
- [ ] Test accuracy with sample photos
- [ ] Optimize matching speed
- [ ] Handle edge cases (partial views, lighting)

**Week 5-6: Mobile App**
- [ ] Basic Flutter app with camera
- [ ] Database integration
- [ ] Recognition display UI
- [ ] Simple artwork detail page
- [ ] Testing with real museum photos

### Phase 2: Polish (2-3 weeks)
- [ ] Generate TTS audio for all artworks
- [ ] Improve UI/UX
- [ ] Add search/browse functionality
- [ ] Create 2-3 themed tours
- [ ] Beta testing

### Phase 3: Launch (1 week)
- [ ] App store submission
- [ ] Marketing website
- [ ] Social media presence
- [ ] Reach out to Met for partnership

### Phase 4: Expansion (Ongoing)
- [ ] Add more artworks (up to 500)
- [ ] Support for other museums
- [ ] AR features (overlay info on camera)
- [ ] User-generated content (reviews, photos)
- [ ] Premium features (human narration, private tours)

---

## 💰 Monetization Strategy (Future)

### Free Features:
- Recognition of 100 artworks
- Basic text descriptions
- TTS audio
- Simple tours

### Premium ($3.99/month or $29.99/year):
- All 500+ artworks
- Professional audio narrations
- Exclusive curator insights
- AR features
- Download content for offline
- Ad-free experience

### Alternative Revenue:
- Museum partnerships (white-label app)
- Tourism board sponsorships
- In-app purchases (individual museum packs)
- Educational licenses (schools)

---

## 🛠️ Technology Stack Summary

### Mobile App
- **Framework:** Flutter
- **Language:** Dart
- **Camera:** camera plugin
- **Database:** sqflite
- **Audio:** audioplayers plugin
- **HTTP:** http package
- **Image Processing:** flutter_opencv or native integration

### Backend/Data Pipeline (Python)
- **API calls:** requests
- **Image processing:** OpenCV, Pillow
- **Feature extraction:** opencv-python
- **Database:** sqlite3
- **TTS:** gTTS or pyttsx3
- **Data processing:** pandas

### Deployment
- **App stores:** Apple App Store, Google Play
- **Website:** GitHub Pages or Vercel (static)
- **Analytics:** Firebase Analytics (free tier)

---

## 📱 User Experience Flow

### First Launch
1. Welcome screen with quick tutorial
2. "Point your camera at any artwork in The Met"
3. Show sample recognition demo
4. Browse featured artworks

### Recognition Flow
1. User opens camera view
2. Frame highlights when artwork detected
3. Tap to confirm or auto-recognize
4. Card slides up with artwork info
5. Auto-play audio narration (optional)
6. Buttons: "Read more", "Add to favorites", "Share"

### Browse Mode
1. Grid view of all artworks
2. Filter by: Department, Artist, Period
3. Search by name
4. Sort by: Popularity, Alphabetical, Date

### Tour Mode
1. Select a tour (e.g., "Highlights in 30 minutes")
2. Map showing route through galleries
3. Navigation to each artwork
4. Audio guides through entire tour

---

## 🎯 Success Metrics

### Technical KPIs
- Recognition accuracy > 90%
- Recognition speed < 2 seconds
- App size < 50MB (initial download)
- Offline functionality 100%

### User KPIs
- Downloads: 10k in first 3 months
- Daily active users: 1k
- Average session time: 15 minutes
- Artworks scanned per session: 5+

---

## 🚧 Challenges & Solutions

### Challenge 1: Image Recognition Accuracy
**Problem:** User photos vary (angle, lighting, distance, partial views)
**Solutions:**
- Train on augmented dataset (different angles)
- Multi-scale feature matching
- Confidence threshold + fallback to manual search
- User feedback loop to improve

### Challenge 2: Database Size
**Problem:** 100 artworks with images + features = large app
**Solutions:**
- Compress images aggressively
- Download full database on first launch (wifi only)
- Incremental updates
- Lazy loading of audio files

### Challenge 3: Copyright/Permissions
**Problem:** Using museum images
**Solutions:**
- Met has open access policy (most artworks are public domain)
- Credit properly in app
- Reach out for official partnership
- Avoid selling artworks themselves

### Challenge 4: Competition
**Problem:** Google Lens, museum's own apps
**Solutions:**
- Focus on experience, not just recognition
- Better curated content
- Engaging narrations
- Gamification (collect artworks, tours)
- Community features

---

## 🔐 Legal & Compliance

### Image Rights
- The Met's open access policy covers 375k+ artworks
- Always attribute: "Image courtesy of The Metropolitan Museum of Art"
- Link to Met's collection page

### Privacy
- No user tracking beyond anonymous analytics
- No personal data collection
- Camera only used for recognition (no cloud upload)
- GDPR/CCPA compliant

### Terms of Service
- Educational use only
- Not for commercial reproduction
- User-generated content moderation

---

## 📚 Resources & References

### APIs
- The Met API: https://metmuseum.github.io/
- Met Open Access: https://www.metmuseum.org/about-the-met/policies-and-documents/open-access

### Technical Documentation
- OpenCV Tutorials: https://docs.opencv.org/
- Flutter Documentation: https://flutter.dev/docs
- SIFT/ORB Papers: Available on arXiv

### Inspiration
- Google Arts & Culture
- Smartify app
- Bloomberg Connects

---

**Next Steps:** Let's start building the data pipeline!
