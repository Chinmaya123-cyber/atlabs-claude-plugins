# Fix playbook: diagnose, then the recipe

Fix at the earliest layer where the error lives. The layers are **script/VO → keyframe image → motion → lip sync → audio mix/captions**. A later layer can't fix an earlier one: every clip starts from its keyframe, and every lip sync speaks the scene's VO.

## 1. Diagnosis table

For each reported issue, find the scene, pull its evidence (see `qc.md`: frames, whisper, shot history) and match it below.

| Symptom | Where it really lives | Check | Recipe |
|---|---|---|---|
| Wrong object or person in the shot: someone outside a railing, an arm inside a wall, an extra prop, a wrong number, day in a night window, an animal on the wrong side of a fence | **Keyframe** | Frame 0 of the clip and the shot's still show it. Langfuse "direct this shot" rounds: several motion retries with the error still there | A1 then A2 |
| Customer retried motion 3+ times on one scene and it's still wrong | Almost always the **keyframe** | Langfuse "direct this shot" rounds, the customer's own edits in the billing log if you have access (a clone keeps no history of the customer's attempts) | A1 then A2 |
| Body passes through things, floating objects, running up walls | **Motion prompt** overloaded (two beats plus a camera orbit in 5–9 s) | Read the clip's prompt | A2 with one action and a locked or slow camera |
| Lip sync gone or mouth not moving | Clip was regenerated as plain motion ("no dialogue"), or made from the References tab at 480p | Whisper on the clip: no speech. Prompt has no `<Audio 1>` | A3 |
| Is the scene dialogue at all? | **Check first.** Narration and thought scenes must NOT be lip-synced | `get_screenplay` speaker; scene text; Langfuse scene_data | Narration: mouths closed, scene VO plays |
| Wrong person talks, or both talk | Lip-sync prompt didn't pin the speaker, or look-alike characters | Frame sheet during speech | A3 with the speaker named by clothing and hair, listeners "mouths closed and still" |
| Two characters swap faces | Near-identical cast portraits | Compare portraits side by side | Give one character a distinguishing trait in the keyframe edit (A1); state it in subject_definitions |
| Voice sounds different from the rest, higher or faster | `scene_edit_lipsync` with H3 Highspeed/Max **re-voiced** the line | Whisper span length vs the VO; pitch | A3 with the reference-to-video `fully_copy` wording, or Sync 3 |
| Wrong language in the clip | Prompt didn't lock the language | Whisper language and probability | A3 with `<d>[Language] …</d>` and "<Language> only" in retention_analysis |
| Name said wrong (TTS) | **VO** text or spelling | Whisper the VO | A4, then A3 for that scene |
| Character's face or age drifts in a close-up or second shot | Model redraws the face on a cut | Compare against `portrait_media_id` | A1 if the still is wrong; else A2/A3 single shot, or name "face follows @Mention exactly" |
| Portrait contradicts the script (portrait shows a goat, text says rabbit) | **Cast portrait** | `list_story_characters` | Tell the member; fixing the cast changes every scene, so escalate unless they ask |
| Scene longer than 15 s with dialogue | H3 limit (audio ref and clip max 15 s) | `duration_seconds` | A5 split, then A3 per part |
| Static body in a long talking clip | One long lip-sync take | Frame sheet | A5 split into an action shot and a shorter talking shot |
| Lip sync weird on a wide shot | Mouths too small in frame | Frame sheet | A3 with 1 s on the wide frame, then a hard cut to a medium close-up of the speaker |
| Character-sheet or reference flash in the first ~1 s | Model artifact | Frames 0–24 | Trim the shot start (`trim_shot_video`), or regenerate if it's long |
| Audio late or early vs lips | H3 ref clips can place a padded short line 1.6–1.9 s late | Whisper word-centre offset, clip vs VO | A6 |
| One voice much quieter | Voice loudness differs per voice | `ebur128` per VO | A6 levelling |
| Captions show `[tags]` or wrong names | Caption source | `get_scene_captions` | A7 (`resync_captions`) |
| Many more scenes or a longer runtime than the script asked | **Pipeline / script inflation** | Script vs `get_story` | Not fixable shot by shot. Report it and escalate if the customer wants a rebuild |
| Sports or complex body mechanics wrong | Known model weak spot | – | One clear action per clip. If 3 attempts fail, escalate. A missing helmet etc. can trace back to the cast portrait |

## 2. Recipes A1–A7

Before any paid call: `get_story` status must be COMPLETED (or NOT_STARTED). The member has approved the quote. You've fetched fresh media ids from `get_story_assets` / `get_scene_assets`.

### A1. Keyframe fix
`scene_edit_image(aroll_id, source_media_id=<current still: the shot's image, or animated_from_media_id behind the clip>, prompt, [reference_media_ids])`. Leave `model` out to keep the story's own image model. Use 1K unless asked for more.
- Prompt: `Edit @CurrentFrame: <one precise change>. Keep everything else exactly the same: <characters, clothes, light, composition, style>.` With reference images, the source becomes `@Image1` and references start at `@Image2`, or use a portrait's cast mention.
- Spell exact sequences out ("blocks numbered 1, 2, 3, 4, 5 left to right, no repeats, none missing").
- QC the still (see `qc.md`: look at it next to the portraits) **before** any motion or lip-sync spend. Then A2 or A3 from the new still.
- New picture from scratch: `scene_edit_new_image` in the story's style.

### A2. Motion, no dialogue
`scene_edit_motion` with the workflow-default i2v model (often `h3_highspeed`, 768p) and `start_frame_media_id` = the (fixed) still. Duration = the scene length (5–15 s).
- Prompt in the pipeline's own format: fetch the motion template the session used (`getPrompt` with its promptName). Otherwise use the H3 image-to-video format (the `h3-prompt-writing` skill if installed): three fields in order, `integrated_multimodal_description` (timed beats: who does what, camera, sound), then `overall_soundscape` (one line of ambience), then `non_diegetic_music: None`.
- **Start-frame models and the Atlabs chip rules:** the tool passes the start frame itself, and a motion prompt must **not** mention it. Don't write any "first frame / <Picture 1> is referenced" line, and no `<Picture 1>`/`@Image1`; describe what is already in frame in words ("the girl on the top bunk…") and only use cast @mentions that are also passed as references.
- **One action, one camera move** (static, or a slow push). Nothing that isn't in the still enters the frame.
- End with "No dialogue, no voices, no singing, no music." H3 always makes audio.
- Every @mention in the prompt must be among the references, and every reference must be mentioned. A motion prompt never names the start frame itself.

### A3. Lip sync (dialogue scenes) — the house method
Use **reference-to-video through `scene_edit_motion`**, with the workflow default model (usually `h3_highspeed_reference_to_video`, `"768p"`, `generate_audio: true`).
- `reference_image_ids` = `[the scene still FIRST, then the portrait_media_id of each @mentioned character visible in frame]`.
- `reference_audio_ids` = `[the scene's own voiceover media_id]`, **only the speaking character's line**. Never re-generate the VO unless A4 applies; keep the original file.
- **Step 0: check the still.** Speaker visible and facing camera, mouth area clean, right cast and clothes. If not, A1 first.
- Audio must be 2–15 s. If it's shorter, pad it with silence (`ffmpeg -i in.mp3 -af apad=whole_dur=2.5 out.mp3`), upload it with `start_upload` and a curl PUT (the PUT response holds the new `media_id`), and use that. If it's longer than 15 s, A5 first.
- Duration = max(model minimum, VO length rounded up): `h3_highspeed_reference_to_video` starts at 4 s, so a 2.6 s line still takes 4 s, and a 7.4 s line takes 8 s.
- **Prompt:** fetch the session's lip-sync template (`getPrompt` with the lip-sync promptName seen in the session) and write it exactly in its model-spec format. For MiniMax H3 that is: six sections, ≤ 4,500 chars, `<Picture 1>`/`<Audio 1>`, the speaker as `<Subject 1> (S1)`, dialogue as `<d>[Language] exact words</d>`, "lips sync precisely to every syllable of <Audio 1>", listeners silent with mouths closed, no music.
  - No template available? Write the six H3 reference sections yourself, in this order: `subject_definitions` (one line each for <Picture 1>, each visible character as <Subject N>, the environment, and <Audio 1> bound to the speaker), `summary` (one or two sentences, starting `[keyframe completion + audio reuse]`), `retention_analysis` (one line per label: fully_preserved / fully_copy), `detailed_description` (style line, then `[Shot 1]` from <Picture 1>, the line in `<d>[Language] …</d>`, the lip-sync sentence, performance, one camera move, settle), `overall_soundscape` (one sentence), `non_diegetic_music` (`N/A. No music. No extra dialogue, voices or vocal sounds beyond <Audio 1>.`).
  - The Atlabs tool wants chips. Map `<Picture 1>` to `@Image1` (the still) and `<Audio 1>` to `@Audio1`, and name portraits by cast mention (`@Ella`). The tool refuses unmentioned or unknown chips, and the error lists the allowed ones.
  - In `retention_analysis`, add: `<Audio 1>: fully_copy - the exact recording is reused 1:1: the same voice, timbre, pitch, speed and pauses, not re-voiced, re-spoken or re-timed. <Language> only.`
  - Identify the speaker by visible clothing and hair when characters look alike, and add "She is a different person from <Subject 2>".
  - Wide shots: `[Shot 1]` holds the wide frame about 1 s with nobody speaking, then `[Shot 2] At 00:01.000` hard-cuts to a medium close-up of the speaker for the line.
- **Fallback for a clip that's already good but lost sync:** `scene_edit_lipsync(aroll_id, source_media_id=<the clip>, model="sync_3", auto_detect_speaker or speaking_character_media_id)`. It keeps the audio exactly, takes no prompt and needs a video. Avoid H3 Highspeed/Max in `scene_edit_lipsync` when the exact voice matters, because they re-voice.
- Narration scenes: no audio reference; "every mouth stays closed"; the scene VO plays over the clip.

### A4. Voiceover fix
- Narrator or speaker scene: `scene_edit_voiceover(scene_id, text)` with corrected spelling, about 0.1 cr. On a scene whose voice comes from its speaker, **don't** pass `voice_code`.
- Character line that needs a specific voice: `generate_voice(text, voice_code=<character's voice_code from list_story_characters>)`, then `set_scene_voiceover_file(scene_id, media_id)`.
- A new VO rewrites that scene's captions. Re-check them, and redo lip sync (A3) for that scene.
- Check that ElevenLabs tags (`[Calm]`, `[short pause]`) don't end up on screen.

### A5. Split a long scene
`split_scene(scene_id, at_seconds | after_word | at_shot_aroll_id)` is free (exactly one cut point; not in Cartoon V8 stories). Clones often have empty captions, so use `at_seconds` at a natural VO pause (`ffmpeg -i vo.mp3 -af silencedetect=n=-35dB:d=0.25 -f null -`). Wait for `split_status` to clear, re-fetch ids, then A3 each part (each ≤ 15 s), with a wider shot and a closer shot for variety.

### A6. Audio timing and level
- **Offset:** measure the median gap between whisper word centres in the clip and the VO. For 0.1–0.45 s, use `set_scene_audio(voiceover_start_seconds=…)`; this does **not** move captions. For larger gaps, bake silence into the file (`-af adelay=1850|1850`), re-upload, `set_scene_voiceover_file`, set the start back to 0, and the captions rebuild.
- **Level:** measure with `ffmpeg -i f -af ebur128 -f null -`. Apply exact gain per file to −16 LUFS (`volume=<-16-I>dB,alimiter=limit=0.89`); single-pass loudnorm leaves short lines low. Re-upload.
- **Routing (needs the member's choice, listed in the quote):** `set_scene_audio` and `set_shot_audio` require asking "keep both, mute the voiceover, or mute the shot". Recommend one; for dialogue clips, either the clip audio is on and the VO is off (`set_scene_audio`), or the levelled VO is on and the shot is muted (`set_shot_audio(aroll_id, is_on=false)`). Every `set_scene_voiceover_file` turns shot audio back on, so mute it again if needed. Check that no lip-synced scene ends up silent.

### A7. Captions
`get_scene_captions`, then `resync_captions(scene_id, text)` with the corrected words (names, casing, stripped tags); Atlabs re-times every word to the audio. Free, but confirm the change like any edit. Use `override_captions` only when you must set timings yourself (e.g. the clone has no caption timings at all).

## 3. What not to do
- Don't edit scenes the customer didn't list, unless the fix requires it (a split, or a neighbouring shot for continuity). If so, say why in the plan.
- Don't regenerate the whole story or the cast to fix a few shots.
- Don't switch away from the workflow models on your own (see `models-and-pricing.md`).
- Don't retry the same prompt unchanged. Every retry changes something specific that QC pointed at.
- Don't touch billing, refunds or customer messages. That's Chinmaya's call.
