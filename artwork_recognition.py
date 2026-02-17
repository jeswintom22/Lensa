"""
Image Recognition Engine for Museum Guide App
Uses ORB (Oriented FAST and Rotated BRIEF) for feature matching
"""

import cv2
import numpy as np
import sqlite3
import pickle
from pathlib import Path
from typing import List, Tuple, Optional
import urllib.request
from io import BytesIO
from PIL import Image

class ArtworkRecognitionEngine:
    """
    Handles image recognition for artworks using feature matching
    No ML/AI tokens needed - runs completely locally!
    """
    
    def __init__(self, db_path: str = "museum_guide.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Initialize ORB detector
        # ORB is free, fast, and works well for artwork recognition
        self.orb = cv2.ORB_create(
            nfeatures=2000,        # Number of features to detect
            scaleFactor=1.2,       # Pyramid decimation ratio
            nlevels=8,             # Number of pyramid levels
            edgeThreshold=31,      # Border size
            firstLevel=0,
            WTA_K=2,
            scoreType=cv2.ORB_HARRIS_SCORE,
            patchSize=31
        )
        
        # Create matcher for feature matching
        # Using BFMatcher (Brute Force) - simple and effective
        self.matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        
        print("✓ Recognition engine initialized")
    
    def download_image(self, url: str) -> Optional[np.ndarray]:
        """Download image from URL and convert to OpenCV format"""
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                image_data = response.read()
                image = Image.open(BytesIO(image_data))
                # Convert to OpenCV format (BGR)
                return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load image from file"""
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error loading image: {image_path}")
        return img
    
    def extract_features(self, image: np.ndarray) -> Tuple[List, np.ndarray]:
        """
        Extract ORB features from an image
        Returns keypoints and descriptors
        """
        # Convert to grayscale (feature detection works on grayscale)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect keypoints and compute descriptors
        keypoints, descriptors = self.orb.detectAndCompute(gray, None)
        
        return keypoints, descriptors
    
    def preprocess_reference_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess reference images for better feature extraction
        """
        # Resize if too large (for faster processing)
        max_dimension = 1200
        height, width = image.shape[:2]
        
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))
        
        # Enhance contrast (helps with museum lighting variations)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def build_reference_database(self):
        """
        Process all artworks in database and extract features
        Run this once after adding new artworks
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, met_object_id, title, image_url 
            FROM artworks 
            WHERE image_url IS NOT NULL AND image_url != ''
        """)
        
        artworks = cursor.fetchall()
        print(f"\n🔨 Building reference database for {len(artworks)} artworks...")
        
        success_count = 0
        
        for artwork_id, met_id, title, image_url in artworks:
            print(f"  Processing: {title[:50]}...", end=" ")
            
            # Download image
            image = self.download_image(image_url)
            if image is None:
                print("✗ Download failed")
                continue
            
            # Preprocess
            image = self.preprocess_reference_image(image)
            
            # Extract features
            keypoints, descriptors = self.extract_features(image)
            
            if descriptors is None or len(descriptors) == 0:
                print("✗ No features found")
                continue
            
            # Save to database
            descriptor_blob = pickle.dumps(descriptors)
            
            cursor.execute("""
                INSERT OR REPLACE INTO artwork_features 
                (artwork_id, feature_descriptor, feature_type)
                VALUES (?, ?, ?)
            """, (artwork_id, descriptor_blob, 'orb'))
            
            self.conn.commit()
            success_count += 1
            print(f"✓ ({len(keypoints)} features)")
        
        print(f"\n✓ Successfully processed {success_count}/{len(artworks)} artworks")
    
    def recognize_artwork(self, 
                         query_image: np.ndarray, 
                         min_matches: int = 30,
                         match_threshold: float = 0.7) -> Optional[Tuple[int, float, int]]:
        """
        Recognize an artwork from a user's photo
        
        Args:
            query_image: User's photo (numpy array)
            min_matches: Minimum number of good matches required
            match_threshold: Ratio test threshold (lower = stricter)
        
        Returns:
            (artwork_id, confidence_score, num_matches) or None
        """
        # Extract features from query image
        query_kp, query_desc = self.extract_features(query_image)
        
        if query_desc is None or len(query_desc) == 0:
            print("No features detected in query image")
            return None
        
        print(f"Detected {len(query_kp)} features in query image")
        
        # Load all reference descriptors from database
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT af.artwork_id, af.feature_descriptor, a.title
            FROM artwork_features af
            JOIN artworks a ON af.artwork_id = a.id
        """)
        
        best_match = None
        best_score = 0
        best_matches_count = 0
        
        for artwork_id, descriptor_blob, title in cursor.fetchall():
            # Deserialize descriptors
            ref_desc = pickle.loads(descriptor_blob)
            
            # Match features using k-nearest neighbors (k=2)
            try:
                matches = self.matcher.knnMatch(query_desc, ref_desc, k=2)
            except cv2.error:
                continue
            
            # Apply Lowe's ratio test to filter good matches
            good_matches = []
            for match_pair in matches:
                if len(match_pair) == 2:
                    m, n = match_pair
                    if m.distance < match_threshold * n.distance:
                        good_matches.append(m)
            
            num_good_matches = len(good_matches)
            
            # Calculate confidence score
            if num_good_matches >= min_matches:
                # Score based on number of matches and average distance
                avg_distance = sum(m.distance for m in good_matches) / num_good_matches
                confidence = num_good_matches / (1 + avg_distance / 100)
                
                if confidence > best_score:
                    best_score = confidence
                    best_match = artwork_id
                    best_matches_count = num_good_matches
                    print(f"  Match: {title[:40]} - {num_good_matches} matches, score: {confidence:.2f}")
        
        if best_match:
            return (best_match, best_score, best_matches_count)
        
        return None
    
    def get_artwork_details(self, artwork_id: int) -> dict:
        """Fetch full details for a recognized artwork"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT met_object_id, title, artist_display_name, date, 
                   medium, department, description, image_url
            FROM artworks
            WHERE id = ?
        """, (artwork_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'id': artwork_id,
                'met_id': row[0],
                'title': row[1],
                'artist': row[2],
                'date': row[3],
                'medium': row[4],
                'department': row[5],
                'description': row[6],
                'image_url': row[7]
            }
        return None
    
    def test_recognition(self, test_image_path: str):
        """
        Test recognition on a sample image
        Useful for debugging and validation
        """
        print(f"\n🧪 Testing recognition on: {test_image_path}")
        
        # Load test image
        test_image = self.load_image(test_image_path)
        if test_image is None:
            return
        
        # Try to recognize
        result = self.recognize_artwork(test_image)
        
        if result:
            artwork_id, confidence, num_matches = result
            details = self.get_artwork_details(artwork_id)
            
            print(f"\n✓ RECOGNIZED!")
            print(f"  Title: {details['title']}")
            print(f"  Artist: {details['artist']}")
            print(f"  Confidence: {confidence:.2f}")
            print(f"  Matches: {num_matches}")
        else:
            print("\n✗ Not recognized")
            print("  Try:")
            print("  - Taking photo from different angle")
            print("  - Better lighting")
            print("  - Getting closer to artwork")


def demo_recognition():
    """
    Demo showing how the recognition engine works
    """
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   Artwork Recognition Engine Demo                   ║
    ║   Using ORB Feature Matching                        ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    engine = ArtworkRecognitionEngine()
    
    print("\n📊 Current Status:")
    cursor = engine.conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM artworks")
    artwork_count = cursor.fetchone()[0]
    print(f"  Artworks in database: {artwork_count}")
    
    cursor.execute("SELECT COUNT(*) FROM artwork_features")
    features_count = cursor.fetchone()[0]
    print(f"  Artworks with features: {features_count}")
    
    if features_count == 0:
        print("\n⚠️  No features found!")
        print("   Run: engine.build_reference_database()")
        print("   This will process all artworks and extract features")
    
    print("\n💡 How it works:")
    print("  1. User takes photo of artwork")
    print("  2. Extract ORB features from photo")
    print("  3. Match against database of reference features")
    print("  4. Return best match with confidence score")
    
    print("\n⚡ Advantages:")
    print("  ✓ No API costs - runs locally")
    print("  ✓ Works offline")
    print("  ✓ Fast (<2 seconds)")
    print("  ✓ Privacy-friendly (no cloud uploads)")
    print("  ✓ Handles different angles/lighting")


if __name__ == "__main__":
    demo_recognition()
    
    # Example usage:
    # engine = ArtworkRecognitionEngine()
    # 
    # # Build reference database (run once)
    # engine.build_reference_database()
    # 
    # # Test recognition
    # engine.test_recognition("path/to/test/photo.jpg")
