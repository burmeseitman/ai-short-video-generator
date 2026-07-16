import os
import sys
import re
from datetime import datetime

# Inject Homebrew dynamic library path for Pillow to load libraqm/libharfbuzz
# This enables perfect complex text shaping and rendering.
os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = "/opt/homebrew/lib:" + os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")

import yaml
from src.crew import run_shortform_crew
from src.tools.voice_tool import generate_scene_voiceovers
from src.planner import pick_topic_for_today

def parse_agent_output(output_text):
    """
    Parses the TITLE and SCENES list (SCRIPT, VISUAL_PROMPT, SEARCH_QUERY) from the agent output text.
    Handles console borders, markdown bold markers, JSON formats, and numbered lists.
    Strips out SSML tags from the script text before translating/processing.
    """
    import json
    # Clean up CrewAI console borders
    lines = []
    for line in output_text.split("\n"):
        line = line.strip()
        if line.startswith("│"):
            line = line[1:]
        if line.endswith("│"):
            line = line[:-1]
        line = line.strip()
        if any(line.startswith(x) for x in ["├──", "╰──", "╭──", "└──", "┌──", "───", "──"]):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)

    # Remove bold markers around keys and in general to simplify parsing
    cleaned = cleaned.replace("**", "")

    # Extract Title
    title = "New Short Video"
    title_match = re.search(r"TITLE:\s*(.*)", cleaned, re.IGNORECASE)
    if not title_match:
        # Search JSON title key
        title_match = re.search(r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"', cleaned, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).split("\n")[0].strip().strip("[]\"'* -")

    scenes = []

    # ── Option 1: Parse JSON block regex ───────────────────────────────────────
    # We find all scene objects like { "SCRIPT": ..., "SEARCH_QUERY": ... }
    json_blocks = re.findall(r'\{([^}]+)\}', cleaned, re.DOTALL)
    for block in json_blocks:
        if "script" in block.lower():
            # Match double-quoted strings supporting escaped quotes inside
            script_match = re.search(r'"script"\s*:\s*"((?:[^"\\]|\\.)*)"', block, re.IGNORECASE | re.DOTALL)
            query_match = re.search(r'"search_query"\s*:\s*"((?:[^"\\]|\\.)*)"', block, re.IGNORECASE | re.DOTALL)
            
            if script_match:
                script = script_match.group(1).replace('\\"', '"').replace('\\n', ' ').strip()
                # Remove SSML tags to keep text clean for translation and gTTS
                script = re.sub(r'<[^>]+>', '', script)
                
                query = query_match.group(1).replace('\\"', '"').replace('\\n', ' ').strip() if query_match else "technology"
                scenes.append({
                    "SCRIPT": script,
                    "VISUAL_PROMPT": query,
                    "SEARCH_QUERY": query
                })
                
    if scenes:
        print(f"  ✅ Parser: Successfully extracted {len(scenes)} scenes from JSON template.")
        return title, scenes

    # ── Option 2: Parse standard layout (splitting by scene numbers/bullets) ────
    scene_blocks = re.split(r"(?:\n|^)(?:-\s*|\d+\.\s*|Scene\s*\d+\s*:)", cleaned, flags=re.IGNORECASE)
    # Skip intro block if it does not contain keywords
    if scene_blocks and not any(k in scene_blocks[0].lower() for k in ["script", "timestamp", "time-stamp"]):
        scene_blocks = scene_blocks[1:]
        
    for idx, block in enumerate(scene_blocks):
        if not block.strip():
            continue
            
        script_match = re.search(r"SCRIPT:\s*(.*?)(?=\s*(?:SEARCH_QUERY|ASSET_TYPE|TIME[-_]?STAMP|VISUAL_PROMPT)|$)", block, re.DOTALL | re.IGNORECASE)
        script = script_match.group(1).strip() if script_match else block.strip()
        script = script.replace("\n", " ")
        script = re.sub(r"\s+", " ", script).strip().strip("[]\"'* -")
        script = re.sub(r'<[^>]+>', '', script)  # Remove SSML tags
        
        query_match = re.search(r"SEARCH_QUERY:\s*(.*?)(?=\s*(?:TIME[-_]?STAMP|ASSET_TYPE|SCRIPT)|$)", block, re.DOTALL | re.IGNORECASE)
        query = query_match.group(1).strip() if query_match else "abstract technology"
        query = query.replace("\n", " ")
        query = re.sub(r"\s+", " ", query).strip().strip("[]\"'* -")
        
        scenes.append({
            "SCRIPT": script,
            "VISUAL_PROMPT": query,
            "SEARCH_QUERY": query
        })

    # ── Last Resort Fallback ───────────────────────────────────────────────────
    if not scenes:
        print("  ⚠️  Parser warning: Layout parser failed. Using fallback mode.")
        scenes.append({
            "SCRIPT": re.sub(r'<[^>]+>', '', output_text),
            "VISUAL_PROMPT": "A high-tech background loop, abstract data visualization",
            "SEARCH_QUERY": "abstract technology"
        })

    return title, scenes

