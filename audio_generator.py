"""
Audio Narration Generator for Museum Guide App
Uses free Text-to-Speech to create audio files
"""

import sqlite3
from gtts import gTTS
from pathlib import Path
import time

class AudioNarrationGenerator:
    """
    Generates audio narrations for artworks using Google Text-to-Speech
    """
    
    def __init__(self, db_path: str = "museum_guide.db", audio_dir: str = "audio"):
        self.db_path = db_path
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(db_path)
    
    def generate_narration_script(self, artwork: dict) -> str:
        """
        Create engaging narration script for an artwork
        Format: Hook → Context → Key Feature → Fun Fact → Call to Action
        """
        title = artwork['title']
        artist = artwork.get('artist_display_name', 'Unknown artist')
        date = artwork.get('date', 'Unknown date')
        medium = artwork.get('medium', '')
        department = artwork.get('department', '')
        
        # Hook (5 seconds)
        hooks = [
            f"You're looking at {title}.",
            f"This is one of the museum's treasures.",
            f"Meet {title}.",
        ]
        hook = hooks[0]
        
        # Context (15 seconds)
        context = f"Created by {artist} "
        if date and date != 'Unknown date':
            context += f"in {date}, "
        
        if medium:
            medium_clean = medium.lower()
            if 'oil' in medium_clean:
                context += "this oil painting "
            elif 'marble' in medium_clean:
                context += "this marble sculpture "
            elif 'bronze' in medium_clean:
                context += "this bronze work "
            elif 'ceramic' in medium_clean:
                context += "this ceramic piece "
            else:
                context += "this artwork "
        
        context += "is a masterpiece of "
        
        # Add department context
        if 'European' in department:
            context += "European art."
        elif 'American' in department:
            context += "American art."
        elif 'Egyptian' in department:
            context += "ancient Egyptian culture."
        elif 'Greek' in department or 'Roman' in department:
            context += "classical antiquity."
        elif 'Asian' in department:
            context += "Asian artistic tradition."
        else:
            context += f"the {department}."
        
        # Key Feature (15 seconds)
        features = self._generate_key_features(artwork)
        
        # Fun Fact (10 seconds)
        fun_fact = self._generate_fun_fact(artwork)
        
        # Call to Action (5 seconds)
        cta = "Take a closer look and see what details you can discover."
        
        # Combine all parts
        full_script = f"{hook} {context} {features} {fun_fact} {cta}"
        
        return full_script
    
    def _generate_key_features(self, artwork: dict) -> str:
        """Generate description of key visual features"""
        medium = artwork.get('medium', '').lower()
        department = artwork.get('department', '')
        
        if 'painting' in medium or 'European Paintings' in department:
            return "Notice the masterful use of color and brushwork. The composition draws your eye across the canvas."
        elif 'sculpture' in medium or 'statue' in artwork.get('title', '').lower():
            return "Observe the incredible detail in the carved features and the lifelike proportions."
        elif 'Egyptian' in department:
            return "The hieroglyphics and symbolic imagery tell stories from thousands of years ago."
        elif 'ceramic' in medium or 'pottery' in medium:
            return "The intricate patterns and glazing techniques showcase exceptional craftsmanship."
        elif 'armor' in medium or 'Arms and Armor' in department:
            return "Notice the engineering and artistry combined in this protective equipment."
        else:
            return "Pay attention to the materials, technique, and symbolic elements used by the artist."
    
    def _generate_fun_fact(self, artwork: dict) -> str:
        """Generate an interesting fun fact"""
        artist = artwork.get('artist_display_name', '')
        date = artwork.get('date', '')
        department = artwork.get('department', '')
        
        # Artist-specific facts
        if 'Van Gogh' in artist:
            return "Van Gogh created hundreds of paintings in just the last two years of his life."
        elif 'Vermeer' in artist:
            return "Vermeer painted fewer than 40 works in his entire lifetime, making each one extremely precious."
        elif 'Rembrandt' in artist:
            return "Rembrandt often included himself in his paintings as a hidden observer."
        
        # Department/type specific facts
        if 'Egyptian' in department:
            return "This artifact has survived for thousands of years, outlasting entire civilizations."
        elif 'Arms and Armor' in department:
            return "Medieval armor like this could weigh up to 50 pounds, yet knights could move surprisingly well in it."
        elif 'Greek' in department or 'Roman' in department:
            return "Many classical statues were originally painted in bright colors, not the white marble we see today."
        
        # Date-based facts
        try:
            year = int(''.join(filter(str.isdigit, date))[:4])
            if year < 1500:
                return f"This artwork is over {2024 - year} years old."
            elif year < 1800:
                return f"This was created {2024 - year} years ago, before photography existed."
        except:
            pass
        
        return "Artworks like this connect us to the creativity and vision of people from another time."
    
    def generate_audio_file(self, artwork_id: int, script: str, lang: str = 'en') -> str:
        """
        Generate audio file from script using gTTS
        Returns path to generated audio file
        """
        filename = f"artwork_{artwork_id}.mp3"
        filepath = self.audio_dir / filename
        
        try:
            # Generate speech
            tts = gTTS(text=script, lang=lang, slow=False)
            tts.save(str(filepath))
            
            return str(filepath)
        except Exception as e:
            print(f"Error generating audio: {e}")
            return None
    
    def generate_all_narrations(self):
        """Generate audio narrations for all artworks in database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, met_object_id, title, artist_display_name, 
                   date, medium, department
            FROM artworks
        """)
        
        artworks = cursor.fetchall()
        total = len(artworks)
        
        print(f"\n🎙️  Generating audio narrations for {total} artworks...")
        print("=" * 60)
        
        success_count = 0
        
        for i, row in enumerate(artworks, 1):
            artwork_dict = {
                'id': row[0],
                'met_object_id': row[1],
                'title': row[2],
                'artist_display_name': row[3],
                'date': row[4],
                'medium': row[5],
                'department': row[6]
            }
            
            title = artwork_dict['title'][:50]
            print(f"[{i}/{total}] {title}...", end=" ")
            
            # Generate script
            script = self.generate_narration_script(artwork_dict)
            
            # Generate audio
            audio_path = self.generate_audio_file(artwork_dict['id'], script)
            
            if audio_path:
                # Update database with audio file path
                cursor.execute("""
                    UPDATE artworks 
                    SET audio_file_path = ?
                    WHERE id = ?
                """, (audio_path, artwork_dict['id']))
                self.conn.commit()
                
                print(f"✓ ({len(script)} chars)")
                success_count += 1
            else:
                print("✗ Failed")
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        print("=" * 60)
        print(f"✓ Generated {success_count}/{total} audio files")
        print(f"📁 Audio files saved to: {self.audio_dir.absolute()}")
    
    def preview_narration(self, artwork_id: int):
        """Preview the narration script for an artwork"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, met_object_id, title, artist_display_name, 
                   date, medium, department
            FROM artworks
            WHERE id = ?
        """, (artwork_id,))
        
        row = cursor.fetchone()
        if not row:
            print(f"Artwork {artwork_id} not found")
            return
        
        artwork_dict = {
            'id': row[0],
            'met_object_id': row[1],
            'title': row[2],
            'artist_display_name': row[3],
            'date': row[4],
            'medium': row[5],
            'department': row[6]
        }
        
        script = self.generate_narration_script(artwork_dict)
        
        print(f"\n📝 Narration Preview for: {artwork_dict['title']}")
        print("=" * 60)
        print(script)
        print("=" * 60)
        print(f"Length: {len(script)} characters")
        print(f"Estimated duration: {len(script) // 15} seconds")


def main():
    """Main function to generate all audio narrations"""
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║   Audio Narration Generator                         ║
    ║   Using Google Text-to-Speech (Free)                ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    generator = AudioNarrationGenerator()
    
    # Preview one narration
    print("\n📋 Preview of narration format:")
    generator.preview_narration(1)
    
    # Ask for confirmation
    print("\n" + "=" * 60)
    response = input("\nGenerate audio for all artworks? (y/n): ")
    
    if response.lower() == 'y':
        generator.generate_all_narrations()
        print("\n✓ Complete! Audio files ready for mobile app.")
    else:
        print("\nCancelled. No audio files generated.")


if __name__ == "__main__":
    main()
