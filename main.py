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
    Parses the TITLE and SCENES list (SCRIPT, VISUAL_PROMPT) from the agent output text.
    """
    title = "New Short Video"
    scenes = []

    # Get TITLE
    title_match = re.search(r"TITLE:\s*(.*)", output_text, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip().strip("[]\"' ")
        title = title.replace('\u10E2', '\u1010')

    # Try to find yaml-like SCENES section
    scenes_section_match = re.search(r"SCENES:\s*(.*)", output_text, re.DOTALL | re.IGNORECASE)
    if scenes_section_match:
        scenes_block = scenes_section_match.group(1).strip()
        
        # Clean markdown wrappers if any
        scenes_block = re.sub(r"```(yaml|json)?", "", scenes_block).strip()

        try:
            parsed_scenes = yaml.safe_load(scenes_block)
            if isinstance(parsed_scenes, list):
                for s in parsed_scenes:
                    if isinstance(s, dict) and "SCRIPT" in s:
                        script = s.get("SCRIPT", "").strip()
                        prompt = s.get("VISUAL_PROMPT", s.get("KEYWORD", "technology")).strip()
                        # Clean wrapping brackets, quotes, or markdown formatting
                        script = script.strip("[]\"'").strip()
                        prompt = prompt.strip("[]\"'").strip()
                        # Normalise any hallucinated Georgian characters back to Myanmar Unicode
                        script = script.replace('\u10E2', '\u1010')
                        scenes.append({
                            "SCRIPT": script,
                            "VISUAL_PROMPT": prompt
                        })

        except Exception:
            pass


    # Fallback to Regex if YAML parsing fails
    if not scenes:
        script_prompt_pairs = re.findall(
            r"-\s*SCRIPT:\s*(.*?)\s*\n\s*VISUAL_PROMPT:\s*(.*?)(?=\n\s*-|\n\s*\w+:|$)",
            output_text,
            re.DOTALL | re.IGNORECASE
        )
        for s, p in script_prompt_pairs:
            cleaned_script = s.strip().replace('"', '').replace('\u10E2', '\u1010')
            scenes.append({
                "SCRIPT": cleaned_script,
                "VISUAL_PROMPT": p.strip().replace('"', '')
            })


    # Last resort fallback: wrap whole text as 1 scene
    if not scenes:
        scenes.append({
            "SCRIPT": output_text,
            "VISUAL_PROMPT": "A high-tech background loop, abstract data visualization"
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
        path = f"remotion/public/runs/{name}"
        os.makedirs(path, exist_ok=True)
        return path

    run_dir = make_run_dir(video_topic)
    print(f"📂 Run folder: {run_dir}")

    
    print(f"🚀 [1/4] Starting CrewAI Automation for Topic: '{video_topic}'")
    crew_output = run_shortform_crew(video_topic)
    
    # Parse structured scene edits
    title, scenes = parse_agent_output(str(crew_output))
    print(f"\n✨ Generated Title: {title}")
    print(f"📋 Total Scenes Extracted: {len(scenes)}")

    # Translate English script to Myanmar
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='en', target='my')
        print("\n🌐 Translating English script to Myanmar (Free)...")
        for scene in scenes:
            en_text = scene.get("SCRIPT", "")
            if en_text:
                my_text = translator.translate(en_text)
                scene["SCRIPT"] = my_text
                print(f"  En: {en_text[:40]}... -> My: {my_text[:40]}...")
    except Exception as e:
        print(f"⚠️ Translation failed: {e}. Subtitles may be in English.")

    # 1. Generate Voiceover for each scene
    print("\n🔊 [2/4] Generating Scene-Level Myanmar Voiceovers...")
    voice_files = generate_scene_voiceovers(scenes, run_dir=run_dir)
    
    # 2. Generate Asset for each scene
    print("\n📹 [3/4] Compiling Scene Assets (50% Pexels, 30% Unsplash, 20% Giphy)...")

    # Target ratio: 50% Pexels, 30% Unsplash, 20% Giphy
    # Cycle of 10 to perfectly match the 5:3:2 ratio while ensuring visual variety
    source_cycle = [
        "pexels", "unsplash", "pexels", "giphy", "pexels", 
        "unsplash", "pexels", "unsplash", "pexels", "giphy"
    ]
    scene_sources = [source_cycle[i % 10] for i in range(len(scenes))]

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


    # 3. Export JSON and trigger Remotion
    print("\n🎞️ [4/4] Rendering Dynamic Subtitled Video with Remotion...")
    import json
    import subprocess
    import shutil

    # Fallback to copy an existing BGM since video_editor.py was removed
    def get_bgm(output_path):
        fallback_bgm = "remotion/public/runs/How_to_Use_AI_Chatbots_for_Dai_20260711_200252/bgm.mp3"
        if os.path.exists(fallback_bgm):
            shutil.copy(fallback_bgm, output_path)
            return output_path
        return ""

    bgm_path = get_bgm(f"{run_dir}/bgm.mp3")
    
    render_scenes = []
    total_frames = 0
    fps = 30
    
    for idx, (scene, voice_path) in enumerate(zip(scenes, voice_files)):
        # Calculate audio duration using mutagen
        from mutagen.mp3 import MP3
        audio = MP3(voice_path)
        duration_sec = audio.info.length
        
        frames = int(duration_sec * fps)
        total_frames += frames
        
        # Make paths relative to remotion/public for staticFile()
        # Since remotion/public/runs is a symlink to output/runs, we can just use "runs/{run_name}/file"
        run_name = os.path.basename(run_dir)
        rel_video = f"runs/{run_name}/{os.path.basename(scene['VIDEO_PATH'])}"
        rel_voice = f"runs/{run_name}/{os.path.basename(voice_path)}"
            
        render_scenes.append({
            "videoPath": rel_video,
            "voicePath": rel_voice,
            "durationFrames": frames,
            "text": scene.get("SCRIPT", ""),
            "creditText": scene.get("CREDIT_TEXT", "")
        })

    # Add intro frames (3 seconds at 30 fps) to the total duration
    total_frames += 90

    # Ensure total duration meets the 60s minimum (1800 frames)
    if total_frames < 1800:
        total_frames = 1800

    run_name = os.path.basename(run_dir)
    rel_bgm = f"runs/{run_name}/{os.path.basename(bgm_path)}" if bgm_path else ""
        
    render_data = {
        "title": title,
        "totalDurationFrames": total_frames,
        "bgmPath": rel_bgm,
        "scenes": render_scenes
    }

    render_data_path = os.path.abspath(f"{run_dir}/render_data.json")
    with open(render_data_path, "w", encoding="utf-8") as f:
        json.dump(render_data, f, indent=2, ensure_ascii=False)
        
    abs_final_video_path = os.path.abspath(f"{run_dir}/final_video.mp4")
    
    print(f"🚀 Triggering Remotion Render (this may take a few minutes)...")
    try:
        subprocess.run(
            ["npx", "remotion", "render", "src/index.ts", "MainVideo", abs_final_video_path, f"--props={render_data_path}"],
            cwd="remotion",
            check=True
        )
        print(f"✅ Video successfully rendered at: {abs_final_video_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Remotion render failed: {e}")

if __name__ == "__main__":
    main()