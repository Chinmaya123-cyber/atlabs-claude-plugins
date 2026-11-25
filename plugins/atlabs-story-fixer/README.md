# Atlabs Story Fixer

A Claude Code plugin that fixes customer Atlabs user stories end to end:

1. reads the story (cloned into your Atlabs account) and its Langfuse session;
2. finds the root cause of each customer issue (keyframe, motion, lip sync, voiceover, audio, captions);
3. recommends fixes on the story's **own workflow default models**, with a credit quote;
4. fixes only after you say yes, piloting one job first;
5. QCs every generation (frames, whisper words, language, voice, sync);
6. sends anything still broken after 3 tries to Chinmaya on Slack, with full details;
7. ends every job with a short Slack DM to Chinmaya: the original story link, the issues, what was fixed and what couldn't be solved;
8. reminds you to **clone the fixed story back into the customer's account**, because the fixes only exist on your copy until you do.

Built for the Atlabs team. It only works with access to Atlabs, the team's Langfuse project and the Atlabs Slack. Customer stories stay confidential: the plugin holds no customer data or internal ids, and those stay in each member's own accounts and in a private notes file (see below).

## Use it in Claude Code

It needs a shell for downloads, ffmpeg and whisper, so it runs in **Claude Code**: the desktop app's **Code** tab, the `claude` CLI, or the VS Code/JetBrains extension. Plain Claude chat can't run the QC.

### Install (once)

```bash
claude plugin marketplace add Chinmaya123-cyber/atlabs-claude-plugins
```

```bash
claude plugin install atlabs-story-fixer@atlabs-internal
```

Or inside a Claude Code session: `/plugin marketplace add Chinmaya123-cyber/atlabs-claude-plugins`, then `/plugin install atlabs-story-fixer@atlabs-internal`. The repo is public, so you don't need a GitHub account.

### Get updates

Chinmaya edits the repo, and you pull the latest:

```bash
claude plugin marketplace update atlabs-internal
```

You can also turn on auto-update for this marketplace in `/plugin` → Marketplaces, so new versions arrive when Claude Code starts.

### Tools you need

The plugin checks these for you on first run and shows the exact setup command if one is missing:
- **Atlabs MCP:** `claude mcp add -s user --transport http atlabs https://mcp.atlabs.ai/mcp`, then `/mcp` → sign in.
- **Langfuse MCP:** ask Chinmaya for keys to the Atlabs project.
- **Internal notes file:** ask Chinmaya on Slack for the story-fixer internal notes and save them as `~/.atlabs-story-fixer/internal.md`. It holds internal ids and queries that are kept out of this public repo.
- **Slack, required.** Connect your own Slack account: claude.ai → Settings → Connectors → Slack → Connect (Atlabs workspace), then restart Claude Code. The skill won't start a fix until Slack works, because every job ends with a summary DM to Chinmaya.
- `ffmpeg` and faster-whisper (in its own venv, because plain `pip3` is blocked on recent Homebrew Python):
  ```bash
  brew install ffmpeg
  ```
  ```bash
  python3 -m venv ~/.story-fixer-venv && ~/.story-fixer-venv/bin/pip install -U faster-whisper numpy
  ```

## Before each story: clone it into your account

The Atlabs MCP only reads stories in your own Atlabs account. For every customer story:
1. Get access to the story (shared with you, or ask Chinmaya).
2. Open it in app.atlabs.ai, signed in to the same account you connected to the Atlabs MCP, and **clone it**. You'll get "[Cloned] <story name>".
3. Give the skill the **clone's** link, the customer's **original story link**, the Langfuse session link and the customer's issues.

## After each story: clone it back to the customer

The fixes are made on **your** clone. When the job is done, clone the fixed story back into the customer's account (open it in app.atlabs.ai and share or clone it into their account), and check it opens there with the new scenes. Only then tell the customer it's fixed. If you can't reach their account, ask Chinmaya.

## Run it

```
/atlabs-story-fixer:fix-story <your clone link> <customer original story link> <langfuse session link> <customer issues>
```

Or just say: "Fix this user story: <links>, the customer says scene 12 lip sync is off and the girl's dress changes in scene 20."

Nothing is spent until you approve the quote.

## What's inside

```
.claude-plugin/plugin.json        plugin manifest (bump "version" on every change)
(marketplace.json lives at the repo root)
commands/fix-story.md             /fix-story slash command
skills/story-fixer/SKILL.md       the workflow
skills/story-fixer/references/    playbook, models & prices, QC, Langfuse, Slack reports, setup
skills/story-fixer/scripts/qc_clip.py   per-clip QC (frame sheets, whisper, VO match, offset)
```

## Maintaining (Chinmaya)

- Edit the files, bump `version` in `.claude-plugin/plugin.json` (the only place the version lives), commit and push. Teammates get it on their next `marketplace update` or auto-update.
- Never commit internal ids, customer data or keys: this repo is public. Internal details go in `~/.atlabs-story-fixer/internal.md`, shared privately.
- Update the price table in `references/models-and-pricing.md` when credit rates change.
- New fix method found? Add a row to the diagnosis table and a recipe to `references/fix-playbook.md`.
