---
name: video-finish
description: Edit, mix, subtitle and export vertical map videos with FFmpeg and CapCut. Use for scene assembly, Thai subtitles, ducking music, export validation and CapCut handoff.
---

# Map video finishing
Use the project virtual environment; FFmpeg is supplied by imageio_ffmpeg.get_ffmpeg_exe(), not necessarily on PATH.
Default export: 1080x1920 30fps, H.264 yuv420p, AAC, faststart.
Mix via scripts/map_video.py mix --video VIDEO --voice VOICE --music MUSIC --out OUTPUT.
The mix includes speech-driven music ducking and a -16 LUFS single-pass normalization target. Measure finished loudness for delivery-critical work; it is not guaranteed exact.
Match narration and picture durations before mixing; the command ends with the video. Never silently cut a sentence.
Use Thai-capable fonts and inspect shaping on a rendered frame. Prefer one subtitle line, highlight a few key words, keep lower UI safe areas.
For precise Thai subtitles import verified SRT into CapCut; never claim automatically aligned subtitles from estimated script durations.
Import map MP4 shots, narration, music, SFX and SRT into the existing CapCut app. Do not modify private CapCut project databases without verified format support.
Decode the final export, inspect first/middle/last frames, listen to audio and verify no clipped speech or missing attribution.
Export a clean master plus captioned version when requested.
