# AI Short Video Generator

An automated pipeline for generating cinematic, highly engaging short-form videos (TikTok, YouTube Shorts, Reels) using 100% free external stock APIs and a local AI scriptwriter.

## Features
- **100% Free Scripting:** Uses a local Qwen 2.5 (14B) model via CrewAI to generate English scripts, which are automatically translated to Myanmar (Burmese) using Google Translate (`deep-translator`), ensuring $0 cost for text generation.
- **100% Free Media Sourcing:** Automatically pulls completely free visual assets for each scene using a proportionally mixed ratio to maintain visual variety and keep costs at $0:
  - 50% Pexels Stock Footage (MP4)
  - 30% Unsplash High-Quality Photos (JPG)
  - 20% Giphy GIFs (MP4)
- **Advanced Programmatic Editing with Remotion:** 
  - Mixes Images, GIFs, and Videos seamlessly into a single timeline using React-based rendering.
  - Applies a dynamic Ken Burns zoom-and-pan effect to all static Unsplash photos to maintain visual pacing.
  - Features Karaoke-style active word highlighting for subtitles, ensuring perfect viewer retention.
  - Automatically crops all media to a 9:16 portrait aspect ratio (1080x1920).
- **Run-based Organization:** Each video generation is cleanly organized into its own `remotion/public/runs/YYYYMMDD_topic` directory.

## Prerequisites
- **Node.js & npm** (Required for Remotion)
- **Python 3.10+**
- **Ollama** installed locally with the `qwen2.5:14b` model pulled (`ollama run qwen2.5:14b`).
- Free API Keys for media sources:
  - Pexels (Stock Video)
  - Unsplash (Stock Images)
  - Giphy (GIFs)

## Setup
1. Clone this repository.
2. Initialize the Python backend:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Initialize the Remotion frontend:
   ```bash
   cd remotion
   npm install
   cd ..
   ```
4. Set up your environment variables by copying `.env.example` to `.env` and adding your API keys:
   ```env
   AI_MODEL=ollama/qwen2.5:14b
   WRITER_MODEL=ollama/qwen2.5:14b

   PEXELS_API_KEY=your-pexels-key
   UNSPLASH_API_KEY=your-unsplash-key
   GIPHY_API_KEY=your-giphy-key
   ```

## Usage
Run the main script and follow the prompt to enter your video topic:
```bash
python3 main.py
```
*(You can also pipe the topic non-interactively: `echo "A day in the life of a golden retriever" | python main.py`)*

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
