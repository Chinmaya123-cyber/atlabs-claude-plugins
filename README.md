# Atlabs Claude Code plugins (internal)

The Atlabs team's Claude Code plugin marketplace. The plugins only work with Atlabs team access.

| Plugin | What it does |
|---|---|
| [`atlabs-story-fixer`](plugins/atlabs-story-fixer) | Fix customer user stories end to end: Langfuse context, root-cause diagnosis, workflow-default models with a credit quote, fix on approval, QC, Slack escalation and a job summary to Chinmaya |

## Install (once per person)

No GitHub account needed. In a terminal (or type the same commands with a leading `/` inside Claude Code):

```bash
claude plugin marketplace add Chinmaya123-cyber/atlabs-claude-plugins
```

```bash
claude plugin install atlabs-story-fixer@atlabs-internal
```

Then follow the 4 setup steps in [the plugin's README](plugins/atlabs-story-fixer/README.md).

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
4. Never commit API keys or customer data.

## Adding a plugin

Add a folder under `plugins/`, with `.claude-plugin/plugin.json` and its `skills/` and `commands/`. Then add an entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<name>"`.