def main():
    today = datetime.now()

    # ── Topic selection ────────────────────────────────────────────────────────
    if len(sys.argv) > 1:
        # Manual override — highest priority, skip planner entirely
        video_topic = sys.argv[1]
    else:
        # Auto-plan mode: read today's schedule and let LLM pick a topic
        try:
            plan = pick_topic_for_today()
            print(f"\n📅 Today's Plan  : {plan['day']} — Niche: {plan['niche']}")
            print(f"📂 Category      : {plan['category']}")
            print(f"🎯 Style         : {plan['style']}")
            print(f"🤖 Suggested Topic: '{plan['topic']}'")
            
            # Default to suggested topic first in case input fails (non-interactive)
            video_topic = plan['topic']
            
            user_input = input("\nPress Enter to use this topic, or type your own: ").strip()
            if user_input:
                video_topic = user_input
        except (EOFError, IOError):
            # Non-interactive fallback — reuse the already suggested topic
            pass
        except Exception as e:
            print(f"⚠️  Planner failed ({e}). Please enter topic manually.")
            video_topic = input("Enter video topic: ").strip() or "AI Tech Trends"


    print(f"🎬 Active Topic Selected: '{video_topic}'")
    
    from src.planner import save_topic_to_history
    save_topic_to_history(video_topic)
    print(f"✨ Selected Topic: {video_topic}")

    def make_run_dir(topic):
        safe = re.sub(r'[^a-zA-Z0-9]+', '_', topic.lower()).strip('_')[:50]
        name = f"{today.strftime('%Y%m%d')}_{safe}"
        path = f"runs/{name}"
        os.makedirs(path, exist_ok=True)
        return path

    run_dir = make_run_dir(video_topic)
    print(f"📂 Run folder: {run_dir}")

    
    print(f"🚀 [1/5] Starting CrewAI Automation (+ Critic Review) for Topic: '{video_topic}'")
    crew_output = run_shortform_crew(video_topic)
    
    # Parse structured scene edits
    title, scenes = parse_agent_output(str(crew_output))
    print(f"\n✨ Generated Title: {title}")
    print(f"📋 Total Scenes Extracted: {len(scenes)}")

    # Translate English script to Myanmar if not already translated (agent-level Burmese bypass)
    def is_burmese(text):
        return bool(re.search(r'[\u1000-\u109f]', text))

    translated_count = 0
    skipped_count = 0
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='en', target='my')
        print("\n🌐 [2/5] Translating English script to Myanmar (Free)...")
        for scene in scenes:
            text = scene.get("SCRIPT", "")
            if text:
                if is_burmese(text):
                    skipped_count += 1
                else:
                    my_text = translator.translate(text)
                    scene["SCRIPT"] = my_text
                    translated_count += 1
                    print(f"  En: {text[:40]}... -> My: {my_text[:40]}...")
        if skipped_count > 0:
            print(f"  ℹ️  Detected native Burmese script: Skipped translation for {skipped_count} scenes.")
    except Exception as e:
        print(f"⚠️ Translation failed: {e}. Subtitles may be in English.")

    # 3. Generate Voiceover for each scene
    print("\n🔊 [3/5] Generating Scene-Level Myanmar Voiceovers...")
    voice_files = generate_scene_voiceovers(scenes, run_dir=run_dir)
    
    # 4. Generate Asset for each scene
    print("\n📹 [4/5] Compiling Scene Assets...")

    # Determine asset sources dynamically based on Director/Critic storyboard ASSET_TYPE
    scene_sources = []
    for scene in scenes:
        asset_type = scene.get("ASSET_TYPE", "VIDEO")
        if asset_type == "PHOTO":
            scene_sources.append("unsplash")
        elif asset_type == "GIF":
            scene_sources.append("giphy")
        else:
            scene_sources.append("pexels")

    pexels_api_key = os.getenv("PEXELS_API_KEY")
    from src.tools.pexels_tool import download_pexels_video
    from src.tools.unsplash_tool import download_unsplash_photo
    from src.tools.giphy_tool import download_giphy_video

    def generate_mock_image(output_path):
        # Ultimate fallback if APIs fail (creates a basic image so Remotion doesn't crash)
        try:
            from PIL import Image
            img = Image.new('RGB', (832, 480), color = (73, 109, 137))
            img.save(output_path)
            return output_path
        except:
            return None

    for idx, scene in enumerate(scenes):
        prompt = scene.get("VISUAL_PROMPT", "abstract technology")
        search_query = scene.get("SEARCH_QUERY", prompt[:30])
        source = scene_sources[idx]

        video_file = None

        if source == "unsplash":
            print(f"  🎬 Scene {idx + 1} [UNSPLASH IMAGE]: Searching photo: '{search_query}'...")
            local_path, photo_url = download_unsplash_photo(search_query, output_dir=run_dir)
            if local_path:
                video_file = local_path
                scene["CREDIT_TEXT"] = "Photo by Unsplash"
            else:
                print("    ⚠️ Unsplash failed. Falling back to Pexels...")
                source = "pexels"

        elif source == "giphy":
            print(f"  🎬 Scene {idx + 1} [GIPHY GIF]: Searching Giphy: '{search_query}'...")
            video_file = download_giphy_video(search_query, output_dir=run_dir)
            if video_file:
                scene["CREDIT_TEXT"] = "GIF via Giphy"
            else:
                print("    ⚠️ Giphy failed. Falling back to Pexels...")
                source = "pexels"

        if source == "pexels" or not video_file:
            print(f"  🎬 Scene {idx + 1} [PEXELS VIDEO]: Searching stock footage: '{search_query}'...")
            output_file = f"{run_dir}/pexels_scene_{idx}.mp4"
            if pexels_api_key and pexels_api_key != "YOUR_PEXELS_API_KEY":
                video_file = download_pexels_video(search_query, pexels_api_key, output_file)
                if video_file:
                    scene["CREDIT_TEXT"] = "Footage by Pexels"
            
            # Absolute worst-case fallback
            if not video_file:
                print("    ⚠️ Pexels video failed. Generating Mock fallback image...")
                video_file = generate_mock_image(f"{run_dir}/mock_scene_{idx}.jpg")

        scene["VIDEO_PATH"] = video_file


    # 3. Cinematic Post-Processing with MoviePy
    print("\n🎞️ [5/5] MoviePy Cinematic Post-Processing (Transitions, Ducking, Grading)...")
    import shutil
    from src.tools.video_composer import compose_final_video

    # Try to find a BGM file
    def get_bgm(output_path):
        # Check for user-provided BGM in assets folder
        assets_bgm_dir = "assets/bgm"
        if os.path.isdir(assets_bgm_dir):
            import random
            bgm_files = [f for f in os.listdir(assets_bgm_dir) if f.endswith(('.mp3', '.wav', '.m4a'))]
            if bgm_files:
                chosen = os.path.join(assets_bgm_dir, random.choice(bgm_files))
                shutil.copy(chosen, output_path)
                print(f"  🎵 BGM selected: {os.path.basename(chosen)}")
                return output_path

        # Fallback: check for existing BGM from a previous run
        for root, dirs, files in os.walk("runs"):
            for f in files:
                if f == "bgm.mp3":
                    src = os.path.join(root, f)
                    shutil.copy(src, output_path)
                    print(f"  🎵 BGM fallback: {src}")
                    return output_path
        
        print("  ⚠️ No BGM found. Video will have voiceover only.")
        return None

    bgm_path = get_bgm(f"{run_dir}/bgm.mp3")

    final_video_path = compose_final_video(
        scenes=scenes,
        voice_files=voice_files,
        run_dir=run_dir,
        title=title,
        bgm_path=bgm_path
    )

    print(f"\n🎉 Pipeline complete! Final video: {final_video_path}")

if __name__ == "__main__":
    main()