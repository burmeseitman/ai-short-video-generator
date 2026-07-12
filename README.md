# AI Short Video Generator

An automated pipeline for generating cinematic, highly engaging short-form videos (TikTok, YouTube Shorts, Reels) using a mix of Local AI and external media APIs.

## Features
- **100% Free Scripting:** Uses a local Qwen 2.5 (14B) model via CrewAI to generate English scripts, which are automatically translated to Myanmar (Burmese) using Google Translate (`deep-translator`), ensuring $0 cost for text generation.
- **Dynamic Media Sourcing:** Automatically pulls media for exactly 6 scenes using a proportionally mixed ratio:
  - 25% Pexels Stock Video
  - 20% Unsplash Image-to-Video (via Fal.ai)
  - 25% Giphy GIFs (High-quality MP4s)
  - 30% Pure AI Text-to-Video (via Fal.ai Wan 2.1)
- **Advanced Video Editing:** 
  - Applies a dynamic Ken Burns zoom (100% to 108%) to all static/stock media to maintain visual pacing.
  - Features Karaoke-style active word highlighting for subtitles, ensuring perfect viewer retention.
  - Automatically center-crops all media to a 9:16 portrait aspect ratio (1080x1920).
- **Run-based Organization:** Each video generation is cleanly organized into its own `output/runs/YYYYMMDD_topic` directory.

## Prerequisites
- **Python 3.10+**
- **Ollama** installed locally with the `qwen2.5:14b` model pulled (`ollama run qwen2.5:14b`).
- API Keys for media sources:
  - Fal.ai (Video Generation)
  - Pexels (Stock Video)
  - Unsplash (Stock Images)
  - Giphy (GIFs)

## Setup
1. Clone this repository.
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   pip install deep-translator
   ```
3. Set up your environment variables by copying `.env.example` to `.env` and adding your API keys:
   ```env
   AI_MODEL=ollama/qwen2.5:14b
   WRITER_MODEL=ollama/qwen2.5:14b

   AI_VIDEO_PROVIDER=falai
   AI_VIDEO_API_KEY=your-fal-key
   AI_VIDEO_MODEL=fal-ai/wan-t2v

   PEXELS_API_KEY=your-pexels-key
   UNSPLASH_API_KEY=your-unsplash-key
   GIPHY_API_KEY=your-giphy-key
   PIXABAY_API_KEY=your-pixabay-key
   ```

## Usage
Run the main script and follow the prompt to enter your video topic:
```bash
python3 main.py
```

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
