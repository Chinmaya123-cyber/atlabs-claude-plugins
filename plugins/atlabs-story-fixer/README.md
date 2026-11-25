# Atlabs Story Fixer

A Claude Code plugin for the Atlabs team that fixes customer user stories end to end:

1. reads the story (cloned into your Atlabs account) and its Langfuse session;
2. finds the root cause of each customer issue (keyframe, motion, lip sync, voiceover, audio, captions);
3. recommends fixes on the story's **own workflow default models**, with a credit quote;
4. fixes only after you say yes, piloting one job first;
5. QCs every generation (frames, transcript, language, voice, sync);
6. sends anything still broken after 3 tries to Chinmaya on Slack, with full details;
7. ends every job with a short Slack DM to Chinmaya: the original story link, the issues, what was fixed and what couldn't be solved;
8. reminds you to **clone the fixed story back into the customer's account**.

It runs in **Claude Code** (the Claude desktop app's **Code** tab, or `claude` in a terminal). Plain Claude chat can't run the checks.

## Setup (one time, about 5 minutes)

**1. Add the plugin.** In Claude Code, type these two commands one at a time:

```
/plugin marketplace add Chinmaya123-cyber/atlabs-claude-plugins
```

```
/plugin install atlabs-story-fixer@atlabs-internal
```

Then restart Claude Code.

**2. Sign in to Atlabs.** The plugin already includes the Atlabs connection. Type `/mcp`, pick **atlabs**, choose **Authenticate**, and sign in with your Atlabs account.

**3. Connect Slack.** Go to claude.ai → **Settings** → **Connectors** → **Slack** → **Connect**, and pick the Atlabs workspace.

**4. Langfuse keys.** DM Chinmaya for your keys. The plugin shows you the one command to paste them into the first time you use it.

That's all. The first time you run it, the plugin checks everything and installs its QC tools itself (it asks first).

## Fixing a story

1. Clone the customer's story into **your own** Atlabs account (app.atlabs.ai).
2. In Claude Code, type:
   ```
   /atlabs-story-fixer:fix-story <your clone link> <customer's original story link> <Langfuse session link> <what the customer complained about>
   ```
3. Check the plan and credit quote. Nothing is spent until you say yes.
4. When it's done, clone or share the fixed story back into the customer's account, then tell the customer.

## Updates

```
/plugin marketplace update atlabs-internal
```

Or turn on auto-update for `atlabs-internal` in `/plugin` → Marketplaces.

## What's inside

```
.claude-plugin/plugin.json             plugin manifest (bump "version" on every change)
.mcp.json                              the Atlabs MCP server, so members don't add it by hand
commands/fix-story.md                  /fix-story slash command
skills/story-fixer/SKILL.md            the workflow
skills/story-fixer/references/         playbook, models & prices, QC, Langfuse, Slack reports, setup, team notes
skills/story-fixer/scripts/qc_clip.py  per-clip QC (frame sheets, transcript, language, VO match, offset)
```

## Maintaining (Chinmaya)

- Edit the files, bump `version` in `.claude-plugin/plugin.json` (the only place the version lives), commit and push. Teammates get it on their next update.
- Team ids, Langfuse names and the billing query live in `references/atlabs-internal.md`. Never commit API keys or customer data.
- Update the price table in `references/models-and-pricing.md` when credit rates change.
- New fix method found? Add a row to the diagnosis table and a recipe to `references/fix-playbook.md`.
