# Models: recommend the workflow defaults, then price them

## The rule (follow it every time)

**Recommend only the models the story's own workflow used.** A fix should look like the rest of the story and behave the way the pipeline does. A different model changes the look, the motion feel, the voice handling and the prompt format, and that creates new problems (style mismatch between neighbouring shots, re-voiced audio, refused prompts, wrong resolution, a different price).

The Atlabs MCP doesn't say which model made a clip (`get_story_assets` / `get_scene_assets` have no model field), so piece it together, in this order of trust:
1. **Billing log**, if the member has access (the query is in `atlabs-internal.md`): the pipeline's own generation rows name the exact model. This is the most exact source.
2. **Langfuse session:** the prompt templates that ran and their `getPrompt(...).config`, which names the model family (e.g. MiniMax H3 for lip sync). Some flows also have a model-selection stage with the model per scene; many don't.
3. **The clips themselves:** `ffprobe` resolution, where 1344×768 or 1424×800 means H3-family 768p. The prompt stored on each shot also tells you: six-section `subject_definitions…` means H3 reference-to-video, and `integrated_multimodal_description` means H3 image-to-video.
4. **The image edit default:** `scene_edit_image` keeps the story's own image model when `model` is left out, so leave it out.

Confirmed defaults so far (Nov 2026):

| Story type | Dialogue / lip-sync clips | Non-dialogue clips |
|---|---|---|
| Screenplay stories with speaking characters | `h3_highspeed_reference_to_video`, 768p, with the still, the portraits and the scene VO as references | MiniMax H3 family from the start frame; confirm the exact model from the billing log or the clip resolution |
| Music-video and kids-song stories | H3 family; confirm | H3 family; confirm |

`atlabs-internal.md` may list more confirmed defaults. If the sources disagree or say nothing, **don't guess**. Say which candidates fit, recommend the H3-family one that matches the clip resolution and prompt format, and ask Chinmaya on Slack (template B, need: "default models for story <id>") if the member wants certainty before spending.

Write the defaults into the fix plan as **"Workflow default"**, with the price per unit, so the member sees what you recommend and why.

## If the team member wants a different model

Don't refuse. Warn them once, plainly, before the quote, using this template:

> ⚠️ **<model>** isn't what this story's workflow uses (it used **<default>**). Switching can create new issues: <the risks that apply, e.g. a different look from the neighbouring shots / it re-voices the line instead of copying the audio / a different prompt format / higher cost>. I recommend staying on <default>. Do you still want <model> for scene <n>?

Go ahead only on a clear yes, and log it in the report as "member override". If the override model fails QC, escalate with that context; don't burn retries switching models further.

Known risks worth naming:
- **`minimax_h3_highspeed` / `minimax_h3_max` in `scene_edit_lipsync`** re-voice the line: pitch goes up and timing stretches (a 5.2 s line became 6.7 s) even with the right audio. For an exact copy of the voice, use reference-to-video with `<Audio 1>: fully_copy`, or Sync 3 on an existing clip.
- **Reference-to-video models with no start frame** may re-imagine the scene instead of animating the approved still. Put the still in `reference_image_ids` first, as `<Picture 1>`/`@Image1`, and say the clip begins exactly on it.
- **Non-H3 models** (Seedance, Kling, Wan, Veo, OmniHuman) don't read the H3 six-section prompt. You'd need a different prompt format, and the motion style won't match H3 neighbours.
- **The References tab at 480p** in the web app is the customer's most common self-inflicted cause of lip-sync loss and scene drift.

## Prices (credits) seen in production, November 2026

The Atlabs MCP's `list_models` lists durations and resolutions but **no prices**, so treat this table as a starting point and confirm with a pilot (below).

| Job | Model id (tool) | Res | Rate |
|---|---|---|---|
| Lip sync / dialogue clip, pipeline default for most screenplay stories | `h3_highspeed_reference_to_video` (scene_edit_motion) | 768p only | **1.5 cr/s**, 4–15 s |
| Motion, no dialogue | `h3_highspeed` (scene_edit_motion, start frame) | 768p | 1.5 cr/s |
| Motion / dialogue, H3 standard (rate seen on the Tower story; verify with a pilot) | `minimax_h3_image_to_video`, `minimax_h3_reference_to_video` | "768P" (capital P) | 3 cr/s |
| Motion, H3 Max | `minimax_h3_max_image_to_video` (has end frame, 480/768/1080p, default 480p) | 768p | ~1.7 cr/s at 768p (8 s = 13.6) |
| H3 Max reference | `minimax_h3_max_reference_to_video` | 768p | ~1 cr/s |
| Motion, H3 Lite | `h3_lite` | 768p (2K seen) | ~1 cr/s |
| Lip sync on an existing clip or still | `scene_edit_lipsync` + `minimax_h3_highspeed` | – | ~4–6 cr per clip (min 2 s audio) |
| | `scene_edit_lipsync` + `minimax_h3_pro` | – | ~6 cr per clip (takes < 2 s lines) |
| | `scene_edit_lipsync` + `sync_3` (video only, no prompt) | – | check with a pilot |
| Keyframe edit | story default via `scene_edit_image` (leave `model` out) | 1K | Seedream 5 Pro 1 cr · GPT Image 2.5 Sunburst 1K medium 0.8 cr · Nano Banana Pro 1K 2.5 cr |
| Voiceover line | `scene_edit_voiceover` / `generate_voice` | – | ~0.1 cr per line |
| Split scene, captions, audio routing, trims | – | – | free |

Customer-side models for reference: Seedance 2.5 Ref 3 cr/s, Wan 3.0 Ref 1.2 cr/s, OmniHuman 2.0 1.5 cr/s.

These rates came from real jobs but from different dates and providers, which is why H3 Max can look cheaper than H3 standard. Always confirm with the pilot before quoting a big batch.

Gotchas:
- **Resolution strings are case-sensitive per model:** `minimax_h3_image_to_video` and `minimax_h3_reference_to_video` want `"768P"`; `h3_highspeed*`, H3 Max, Pro and Lite want `"768p"`. A wrong case is refused with the list of valid options.
- A duration between a model's allowed lengths is charged as the next length up.
- H3 models always generate audio, and H3 Max refuses `generate_audio=false`. For non-dialogue clips, say "No dialogue, no voices, no singing, no music" in the prompt and mute the shot audio if needed.
- Retries cost the full price again. Quote with a retry margin.

## How to quote

1. `get_account` gives the balance.
2. For each fix, multiply units by rate: seconds × cr/s for clips, plus each image and VO line.
3. **Pilot:** run the first paid job of each model type alone, after the member says yes to the whole plan. Read `credits_required` or the credits in the submit response and result. If the real rate differs from the table, re-quote the rest before going on.
4. Show the quote as a table: scene, fix, model (workflow default or override), units, first-pass credits, with-retry credits (about +50%). Add the total against the balance.
5. Ask one yes for the batch. Big jobs go in batches (batch 1, QC, then a yes for batch 2).
6. Stop if real spend reaches the approved cap. Ask before going over.

## Billing check (optional, internal access only)

For credit complaints, and to confirm which models the pipeline and the customer actually ran, members with billing-log access use the read-only query in `atlabs-internal.md`. Never change billing data, and never promise refunds. Compensation goes to Chinmaya.
