import os
import requests
import re

def download_pexels_video(visual_prompt, api_key, output_path):
    """
    Search Pexels for a video matching the visual prompt keywords and download it.
    """
    if not api_key or api_key == "local" or api_key == "YOUR_PEXELS_API_KEY":
        print("    ⚠️ Pexels API key missing. Falling back to mock storyboard clip.")
        return None

    # Clean the visual prompt into search terms
    # e.g. "Cinematic shot of a programmer typing on keyboard" -> "programmer typing keyboard"
    clean_prompt = visual_prompt.lower()
    # Remove common filter words
    clean_prompt = re.sub(r'\b(cinematic|shot|of|a|an|the|with|showing|at|on|for|in|and|close-up|wide-angle|panoramic|montage)\b', '', clean_prompt)
    keywords = [w.strip() for w in re.split(r'\W+', clean_prompt) if len(w.strip()) > 2]
    
    # Use first 3 keywords for search
    search_query = " ".join(keywords[:3]) if keywords else "technology"
    print(f"    🔍 Pexels Search: query='{search_query}'...")

    headers = {"Authorization": api_key}
    url = f"https://api.pexels.com/videos/search?query={search_query}&per_page=5"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            videos = data.get("videos", [])
            if not videos:
                print(f"    ⚠️ No videos found on Pexels for query: '{search_query}'")
                return None
            
            # Select the first video and find the best mp4 file link
            video = videos[0]
            video_files = video.get("video_files", [])
            
            # Prioritize 1080p (hd) or lower to prevent Remotion memory crashes during rendering
            best_file = None
            for quality in ['hd', 'sd', 'uhd']:
                files = [f for f in video_files if f.get('file_type') == 'video/mp4' and f.get('quality') == quality]
                if files:
                    best_file = files[0]
                    break
            
            download_url = None
            if best_file:
                download_url = best_file.get("link")
                print(f"    🌟 Selected Pexels file: {best_file.get('width')}x{best_file.get('height')} ({best_file.get('quality')})")

                        
            if download_url:
                print(f"    📥 Downloading Pexels video: {download_url[:60]}...")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Stream the download
                with requests.get(download_url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(output_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                print(f"    ✅ Pexels video downloaded: {output_path}")
                return output_path
            
        else:
            print(f"    ⚠️ Pexels API returned status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"    ⚠️ Pexels video download failed: {e}")

    return None


def download_pexels_photo(visual_prompt, api_key, output_path):
    """
    Search Pexels for a photo matching the visual prompt keywords and download it.
    Returns (local_path, photo_url) tuple for Fal.ai image-to-video usage.
    """
    if not api_key or api_key == "local" or api_key == "YOUR_PEXELS_API_KEY":
        print("    ⚠️ Pexels API key missing. Cannot download reference photo.")
        return None, None

    # Clean the visual prompt into search terms
    clean_prompt = visual_prompt.lower()
    clean_prompt = re.sub(r'\b(cinematic|shot|of|a|an|the|with|showing|at|on|for|in|and|close-up|wide-angle|panoramic|montage)\b', '', clean_prompt)
    keywords = [w.strip() for w in re.split(r'\W+', clean_prompt) if len(w.strip()) > 2]

    search_query = " ".join(keywords[:3]) if keywords else "technology"
    print(f"    🔍 Pexels Photo Search: query='{search_query}'...")

    headers = {"Authorization": api_key}
    url = f"https://api.pexels.com/v1/search?query={search_query}&per_page=5&orientation=portrait"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            photos = data.get("photos", [])
            if not photos:
                print(f"    ⚠️ No photos found on Pexels for query: '{search_query}'")
                return None, None

            # Select first photo, get the highest quality source
            photo = photos[0]
            src = photo.get("src", {})
            # Prefer 'original' for highest resolution, fall back to 'large2x'
            download_url = src.get("original") or src.get("large2x") or src.get("large")
            photo_w = photo.get("width", 0)
            photo_h = photo.get("height", 0)
            print(f"    🌟 Selected Pexels photo: {photo_w}x{photo_h}")

            if download_url:
                print(f"    📥 Downloading Pexels photo: {download_url[:60]}...")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                with requests.get(download_url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(output_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)

                print(f"    ✅ Pexels photo downloaded: {output_path}")
                return output_path, download_url

        else:
            print(f"    ⚠️ Pexels API returned status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"    ⚠️ Pexels photo download failed: {e}")

    return None, None
