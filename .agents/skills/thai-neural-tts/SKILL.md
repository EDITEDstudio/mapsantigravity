---
name: thai-neural-tts
description: "Generates high-quality Thai Neural TTS voiceovers (and multilingual speech) using Microsoft Edge Neural TTS with natural pacing, custom pitch/speed tuning, inter-sentence pauses, multi-character dialogues, and subtitle timestamp sync. Exports standalone MP3/WAV audio files. Use whenever the user asks to generate Thai voice, synthesize speech, create podcast or narration audio, adjust voiceover speed or pitch, or build multi-character dialogues."
---

# Thai Neural TTS Voiceover Skill (สร้างเสียงพากย์ภาษาไทยด้วย AI)

## Overview
A lightweight, studio-grade Thai Text-to-Speech (TTS) production tool powered by **Microsoft Edge Neural Voice Models**. Produces natural human-like cadence, expressive intonation, and clean pronunciation for Thai storytelling, explainer reels, video tutorials, audiobooks, and podcasts—completely free with **zero API keys required**.

### Key Features
- **Neural Thai Voices**:
  - `th-TH-NiwatNeural` (`niwat`): Male, confident, warm, professional narrator.
  - `th-TH-PremwadeeNeural` (`premwadee`): Female, bright, clear, natural conversational tone.
- **Speed & Pitch Control**: Custom speech rates (`--rate "-15%"` to `"+20%"`) and pitch offsets (`--pitch "+5Hz"`).
- **Multi-Speaker Dialogues**: Stitch conversations between multiple characters with customizable pause intervals (`pauseBetweenTurns`).
- **Karaoke Subtitle Sync**: Automatically calculates phrase and turn timestamps for HTML5/video subtitles.
- **Zero Configuration**: Uses `edge-tts` and standard `ffmpeg`.

---

## Quick Start CLI

```bash
# 1. Synthesize a single sentence
python3 scripts/tts_cli.py speak "สวัสดีครับ ยินดีต้อนรับสู่ช่องของเรา" -o narration.mp3 -v niwat

# 2. Synthesize using slower, relaxed pacing (ideal for tutorials)
python3 scripts/tts_cli.py speak "วันนี้เรามาเรียนรู้การใช้ AI กันครับ" -o slow_voice.mp3 -v niwat --rate "-10%"

# 3. Synthesize female voice
python3 scripts/tts_cli.py speak "ยินดีให้บริการค่ะ มีอะไรให้ช่วยไหมคะ" -o female.mp3 -v premwadee

# 4. Synthesize entire text file
python3 scripts/tts_cli.py file my_script.txt -o full_script.mp3 -v niwat

# 5. Synthesize multi-character dialogue with karaoke timing export
python3 scripts/tts_cli.py dialogue examples/sample_dialogue.json -o conversation.mp3 -t timing.json

# 6. List all available Thai / English voices
python3 scripts/tts_cli.py list-voices --lang th
python3 scripts/tts_cli.py list-voices --lang en
```

---

## Voice Presets

| Shortcut | Full Voice ID | Gender | Best For |
| :--- | :--- | :--- | :--- |
| `niwat` | `th-TH-NiwatNeural` | Male | Narrator, Tech Explainer, Documentaries, Storytelling |
| `premwadee` | `th-TH-PremwadeeNeural` | Female | Customer Assistant, Casual Chat, Explainer, Commercials |
| `andrew` | `en-US-AndrewNeural` | Male | English Voiceover, Podcast host |
| `ava` | `en-US-AvaNeural` | Female | English Conversational Assistant |

---

## Recommended Speed (`--rate`) Settings

- **Tutorials / Complex Topics**: `-8%` to `-12%` (gives listeners time to digest dense instructions)
- **Standard Explainer / Reels**: `+0%` to `+3%` (crisp, engaging, energetic)
- **High-energy Shorts / Hooks**: `+6%` to `+10%` (fast-paced TikTok intro hook)

---

## Multi-Speaker Dialogue JSON Schema

Create a JSON file (e.g. `dialogue.json`):

```json
{
  "pauseBetweenTurns": 0.35,
  "turns": [
    {
      "speaker": "Host",
      "voice": "niwat",
      "rate": "+0%",
      "text": "ข้อความของพิธีกรคนที่ 1"
    },
    {
      "speaker": "AI Assistant",
      "voice": "premwadee",
      "rate": "-5%",
      "pitch": "+2Hz",
      "text": "ข้อความตอบกลับของตัวละครที่ 2"
    }
  ]
}
```

Then run:
```bash
python3 scripts/tts_cli.py dialogue dialogue.json -o master_dialogue.mp3 -t timestamps.json
```

---

## Python API Integration

```python
import asyncio
import edge_tts

async def generate():
    text = "ข้อความที่ต้องการให้พูด"
    comm = edge_tts.Communicate(text, "th-TH-NiwatNeural", rate="+0%")
    await comm.save("output.mp3")

asyncio.run(generate())
```
