# AI Short Video Generator

An automated pipeline for generating cinematic, commercial-grade short-form videos (TikTok, YouTube Shorts, Reels) using 100% free external stock APIs, local AI models (CrewAI), and a custom MoviePy composition engine.

## Features

- **Local & Hybrid Multi-Agent System (CrewAI):**
  - **Researcher:** Uncovers controversial or high-retention facts on any given topic.
  - **Script Writer:** Natively writes conversational Burmese (အပြောစတိုင်) scripts with raw storyteller flow, formatted with SSML pacing tags.
  - **Director:** Mathematically breaks the script timeline into sequential 3-to-5 second scenes and maps them to visual cues.
  - **Video Critic (QA Gatekeeper):** Enforces rigid structural audit on timings, asset continuity, and query intent before rendering.
- **Dynamic Curation-Driven Sourcing:**
  - Automatically queries completely free stock platforms based on the Director's storyboard:
    - `ASSET_TYPE: VIDEO` → Queries **Pexels API** for cinematic loops.
    - `ASSET_TYPE: PHOTO` → Queries **Unsplash API** for high-quality images.
    - `ASSET_TYPE: GIF` → Queries **Giphy API** for high-energy animations.
- **Cinematic MoviePy 2.x Composition Engine:**
  - **Crossfade Transitions:** Smooth 0.5s blends between scenes.
  - **Ken Burns Zoom:** Alternating zoom-in/zoom-out motion with high-fidelity LANCZOS downsampling.
  - **Smart BGM Ducking:** Vectorized audio engine that automatically ducks background music to 10% volume during spoken lines, rising back to 30% during silence.
  - **Auto-Cropping:** Crops all landscape/portrait media to a portrait 9:16 aspect ratio (1080x1920) at 30 FPS.
- **Pristine Myanmar Unicode Subtitles:**
  - **Dynamic Wrapping Subtitle Cards:** Auto-calculates text layout coordinates, wrapping lines if width > 960px, and dynamically resizes the height and width of the rounded subtitle card.
  - **Grapheme Cluster-Safe Tokenization:** Splitting text safely at phrase and base consonant boundaries, ensuring combining marks never dangle and causing **zero dotted circles** or grammar mangling.
  - **Dual-Glyph Support:** Prioritizes system fonts (`Myanmar Sangam MN`) supporting both Latin and Myanmar characters to render English words alongside Burmese with zero tofu boxes.
  - **SSML Tag Stripping:** Cleans voiceovers and subtitles of raw XML markup tags for presentation.

## Setup

1. Clone this repository.
2. Initialize the Python virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Set up your environment variables by copying `.env.example` to `.env` and adding your free API keys:
   ```env
   # Model configurations (Qwen 2.5 local model via Ollama recommended)
   AI_MODEL=ollama/qwen2.5:14b
   WRITER_MODEL=ollama/qwen2.5:14b

   # Stock keys
   PEXELS_API_KEY=your-pexels-key
   UNSPLASH_API_KEY=your-unsplash-key
   GIPHY_API_KEY=your-giphy-key
   ```

## Usage

Run the main pipeline script and enter your topic:
```bash
python main.py
```
*(You can also pass the topic as a command line argument: `python main.py "How to spot a phishing email"`)*

The output video will be generated under `remotion/public/runs/YYYYMMDD_[topic]/final_video.mp4`.

## License
MIT
