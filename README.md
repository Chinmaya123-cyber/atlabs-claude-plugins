# Atlabs Claude Code plugins (internal)

The Atlabs team's Claude Code plugin marketplace. The plugins are public, but they only work with Atlabs team access; no internal ids or customer data live here.

| Plugin | What it does |
|---|---|
| [`atlabs-story-fixer`](plugins/atlabs-story-fixer) | Fix customer user stories end to end: Langfuse context, root-cause diagnosis, workflow-default models with a credit quote, fix on approval, QC, Slack escalation and a job summary to Chinmaya |

## Install (once per person)

No GitHub account needed. In a terminal:

```bash
claude plugin marketplace add Chinmaya123-cyber/atlabs-claude-plugins
```

```bash
claude plugin install atlabs-story-fixer@atlabs-internal
```

(Or inside Claude Code: `/plugin marketplace add Chinmaya123-cyber/atlabs-claude-plugins`, then `/plugin install atlabs-story-fixer@atlabs-internal`.)

## Updates

```bash
claude plugin marketplace update atlabs-internal
```

Or turn on auto-update for `atlabs-internal` in `/plugin` → Marketplaces, so new versions arrive when Claude Code starts.

## Changing a plugin

1. Edit the files under `plugins/<name>/`.
2. Bump `version` in `plugins/<name>/.claude-plugin/plugin.json` (the only place the version lives; teammates only get changes after a bump).
3. Run `claude plugin validate .`, then commit and push to `main`.
4. **This repo is public.** Never commit internal ids, customer data or keys; keep them in the private `~/.atlabs-story-fixer/internal.md`.

## Adding a plugin

Add a folder under `plugins/`, with `.claude-plugin/plugin.json` and its `skills/` and `commands/`. Then add an entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<name>"`.
