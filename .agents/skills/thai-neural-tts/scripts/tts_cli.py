#!/usr/bin/env python3
"""
Thai & Multilingual Neural Voice Generator CLI
Supports:
  - Single phrase / sentence generation
  - Text file / script batch synthesis
  - Multi-speaker dialogue with per-character voice, rate, pitch, and inter-turn pause
  - Word & phrase timing export for karaoke subtitle synchronization
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile
import wave
import edge_tts

VOICE_PRESETS = {
    "niwat": {
        "id": "th-TH-NiwatNeural",
        "name": "นิวัตน์ (Niwat)",
        "gender": "Male",
        "style": "Narrator / Host / Confident / Professional",
    },
    "premwadee": {
        "id": "th-TH-PremwadeeNeural",
        "name": "เปรมวดี (Premwadee)",
        "gender": "Female",
        "style": "Friendly / Clear / Natural / Assistant",
    },
    # Common English companions for bilingual content
    "andrew": {
        "id": "en-US-AndrewNeural",
        "name": "Andrew (US)",
        "gender": "Male",
        "style": "Warm / Natural / Podcast",
    },
    "ava": {
        "id": "en-US-AvaNeural",
        "name": "Ava (US)",
        "gender": "Female",
        "style": "Conversational / Clear",
    },
}


def resolve_voice(voice_str: str) -> str:
    v_lower = voice_str.lower()
    if v_lower in VOICE_PRESETS:
        return VOICE_PRESETS[v_lower]["id"]
    return voice_str


async def list_voices(lang_filter: str = "th"):
    voices = await edge_tts.list_voices()
    filtered = [v for v in voices if v["Locale"].lower().startswith(lang_filter.lower())]
    print(f"\n=== Available Voices for Locale '{lang_filter}' ({len(filtered)} found) ===")
    for v in filtered:
        print(f"• {v['ShortName']:<26} | Gender: {v['Gender']:<6} | {v.get('FriendlyName', '')}")
    print("\nPresets shortcuts: 'niwat', 'premwadee', 'andrew', 'ava'")


async def _safe_communicate_save(text: str, voice: str, rate: str = "+0%", volume: str = "+0%", pitch: str = None, out_file: str = ""):
    import re
    kwargs = {"text": text, "voice": voice}
    if rate and rate != "+0%":
        kwargs["rate"] = rate
    if volume and volume != "+0%":
        kwargs["volume"] = volume
    if pitch and pitch not in ("+0Hz", "0Hz", "0"):
        kwargs["pitch"] = pitch

    # Tier 1: Direct synthesis
    try:
        comm = edge_tts.Communicate(**kwargs)
        await comm.save(out_file)
        return
    except Exception:
        pass

    # Tier 2: Drop pitch parameter
    if "pitch" in kwargs:
        kwargs.pop("pitch")
        try:
            comm = edge_tts.Communicate(**kwargs)
            await comm.save(out_file)
            return
        except Exception:
            pass

    # Tier 3: Normalize Thai-English boundary for Premwadee
    norm_text = re.sub(r"([ก-๙])\s+([A-Za-z0-9]+)", r"\1. \2", text)
    norm_text = re.sub(r"([A-Za-z0-9]+)\s+([ก-๙])", r"\1. \2", norm_text)
    if norm_text != text:
        try:
            kwargs["text"] = norm_text
            comm = edge_tts.Communicate(**kwargs)
            await comm.save(out_file)
            return
        except Exception:
            pass

    # Tier 4: Fallback to Niwat if voice was Premwadee
    if "premwadee" in voice.lower():
        try:
            kwargs["text"] = text
            kwargs["voice"] = "th-TH-NiwatNeural"
            comm = edge_tts.Communicate(**kwargs)
            await comm.save(out_file)
            return
        except Exception:
            pass

    # Final attempt: re-raise
    comm = edge_tts.Communicate(text=text, voice=voice)
    await comm.save(out_file)


async def synthesize_single(
    text: str,
    output_path: str,
    voice: str = "th-TH-NiwatNeural",
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
):
    voice_id = resolve_voice(voice)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    await _safe_communicate_save(
        text=text,
        voice=voice_id,
        rate=rate,
        volume=volume,
        pitch=pitch,
        out_file=output_path,
    )
    size_kb = os.path.getsize(output_path) / 1024
    print(f"Synthesized ({size_kb:.1f} KB) -> {output_path} [Voice: {voice_id}, Rate: {rate}]")


def get_ffmpeg():
    import shutil
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


async def synthesize_dialogue(dialogue_json_path: str, output_path: str, timing_output: str = None):
    ffmpeg_bin = get_ffmpeg()
    with open(dialogue_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        turns = data
        meta = {}
    else:
        turns = data.get("turns") or data.get("segments") or []
        meta = data
    if not turns:
        raise ValueError(f"No 'turns' or 'segments' found in {dialogue_json_path}")

    default_voice = meta.get("voice", "th-TH-NiwatNeural")
    default_rate = meta.get("rate", "+0%")
    default_pitch = meta.get("pitch", "+0Hz")
    default_pause_sec = float(meta.get("pauseBetweenTurns", 0.30))

    sr = 44100
    pcm_segments = []
    turn_timings = []
    cur_samples = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        for idx, turn in enumerate(turns):
            speaker = turn.get("speaker", "Speaker")
            voice_id = resolve_voice(turn.get("voice", default_voice))
            rate = turn.get("rate", default_rate)
            pitch = turn.get("pitch", default_pitch)
            text = turn.get("text", "")
            pause_sec = (
                float(turn["pauseAfterMs"]) / 1000.0
                if "pauseAfterMs" in turn and turn["pauseAfterMs"] is not None
                else default_pause_sec
            )
            tail_samples = max(0, int(round(sr * pause_sec)))

            tmp_mp3 = os.path.join(tmpdir, f"turn_{idx}.mp3")
            await _safe_communicate_save(
                text=text,
                voice=voice_id,
                rate=rate,
                pitch=pitch,
                out_file=tmp_mp3,
            )

            # Convert to s16le raw PCM via ffmpeg
            raw = subprocess.run(
                [ffmpeg_bin, "-i", tmp_mp3, "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"],
                capture_output=True,
                check=True,
            ).stdout
            import numpy as np

            arr = np.frombuffer(raw, dtype=np.int16)
            s0 = cur_samples
            s1 = s0 + len(arr)
            pcm_segments.append(arr)
            if tail_samples > 0:
                pcm_segments.append(np.zeros(tail_samples, dtype=np.int16))
            cur_samples = s1 + tail_samples

            turn_info = dict(turn)
            turn_info["turnIndex"] = idx
            turn_info["startSec"] = round(s0 / sr, 3)
            turn_info["endSec"] = round(s1 / sr, 3)
            turn_timings.append(turn_info)
            print(f"  Turn {idx + 1}/{len(turns)}: [{speaker}] ({turn_info['endSec'] - turn_info['startSec']:.2f}s) '{text[:30]}...'")

        import numpy as np

        full_pcm = np.concatenate(pcm_segments)
        wav_path = os.path.join(tmpdir, "dialogue.wav")
        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(full_pcm.tobytes())

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        subprocess.run(
            [ffmpeg_bin, "-y", "-i", wav_path, "-c:a", "libmp3lame", "-b:a", "128k", output_path],
            capture_output=True,
            check=True,
        )

        total_dur = round(len(full_pcm) / sr, 2)
        print(f"Generated Dialogue Audio ({total_dur:.2f}s) -> {output_path}")

        if timing_output:
            os.makedirs(os.path.dirname(os.path.abspath(timing_output)), exist_ok=True)
            for t in turn_timings:
                t["startRatio"] = round(t["startSec"] / total_dur, 4) if total_dur > 0 else 0.0
                t["endRatio"] = round(t["endSec"] / total_dur, 4) if total_dur > 0 else 0.0
            with open(timing_output, "w", encoding="utf-8") as f:
                json.dump({"durationSec": total_dur, "turns": turn_timings}, f, ensure_ascii=False, indent=2)
            print(f"Saved Timing Metadata -> {timing_output}")


def main():
    parser = argparse.ArgumentParser(description="Thai Neural TTS Generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # speak command
    speak_p = subparsers.add_parser("speak", help="Synthesize text string to MP3")
    speak_p.add_argument("text", help="Text to speak")
    speak_p.add_argument("-o", "--output", default="output.mp3", help="Output audio file (.mp3)")
    speak_p.add_argument("-v", "--voice", default="th-TH-NiwatNeural", help="Voice ID or preset ('niwat', 'premwadee')")
    speak_p.add_argument("-r", "--rate", default="+0%", help="Speed: '-20%', '+0%', '+10%'")
    speak_p.add_argument("-p", "--pitch", default="+0Hz", help="Pitch: '-5Hz', '+10Hz'")

    # file command
    file_p = subparsers.add_parser("file", help="Synthesize text from a script file (.txt)")
    file_p.add_argument("input_file", help="Path to text script")
    file_p.add_argument("-o", "--output", default="output.mp3", help="Output audio file (.mp3)")
    file_p.add_argument("-v", "--voice", default="th-TH-NiwatNeural", help="Voice ID or preset")
    file_p.add_argument("-r", "--rate", default="+0%", help="Speed: '-20%', '+0%', '+10%'")

    # dialogue command
    diag_p = subparsers.add_parser("dialogue", help="Synthesize multi-character dialogue from JSON")
    diag_p.add_argument("json_file", help="Path to dialogue JSON file")
    diag_p.add_argument("-o", "--output", default="dialogue.mp3", help="Output master audio file (.mp3)")
    diag_p.add_argument("-t", "--timestamps", default=None, help="Optional output JSON for karaoke timestamps")

    # list-voices command
    list_p = subparsers.add_parser("list-voices", help="List available neural voices")
    list_p.add_argument("-l", "--lang", default="th", help="Language prefix (e.g. 'th', 'en')")

    args = parser.parse_args()

    if args.command == "speak":
        asyncio.run(synthesize_single(args.text, args.output, args.voice, args.rate, pitch=args.pitch))
    elif args.command == "file":
        with open(args.input_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        asyncio.run(synthesize_single(content, args.output, args.voice, args.rate))
    elif args.command == "dialogue":
        asyncio.run(synthesize_dialogue(args.json_file, args.output, args.timestamps))
    elif args.command == "list-voices":
        asyncio.run(list_voices(args.lang))


if __name__ == "__main__":
    main()
