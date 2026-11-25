# QC: check every generation before moving on

Nothing is "fixed" until it passes QC. Look at real frames and listen with whisper; a success status alone proves nothing.

## Working folder

Make one folder per job (customer material is confidential: when the job is closed, delete `clips/`, `vo/` and the `.wav` files, and keep only `manifest.json`, `report.md` and the sheets): `~/Downloads/story-fix-<short story id>/` with `clips/`, `vo/`, `qc/`, `sheets/`, a `manifest.json` (scene → aroll_id, media ids, VO line, speaker, language, issue, status, attempts, credits) and `report.md`. Keep it up to date, because it's what the final report and any escalation are built from.

## Before fixing: baseline evidence

1. `get_story_assets` (big, so parse the saved file with python). Download every clip and VO of the listed scenes (`curl -sfL <url> -o clips/<scene>.mp4`).
2. Run the QC script with the venv Python from setup:
   `~/.story-fixer-venv/bin/python "<skill dir>/scripts/qc_clip.py" clips/<scene>.mp4 --vo vo/<scene>.mp3 --lang <story language code> --out qc/<scene>`
   Add `--model large-v3` for Hebrew, Arabic, Hindi and other non-English stories (slower, much more accurate). It gives an 8-frame sheet, a sheet of every frame in the first 1.25 s, the transcript, the **detected** language (not forced), a text match against the VO, the word-level sync offset and the speech-span ratio.
3. Cast strip: download the character portraits (the url from `show_media` on each `portrait_media_id`) and the keyframe, then tile them into one image with ffmpeg (`ffmpeg -i a.png -i b.png -i c.png -filter_complex "[0][1][2]scale2ref…"`, or simply `hstack` after scaling to one height). `show_media` alone only displays in chat.
4. Look at every sheet yourself (Read the jpg) and write a one-line finding per scene.

## After each generation

1. `get_result(request_id)`. If it says succeeded but returned no file, re-pull `get_scene_assets`; the asset is often there.
2. Download the new file and run `qc_clip.py` on it with the scene's VO.
3. Check against this list and record pass/fail per item:

| Check | Pass when |
|---|---|
| **The reported issue** | It's gone, looking at the frames, not the prompt |
| Keyframe preserved | Frame 0 matches the approved still (composition, light, style) |
| Characters | Faces, hair, clothes and age match the portraits; nobody added or removed; look-alikes not swapped |
| Speaker | Only the speaker's mouth moves during speech; listeners' mouths closed |
| Words | Whisper text ≥ about 0.9 similar to the VO (misheard proper names are fine); no extra words, gibberish or "thanks for watching" filler at the edges |
| Language | `detected_language` = the story language with `detected_language_p` ≥ 0.8; no "language mismatch" note |
| Exact voice (lip-sync scenes) | `speech_span_ratio` between 0.88 and 1.12 (the script flags outside that), and the voice and pitch sound the same as the VO. A longer span or a higher pitch means it was re-voiced |
| Sync offset | `word_offset_s` within ±0.15 s (`env_offset_s` is a rougher cross-check), or fixable with A6 |
| Narration scenes | No speech in the clip; no mouths forming words |
| Motion | One clean action; no clipping through objects, floating, morphing or duplicate limbs; camera move as asked |
| First second | No character-sheet or reference flash on the `_first1s.jpg` sheet (every frame of the first 1.25 s) |
| Duration | Matches the scene; nothing cut off mid-word |
| Text, insignia, logos | No garbled text or real brand marks unless they belong |

4. **Pass:** set it on the story if the tool didn't already (`set_shot_media`), mark it fixed in the manifest, and move on.
5. **Fail:** name the exact failure and change the one thing that causes it: the keyframe if it's baked in, the prompt beat, the speaker wording, padding or the split. Then re-quote if the price changes, and retry. **The limit is 3 paid attempts per issue per shot**, counted across tools. After the third failure, escalate (`slack-reports.md`) and move on.

## Pilot rule

For a batch, run **one** job first, QC it fully, then run the rest. This catches a wrong prompt format, chip names, resolution case or audio wiring before it multiplies.

## Story-level check at the end

- Re-pull `get_story_assets`. Every touched shot points at the new file.
- `get_scene_audio` and `get_scene_captions` on every touched scene: VO on/off as intended, shot audio routing right, no `[tags]` in captions, names right.
- Scene durations still add up. Splits are in the right order.
- Tell the member to **reload the Atlabs editor** to see MCP changes.
- Optional: `export_story`, then spot-check the touched scenes in the export and measure the last 10 s for silence.

## Final report (what the member gets)

`report.md`, and the same in chat:
- story name and ids, workflow and default models used;
- a table: scene, customer issue, root cause, fix, model, attempts, credits, status (Fixed / Escalated / Not fixable / Skipped);
- credits quoted vs spent, and the balance before and after;
- anything the member should tell the customer (in plain words, no internal model names unless asked);
- escalations sent, with the Slack message text;
- **clone back:** a clear reminder that the member must clone the fixed story back into the customer's account (the fixes exist only on their clone until then), with "Clone back to customer: pending" in the report;
- the end-of-job summary DM to Chinmaya (template D in `slack-reports.md`), sent last, every time.
