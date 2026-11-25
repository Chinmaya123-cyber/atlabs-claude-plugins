# Setup and access check (Step 0)

Run this check before anything else. Do as much of it yourself as you can (run the install commands for the member after a quick OK), so they have as few steps as possible.

Team ids, Langfuse names and the billing query are in `atlabs-internal.md` in this folder; read it now.

If a session shows two Atlabs servers (e.g. the plugin's own `atlabs` server and an older `claude mcp add` one), use one consistently: the one whose `get_account` email is the member's.

Atlabs MCP and Slack are required. Langfuse is strongly recommended. Don't start diagnosing until they work, or the person has agreed to go on without one.

## 1. Atlabs MCP (required)

Test: call `get_account`. It should return the account's email and credit balance.

This plugin ships the Atlabs MCP server, so there's nothing to install. If `get_account` fails or the Atlabs tools aren't there, the member only needs to sign in once: type `/mcp`, pick the **atlabs** server (listed under this plugin), choose **Authenticate**, and sign in with their own Atlabs account. If there's still no Atlabs server, they restart Claude Code once after installing the plugin.

**Story access: clone first (required).** The Atlabs MCP can only open stories in the account it's signed in to. Every team member must **clone the customer's story into their own Atlabs account** before the skill can read it, even when the story is shared with them.

1. Get access to the customer's story (shared with the member, or ask Chinmaya).
2. Open it in app.atlabs.ai while signed in to the **same account the MCP uses** (`get_account` shows which email that is), and clone it. The copy appears as "[Cloned] <story name>" with a new story id.
3. Give the skill the clone's link or id.

Test: `get_story(<clone id>)` returns the story. If it says not found or forbidden:
- run `list_stories` and look for "[Cloned] <story name>". The member may have pasted the original's id;
- check the clone was made in the same account the MCP is signed in to, not a second Atlabs login;
- if they can't get access or clone it, escalate to Chinmaya with the "access needed" Slack template in `slack-reports.md`.

Always work on the clone and never on the customer's original.

## 2. Langfuse MCP (strongly recommended)

The Langfuse session for the story holds the real pipeline context: which workflow ran, which models, the exact system prompts and their versions, the script, cast and scene data, and every "Direct this shot" round the customer tried.

Test: call the Langfuse `getHealth` tool, then `listObservations` filtered by the session id (see `langfuse-context.md`).

If the Langfuse tools are missing, the person needs a Langfuse API key pair for the Atlabs project (EU cloud). They ask Chinmaya for keys, then run:

```bash
claude mcp add -s user --transport http langfuse https://cloud.langfuse.com/api/public/mcp --header "Authorization: Basic $(printf '%s' 'PK:SK' | base64)"
```

(They replace PK:SK with their public and secret key, joined by a colon, then restart Claude Code.)

**Session link.** The person gives a link like
`https://cloud.langfuse.com/project/<project_id>/sessions/<session_id>`. The last path part is the session id. If they have no session link for this story, or their keys can't read it, send Chinmaya the "Langfuse session needed" message (template C in `slack-reports.md`, automatic like every Slack report), then carry on with Atlabs-only diagnosis. Tell them the fix plan is less certain without the session.

## 3. Slack (required)

Every job ends with a summary DM to Chinmaya, and stuck issues are escalated there. The member's **own** Slack account must be connected so the messages come from them.

Test: `slack_search_users` with `keywords: ["Chinmaya"]` and `natural_language_query: "Chinmaya at Atlabs"`. It should return Chinmaya in the Atlabs workspace. Use that user id as the DM `channel_id` (`atlabs-internal.md` also lists it).

If there are no Slack tools, or the search fails, **stop and ask the member to connect Slack** before going further:

> To run this skill, connect your Slack account so I can send Chinmaya the job summary and any issues I can't fix:
> 1. Go to **claude.ai → Settings → Connectors**, find **Slack** and click **Connect**.
> 2. Sign in to the **Atlabs** Slack workspace and allow access.
> 3. Restart Claude Code (or start a new session), then tell me "Slack connected".
>
> Claude Code picks up your claude.ai connectors when it's signed in with the same claude.ai account (check `/mcp` for a Slack entry). If Slack isn't offered under Connectors, your org admin has to enable it; tell Chinmaya.

Then re-test. If they say they can't connect today, carry on, but write every Slack message (summary and escalations) out in full in chat so they can paste it to Chinmaya. Mark it "Slack not connected, sent manually" in the report.

## 4. Local tools for QC (recommended)

QC uses `ffmpeg`/`ffprobe` for frame grabs and audio checks, and **faster-whisper** in its own virtual environment for transcripts, language detection and word timestamps. (A plain `pip3 install` fails on recent Homebrew Python, which is "externally managed", so always use the venv.)

Check: `which ffmpeg ffprobe` and `~/.story-fixer-venv/bin/python -c "import faster_whisper, numpy"`. If either fails, **offer to run the install yourself** ("I need to install ffmpeg and a speech checker for QC, about 2 minutes. OK?"), and on yes run:

```bash
brew install ffmpeg
```

```bash
python3 -m venv ~/.story-fixer-venv && ~/.story-fixer-venv/bin/pip install -U faster-whisper numpy
```

If Homebrew itself is missing, ask the member to install it from https://brew.sh first. The first transcription downloads the whisper model (small ≈ 0.5 GB, large-v3 ≈ 3 GB). Without these tools, QC falls back to `show_media` and visual review only; say so in the QC report.
