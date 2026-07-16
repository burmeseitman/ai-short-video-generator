"""
MoviePy Video Composer — Cinematic Post-Processing Engine

Handles: Ken Burns zoom, crossfade transitions, BGM ducking,
audio mixing, and color grading for professional short-form video output.
"""

import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip,
    CompositeAudioClip, concatenate_videoclips, ColorClip, vfx
)


# ── Constants ──────────────────────────────────────────────────────────────────
TARGET_W, TARGET_H = 1080, 1920  # 9:16 portrait
TARGET_FPS = 30
CROSSFADE_SEC = 0.5
BGM_VOLUME_SPEECH = 0.10   # 10% during voiceover
BGM_VOLUME_SILENCE = 0.30  # 30% during silence gaps
INTRO_DURATION = 3.0       # seconds


def apply_ken_burns(clip, direction="zoom_in"):
    """
    Apply a slow Ken Burns zoom effect to a clip and center-crop to 1080×1920.
    Works on both video clips and image clips.
    """
    duration = clip.duration
    if duration is None or duration <= 0:
        duration = 5.0

    # We need extra resolution to zoom into, so we scale up first
    base_w, base_h = clip.size

    # Calculate the scale needed to fill 1080x1920 at minimum
    scale_w = TARGET_W / base_w
    scale_h = TARGET_H / base_h
    base_scale = max(scale_w, scale_h) * 1.15  # 15% extra headroom for zoom

    def zoom_factor(t):
        progress = t / duration if duration > 0 else 0
        if direction == "zoom_in":
            return base_scale * (1.0 + 0.08 * progress)
        else:  # zoom_out
            return base_scale * (1.08 - 0.08 * progress)

    def make_frame(get_frame, t):
        frame = get_frame(t)
        h, w = frame.shape[:2]
        
        factor = zoom_factor(t)
        new_w = int(w * factor)
        new_h = int(h * factor)

        # Resize using PIL for quality
        from PIL import Image
        img = Image.fromarray(frame)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        frame = np.array(img)

        # Center-crop to target
        h2, w2 = frame.shape[:2]
        cx, cy = w2 // 2, h2 // 2
        x1 = max(0, cx - TARGET_W // 2)
        y1 = max(0, cy - TARGET_H // 2)
        x2 = x1 + TARGET_W
        y2 = y1 + TARGET_H
        
        # Ensure we don't exceed bounds
        if x2 > w2:
            x1 = w2 - TARGET_W
            x2 = w2
        if y2 > h2:
            y1 = h2 - TARGET_H
            y2 = h2

        cropped = frame[y1:y2, x1:x2]

        # Safety: if crop is wrong size, pad with black
        if cropped.shape[0] != TARGET_H or cropped.shape[1] != TARGET_W:
            canvas = np.zeros((TARGET_H, TARGET_W, 3), dtype=np.uint8)
            ch, cw = min(cropped.shape[0], TARGET_H), min(cropped.shape[1], TARGET_W)
            canvas[:ch, :cw] = cropped[:ch, :cw]
            return canvas

        return cropped

    return clip.transform(lambda gf, t: make_frame(gf, t), apply_to=['mask'])


def load_media_clip(media_path, target_duration):
    """
    Load a video or image file and prepare it for the pipeline.
    Videos are trimmed/looped to match target_duration.
    Images are converted to clips of the target_duration.
    """
    ext = os.path.splitext(media_path)[1].lower()

    if ext in ('.jpg', '.jpeg', '.png', '.webp'):
        clip = ImageClip(media_path, duration=target_duration)
    elif ext in ('.mp4', '.webm', '.mov', '.gif'):
        clip = VideoFileClip(media_path)
        # Loop short clips to fill the target duration
        if clip.duration < target_duration:
            loops_needed = int(np.ceil(target_duration / clip.duration))
            clip = concatenate_videoclips([clip] * loops_needed)
        clip = clip.subclipped(0, target_duration)
    else:
        # Fallback: treat as image
        clip = ImageClip(media_path, duration=target_duration)

    return clip


def duck_bgm(bgm_clip, voice_clips_with_timing, total_duration):
    """
    Create a volume-ducked version of the BGM track.
    Lowers volume during voiceover sections, raises it during silence.
    
    voice_clips_with_timing: list of (start_sec, end_sec) tuples
    """
    def volume_func(t):
        for start, end in voice_clips_with_timing:
            if start <= t <= end:
                return BGM_VOLUME_SPEECH
        return BGM_VOLUME_SILENCE

    # Loop BGM if shorter than total duration
    if bgm_clip.duration < total_duration:
        loops_needed = int(np.ceil(total_duration / bgm_clip.duration))
        bgm_clip = concatenate_videoclips([bgm_clip] * loops_needed) if hasattr(bgm_clip, 'video') else bgm_clip.fx(vfx.loop, duration=total_duration)
    
    bgm_clip = bgm_clip.subclipped(0, total_duration)
    
    # Apply volume ducking using a smooth function
    return bgm_clip.transform(lambda gf, t: gf(t) * volume_func(t), keep_duration=True)


# ── Font Loading Setup ──────────────────────────────────────────────────────────
# Standard Myanmar Unicode compatible fonts on macOS
MYANMAR_FONTS = [
    "/System/Library/Fonts/Supplemental/Myanmar Sangam MN.ttc",
    "/System/Library/Fonts/Supplemental/Myanmar MN.ttc",
    "/System/Library/Fonts/NotoSansMyanmar.ttc",
    "/System/Library/Fonts/NotoSerifMyanmar.ttc",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
]

def get_best_font(font_size):
    """
    Returns the first available Myanmar-compatible font on the system,
    falling back to default Pillow font if none exist.
    """
    from PIL import ImageFont
    for path in MYANMAR_FONTS:
        if os.path.exists(path):
            try:
                # Specify index=0 for TrueType Collections (.ttc)
                return ImageFont.truetype(path, font_size, index=0)
            except Exception:
                continue
    return ImageFont.load_default()


def create_title_card(title, duration=INTRO_DURATION):
    """
    Create a simple dark title card with text.
    Uses Pillow for reliable text rendering (especially Myanmar).
    """
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (TARGET_W, TARGET_H), color=(17, 17, 17))
    draw = ImageDraw.Draw(img)

    font_size = 72
    font = get_best_font(font_size)

    # Word-wrap the title
    words = title.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > TARGET_W - 120:
            lines.append(current_line)
            current_line = word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    # Draw centered text
    total_text_height = len(lines) * (font_size + 20)
    y_start = (TARGET_H - total_text_height) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (TARGET_W - text_w) // 2
        y = y_start + i * (font_size + 20)

        # Text shadow
        draw.text((x + 3, y + 3), line, fill=(229, 9, 20), font=font)
        # Main text
        draw.text((x, y), line, fill=(255, 255, 255), font=font)

    clip = ImageClip(np.array(img), duration=duration)
    return clip.with_fps(TARGET_FPS)


def split_grapheme_clusters(text):
    """
    Splits Myanmar/English text into a list of individual renderable grapheme clusters.
    Ensures combining marks stay attached to their base characters.
    """
    import re
    clusters = []
    current = ""
    # Range of Myanmar combining marks, English diacritics, and zero-width characters
    combining_pattern = re.compile(r'[\u102b-\u103e\u1056-\u1097\u200b-\u200d\u0300-\u036f]')
    
    for char in text:
        if combining_pattern.match(char) and current:
            current += char
        else:
            if current:
                clusters.append(current)
            current = char
    if current:
        clusters.append(current)
    return clusters


def render_subtitle_overlay(text, duration, width=TARGET_W, height=TARGET_H):
    """
    Render animated karaoke-style subtitles as a transparent overlay clip.
    Strips emojis/control characters to prevent tofu boxes, splits long
    runs safely at grapheme cluster boundaries, and renders wrapped text.
    """
    import re
    if not text:
        return None

    # Step 1: Strip emojis and control characters to avoid tofu boxes
    clean_text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    clean_text = re.sub(r'[\u2600-\u27bf]', '', clean_text)
    clean_text = re.sub(r'[\u200b-\u200d]', '', clean_text)

    # Step 2: Segment safely at space, punctuation, or grapheme boundaries (Burmese Unicode safe)
    raw_tokens = re.split(r'(\s+|။|၊)', clean_text)
    words = []
    
    for token in raw_tokens:
        if not token or not token.strip():
            continue
        if token in ["။", "၊"]:
            if words:
                words[-1] += token
            else:
                words.append(token)
            continue
            
        if len(token) > 12:
            # Segment long space-free compound words at cluster boundaries
            clusters = split_grapheme_clusters(token)
            chunk_size = 8
            for i in range(0, len(clusters), chunk_size):
                sub_word = "".join(clusters[i:i+chunk_size])
                if sub_word:
                    words.append(sub_word)
        else:
            words.append(token)

    if not words:
        return None

    # Step 3: Group into chunks of 4 words
    chunk_size = 4
    chunks = [words[i:i + chunk_size] for i in range(0, len(words), chunk_size)]
    num_chunks = len(chunks)
    chunk_duration = duration / num_chunks if num_chunks > 0 else duration

    fps = TARGET_FPS
    font_size = 56
    font = get_best_font(font_size)

    def make_rgba_frame(t):
        # Base transparent canvas
        img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Active chunk index
        chunk_idx = min(num_chunks - 1, int(t / chunk_duration))
        active_chunk = chunks[chunk_idx]

        # Active word index inside chunk
        t_in_chunk = t - chunk_idx * chunk_duration
        word_idx_in_chunk = min(len(active_chunk) - 1, int((t_in_chunk / chunk_duration) * len(active_chunk)))

        # Define bounds and sizing
        line_height = font_size + 16
        max_content_w = width - 120  # Max printable text width: 960px

        # ── Simulation Pass ──
        # Simulates laying out words to find exact card width & height
        sim_x = 0
        sim_y = 0
        max_sim_w = 0
        
        for idx, word in enumerate(active_chunk):
            word_bbox = draw.textbbox((0, 0), word + ' ', font=font)
            word_w = word_bbox[2] - word_bbox[0]
            
            # Wrap to next line if exceeds boundary
            if sim_x + word_w > max_content_w and sim_x > 0:
                sim_x = 0
                sim_y += line_height
                
            sim_x += word_w
            max_sim_w = max(max_sim_w, sim_x)

        total_text_w = max_sim_w
        total_text_h = sim_y + (font_size + 10)

        # Center card layout
        card_w = min(width - 60, total_text_w + 60)
        card_h = total_text_h + 40
        card_x = (width - card_w) // 2
        card_y = height - card_h - int(height * 0.15)  # Position at bottom 15%

        # Draw semi-transparent card background on canvas
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            radius=15,
            fill=(0, 0, 0, 160)
        )
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        # ── Rendering Pass ──
        # Layout and render words dynamically
        cursor_x = card_x + 30
        cursor_y = card_y + 20

        for i, word in enumerate(active_chunk):
            word_bbox = draw.textbbox((0, 0), word + ' ', font=font)
            word_w = word_bbox[2] - word_bbox[0]

            # Wrap to next line if word exceeds width
            if cursor_x + word_w > card_x + 30 + max_content_w and cursor_x > card_x + 30:
                cursor_x = card_x + 30
                cursor_y += line_height

            is_active = (i == word_idx_in_chunk)
            color = (255, 215, 0, 255) if is_active else (255, 255, 255, 255)

            # Draw shadow
            draw.text((cursor_x + 2, cursor_y + 2), word, fill=(0, 0, 0, 200), font=font)
            # Draw word
            draw.text((cursor_x, cursor_y), word, fill=color, font=font)

            cursor_x += word_w

        return np.array(img)

    from moviepy import VideoClip
    # Extract RGB frames (shape: H, W, 3)
    subtitle_clip = VideoClip(lambda t: make_rgba_frame(t)[:, :, :3], duration=duration)
    # Extract alpha mask frames as values between 0.0 and 1.0 (shape: H, W)
    mask_clip = VideoClip(lambda t: make_rgba_frame(t)[:, :, 3] / 255.0, duration=duration, is_mask=True)
    
    return subtitle_clip.with_mask(mask_clip).with_fps(fps)


