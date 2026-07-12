import os
import requests
import urllib.parse
from datetime import datetime

def download_unsplash_photo(query, output_dir="output"):
    """
    Searches for a portrait photo on Unsplash using the given query and downloads it.
    Returns the absolute path to the downloaded photo.
    """
    api_key = os.getenv("UNSPLASH_API_KEY")
    if not api_key:
        print("⚠️ UNSPLASH_API_KEY is not set. Falling back to placeholder.")
        return None, None

    encoded_query = urllib.parse.quote(query)
    
    # Request high quality portrait photo
    url = f"https://api.unsplash.com/search/photos?query={encoded_query}&client_id={api_key}&orientation=portrait&per_page=5"
    
    print(f"📷 Searching Unsplash for photo: '{query}'...")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("results"):
            print("⚠️ No Unsplash photos found for the query.")
            return None, None
            
        # Get the first result's regular URL
        first_result = data["results"][0]
        photo_url = first_result["urls"]["regular"]
        
        # Download the photo
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"unsplash_photo_{timestamp}.jpg"
        filepath = os.path.abspath(os.path.join(output_dir, filename))
        
        img_data = requests.get(photo_url, timeout=15).content
        with open(filepath, 'wb') as handler:
            handler.write(img_data)
            
        print(f"✅ Downloaded Unsplash photo to {filepath}")
        return filepath, photo_url
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Unsplash API Error: {e}")
        return None, None
