---
name: thai-voice
description: Produce WASABI Thai narration, sound effects and timed subtitle inputs for map explainer videos. Use for ElevenLabs voiceover, pronunciation, audio timing and geographic name narration.
---

# WASABI voice
Use ../thai-neural-tts/SKILL.md as the default voice workflow, per the user. Use Niwat Neural for this map project. ElevenLabs is an optional alternative only when requested.
Create a conversational Thai script and verify province-name pronunciation and numbers.
Prefer the copied original thai-neural-tts/scripts/tts_cli.py. Use the connected ElevenLabs plugin only if requested. For local API use scripts/map_video.py tts --text-file audio/narration.txt --out audio/narration.mp3.
Read ELEVENLABS_API_KEY from the local environment only. Never read another project's secrets, print the key, or ask for it in chat.
Check generation scope and credit cost before large batches. Installation is not a paid generation test.
Keep one continuous narration and measure timestamps/forced alignment before syncing province highlights.
Write timed cues as start/end/text/province ISO fields. Treat estimated timings as estimates.
Generate a reusable synthetic whoosh with scripts/map_video.py sfx --out assets/sfx/whoosh.wav.
Keep narration, music and SFX separate. Do not fabricate provider authorization or claim a tested connection without an actual successful generation.