def compose_final_video(scenes, voice_files, run_dir, title, bgm_path=None):
    """
    Master composition function. Takes scene data and voice files,
    produces a cinematic final video with transitions, ducking, and grading.
    
    Returns: path to the final rendered MP4
    """
    print("🎬 MoviePy Composer: Starting cinematic post-processing...")

    scene_clips = []
    voice_timings = []
    current_time = INTRO_DURATION  # Account for intro card

    # ── Step 1: Create Title Card ──────────────────────────────────────────────
    print("  📝 Rendering title card...")
    title_clip = create_title_card(title)
    scene_clips.append(title_clip)

    # ── Step 2: Process Each Scene ─────────────────────────────────────────────
    for idx, (scene, voice_path) in enumerate(zip(scenes, voice_files)):
        media_path = scene.get("VIDEO_PATH", "")
        script_text = scene.get("SCRIPT", "")

        if not media_path or not os.path.exists(media_path):
            print(f"  ⚠️ Scene {idx + 1}: Missing media file, creating black placeholder")
            media_path = None

        # Get voiceover duration to match scene length
        try:
            voice_clip = AudioFileClip(voice_path)
            scene_duration = voice_clip.duration + 0.5  # Small padding
        except Exception as e:
            print(f"  ⚠️ Scene {idx + 1}: Could not read voice file ({e}), using 10s default")
            voice_clip = None
            scene_duration = 10.0

        print(f"  🎥 Scene {idx + 1}/{len(scenes)}: {scene_duration:.1f}s — Ken Burns + Subtitles...")

        # Load and process media
        if media_path:
            media_clip = load_media_clip(media_path, scene_duration)
        else:
            media_clip = ColorClip(size=(TARGET_W, TARGET_H), color=(30, 30, 40), duration=scene_duration)

        # Apply Ken Burns zoom + crop to portrait
        directions = ["zoom_in", "zoom_out"]
        media_clip = apply_ken_burns(media_clip, direction=directions[idx % 2])
        media_clip = media_clip.with_duration(scene_duration)

        # Render subtitle overlay
        subtitle_clip = render_subtitle_overlay(script_text, scene_duration)

        # Composite: media + subtitle overlay
        if subtitle_clip:
            scene_composite = CompositeVideoClip(
                [media_clip, subtitle_clip.with_position(("center", "bottom"))],
                size=(TARGET_W, TARGET_H)
            ).with_duration(scene_duration)
        else:
            scene_composite = media_clip

        # Attach voiceover audio
        if voice_clip:
            scene_composite = scene_composite.with_audio(voice_clip)

        scene_clips.append(scene_composite)

        # Track voice timing for BGM ducking
        voice_timings.append((current_time, current_time + scene_duration - 0.5))
        current_time += scene_duration

    # ── Step 3: Crossfade Transitions ──────────────────────────────────────────
    print("  ✨ Applying crossfade transitions...")
    if len(scene_clips) > 1:
        # Apply fade-in/fade-out for smooth transitions
        processed_clips = [scene_clips[0]]
        for i in range(1, len(scene_clips)):
            clip = scene_clips[i]
            clip = clip.with_effects([vfx.CrossFadeIn(CROSSFADE_SEC)])
            processed_clips.append(clip)
        
        # Concatenate with crossfade padding
        final_video = concatenate_videoclips(processed_clips, padding=-CROSSFADE_SEC, method="compose")
    else:
        final_video = scene_clips[0] if scene_clips else ColorClip(
            size=(TARGET_W, TARGET_H), color=(0, 0, 0), duration=5
        )

    # ── Step 4: BGM Ducking & Audio Mix ────────────────────────────────────────
    if bgm_path and os.path.exists(bgm_path):
        print("  🎵 Mixing BGM with smart ducking...")
        try:
            bgm = AudioFileClip(bgm_path)
            total_dur = final_video.duration

            # Loop BGM if needed
            if bgm.duration < total_dur:
                loops = int(np.ceil(total_dur / bgm.duration))
                from moviepy import concatenate_audioclips
                bgm = concatenate_audioclips([bgm] * loops)
            bgm = bgm.subclipped(0, total_dur)

            # Apply ducking: lower volume during speech
            def apply_ducking(get_frame, t):
                audio_frame = get_frame(t)
                if isinstance(t, np.ndarray):
                    vol = np.full(t.shape, BGM_VOLUME_SILENCE)
                    for start, end in voice_timings:
                        vol[(t >= start) & (t <= end)] = BGM_VOLUME_SPEECH
                    vol = vol.reshape(vol.shape + (1,) * (audio_frame.ndim - 1))
                    return audio_frame * vol
                else:
                    vol = BGM_VOLUME_SILENCE
                    for start, end in voice_timings:
                        if start <= t <= end:
                            vol = BGM_VOLUME_SPEECH
                            break
                    return audio_frame * vol

            bgm = bgm.transform(apply_ducking, keep_duration=True)

            # Mix BGM with existing audio
            if final_video.audio:
                mixed_audio = CompositeAudioClip([final_video.audio, bgm])
                final_video = final_video.with_audio(mixed_audio)
            else:
                final_video = final_video.with_audio(bgm)
        except Exception as e:
            print(f"  ⚠️ BGM mixing failed ({e}), continuing without BGM")

    # ── Step 5: Color Grading (Removed as requested) ───────────────────────────
    pass

    # ── Step 6: Render Final Output ────────────────────────────────────────────
    output_path = os.path.join(run_dir, "final_video.mp4")
    print(f"  🚀 Rendering final video to: {output_path}")
    print(f"     Resolution: {TARGET_W}×{TARGET_H} | FPS: {TARGET_FPS}")
    print(f"     Duration: {final_video.duration:.1f}s | Scenes: {len(scenes)}")

    final_video.write_videofile(
        output_path,
        fps=TARGET_FPS,
        codec="libx264",
        audio_codec="aac",
        bitrate="8000k",
        preset="medium",
        threads=4,
        logger="bar"
    )

    # Cleanup
    final_video.close()
    for clip in scene_clips:
        try:
            clip.close()
        except:
            pass

    print(f"  ✅ Final video rendered: {output_path}")
    return output_path
