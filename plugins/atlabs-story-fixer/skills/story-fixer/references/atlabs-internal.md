# Atlabs internal notes

Team-specific ids, names and queries the skill uses. Shipped with the plugin, so there's nothing extra to set up.

## Slack
- Escalation and summary recipient: Chinmaya, Slack user id `U08FXMN64DB` (Atlabs workspace).

## Langfuse
- Project: "Storymaking", EU cloud, project id `cm9tgzob100isad070dvz85j5`. Keys: ask Chinmaya.
- For pipeline-made stories, the session id is usually the ORIGINAL story id.
- Screenplay flow prompt names (prefix `TEXT_TO_VIDEO/SCREENPLAY/`):
  - `SCREENPLAY_IMAGE_GENERATION` (keyframe prompts)
  - `MOTION_GENERATION` (motion prompts)
  - `LIP_SYNC_GENERATION_V2` (lip-sync prompts; MiniMax H3 six-section format, 4,500-char limit; config `lipsync_model_family: MINIMAX_H3`)
  - `PARSE_SCREENPLAY`, `RE_PARSE_SCREENPLAY`, `CHARACTER_ENRICHMENT`
- Other flow prefixes seen: `CARTOON_FLOW_TEST_A/B/C/...`, `.../MICRODRAMA/...` (these have a `MOTION_MODEL_SELECTION` stage).
- Observation names: motion and lip-sync prompts are both `GENERATE_AI_VIDEO_PROMPT` (tell them apart by promptName). The in-app "Direct this shot" chat is `DIRECT_THIS_SHOT`.

## Billing log (Metabase connector, ProdDB `database_id: 2`)
```sql
select date_trunc('minute', created_at) t, action, service_key,
       round(duration::numeric, 1) dur, credits_used, is_user_regenerated,
       data->>'generation_source' src
from api_userexternalactionlogs
where story_id = '<ORIGINAL story id>'
order by created_at;
```
`src` = WORKFLOW (pipeline) or EDITOR (customer edits). `service_key` looks like `atlabs/runware/h3-highspeed-reference-to-video`. Read only. Never change billing data.

## Confirmed workflow defaults
- Screenplay flow, dialogue clips: `h3_highspeed_reference_to_video`, 768p, 1.5 cr/s (seen in the billing log).
