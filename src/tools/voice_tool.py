import os
import wave
import struct
import asyncio
import edge_tts
import re

def _clean_text_for_tts(text: str) -> str:
    """Strip brackets, formatting, and stage directions that shouldn't be read out loud."""
    clean = text.replace("SCRIPT:", "").strip()
    clean = clean.strip("[]\"'")
    # Remove stage directions like (Laughter) or (Pause)
    clean = re.sub(r'\(.*?\)', '', clean)
    return clean.strip()

def generate_voiceover(text, output_path="output/temp/voice.mp3"):
    """
    Generates high-quality neural voiceover using edge-tts (ThihaNeural).
    Falls back to a silent WAV clip only if network or API fails.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    clean_text = _clean_text_for_tts(text)

    # If the text is empty, return a short silent clip
    if not clean_text:
        clean_text = "..."

    print(f"    🔊 Neural TTS: Generating voice file for: '{clean_text[:40]}...'")

    # Use Microsoft Edge neural Myanmar voice (Nilar is friendly, positive, and motivational)
    voice = "my-MM-NilarNeural"

    async def _async_generate():
        # Slow down rate by 4% to make it sound natural, clear, and less robotic
        communicate = edge_tts.Communicate(clean_text, voice, rate="-4%", pitch="+1Hz")
        await communicate.save(output_path)


    try:
        # Run async generation inside synchronous call
        asyncio.run(_async_generate())
        print(f"    ✅ Spoken audio compiled: {output_path}")
        return output_path
    except Exception as e:
        print(f"    ⚠️ Neural TTS failed ({e}). Falling back to silent WAV.")
        
        # Fallback silent WAV layout
        approx_duration = max(3.0, len(clean_text) / 6.0)
        approx_duration = min(10.0, approx_duration)
        
        sample_rate = 22050
        num_samples = int(approx_duration * sample_rate)
        
        wav_path = output_path.replace(".mp3", ".wav")
        try:
            with wave.open(wav_path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(sample_rate)
                for _ in range(num_samples):
                    w.writeframesraw(struct.pack("<h", 0))
            return wav_path
        except Exception as fallback_err:
            print(f"    ⚠️ Fallback WAV generation failed: {fallback_err}")
            return output_path

def generate_scene_voiceovers(scenes, run_dir="output"):
    """
    Generates voiceover audio clips for each scene and returns a list of output file paths.
    """
    os.makedirs(run_dir, exist_ok=True)
    voice_files = []

    for idx, scene in enumerate(scenes):
        script_line = scene.get("SCRIPT", "").strip()
        if not script_line:
            continue

        # We save directly as MP3 which edge-tts produces natively
        file_path = f"{run_dir}/voice_scene_{idx}.mp3"
        print(f"🔊 Scene {idx + 1}: Compiling voiceover for: '{script_line[:40]}...'")
        
        result_path = generate_voiceover(script_line, output_path=file_path)
        voice_files.append(result_path)

    return voice_files