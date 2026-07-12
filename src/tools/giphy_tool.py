import os
import requests
import urllib.parse
from datetime import datetime

def download_giphy_video(query, output_dir="output"):
    """
    Searches for a GIF on Giphy using the given query and downloads the MP4 version.
    Returns the absolute path to the downloaded MP4 video.
    """
    api_key = os.getenv("GIPHY_API_KEY")
    if not api_key:
        print("⚠️ GIPHY_API_KEY is not set. Falling back to placeholder.")
        return None

    encoded_query = urllib.parse.quote(query)
    
    # Request Giphy search
    url = f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={encoded_query}&limit=5&rating=g"
    
    print(f"🎬 Searching Giphy for: '{query}'...")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("data"):
            print("⚠️ No Giphy results found for the query.")
            return None
            
        # Get the first result's original MP4 URL
        first_result = data["data"][0]
        # Some gifs might not have mp4, but 'original' usually does.
        # Let's safely extract it.
        try:
            video_url = first_result["images"]["original"]["mp4"]
        except KeyError:
            print("⚠️ Selected Giphy result does not have an MP4 version.")
            return None
        
        # Download the video
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"giphy_video_{timestamp}.mp4"
        filepath = os.path.abspath(os.path.join(output_dir, filename))
        
        vid_data = requests.get(video_url, timeout=15).content
        with open(filepath, 'wb') as handler:
            handler.write(vid_data)
            
        print(f"✅ Downloaded Giphy MP4 to {filepath}")
        return filepath
        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Giphy API Error: {e}")
        return None
