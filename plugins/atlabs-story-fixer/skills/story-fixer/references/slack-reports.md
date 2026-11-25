# Slack reports to Chinmaya

Chinmaya owns this skill, keeps track of every story fix, and takes the fixes the skill can't handle.
- Slack: **Chinmaya** (Atlabs workspace). Get the user id with `slack_search_users` (`keywords: ["Chinmaya"]`) at setup, or from `atlabs-internal.md`, and save it in the manifest.
- Send a **direct message** to that user id with `slack_send_message` (`channel_id` = the user id), from the member's own connected Slack. Don't post in public channels, because customer stories are confidential.

There are two kinds of message, both sent **automatically once the member has said yes to automatic DMs** (asked once at setup, recorded as `slack_consent: yes` in the manifest). Tell them in one line each time you send one, and show them the text. Without that yes, write the message out in chat for them to send.
- **Escalations** (templates A to C): as soon as an issue gets stuck or access is blocked, during the job.
- **Job summary** (template D): **once at the end of every job**, always. That includes jobs where everything was fixed, partial jobs, jobs the member stopped, and jobs where nothing could be fixed.

## When to escalate

1. **Retry limit hit:** the same issue on the same shot still fails QC after **3 paid attempts** in total. The attempts can mix keyframe fixes, motion and lip sync, so don't reset the count when you switch tool.
2. **No known recipe:** the issue matches nothing in `fix-playbook.md` and you can't name a cause you could test.
3. **Access blocked:** the story isn't in the member's account and they can't clone it, or the Langfuse session can't be read.
4. **Product bug suspected:** a tool refuses inputs that match its documented limits, a credit charge doesn't match the quote by more than 20%, the export breaks, or a generation fails twice with a server error.
5. **Out of scope or needs a decision:** a refund or credit compensation, a script rewrite the customer never asked for, a model outside the workflow defaults that the member insists on, or spend above the approved cap.

Don't escalate for things the member can decide (approve a price, choose between two options). Ask them instead.

## Message templates

Keep it scannable. The Slack tool takes standard markdown: `**bold**`, `_italic_`, bullet lists, links. Don't include customer emails, payment details or anything beyond story ids and the issue.

### A. Issue not fixed

```
:rotating_light: **Story fix needs you**: <story name>
**Original story:** <customer's original story link>
**Clone worked on:** <clone story id>
**Langfuse session:** <session link or "not available">
**Reported by:** <team member name> via story-fixer skill
**Scene / shot:** scene <n> (aroll <id>), <mm:ss in the export if known>
**Customer issue:** <the customer's words, short>
**Workflow / default models:** <workflow name>; image <model>; motion <model, res>; lip sync <model>
**What I tried (<n>/3):**
1. <tool + model + key change>: <credits> cr → <QC result, what was still wrong>
2. ...
**Root cause (best guess):** <one or two lines>
**Why I stopped:** <retry limit / no recipe / tool refusal text / billing mismatch>
**Evidence:** <media ids or local frame paths, whisper words, refusal text>
**Credits spent on this issue:** <n>; **balance now:** <n>
**Suggested next step:** <what you'd try with more access or a different model>
```

### B. Access needed

```
:key: **Story fixer: access needed**
**Team member:** <name>
**Story:** <id or link they gave>
**Need:** <clone of the story into <member>'s Atlabs account / Langfuse session link for this story / Langfuse keys>
**Customer issue (short):** <one line>
```

### C. Langfuse session needed

Same as B with **Need:** "Langfuse session link for story <id>". Mention the story's creation date (from `get_story`) so the session is easy to find.

### D. Job summary (end of every job)

Brief: one line per issue. Link the customer's original story so Chinmaya can open it straight away.

```
:white_check_mark: **Story fix done**: <story name>   (or :warning: **Story fix partly done** / :x: **Story fix blocked**)
**Original story:** <customer's original story link>
**Clone worked on:** <clone story link or id>
**Langfuse session:** <link or "not available">
**Fixed by:** <team member name>
**Workflow / default models:** <workflow>; <image model>; <motion model, res>; <lip-sync model>
**Issues → fixes:**
• Scene <n>: <customer issue, short> → <root cause> → <fix + model> → :white_check_mark: fixed (<attempts> tries, <credits> cr)
• Scene <n>: <issue> → <what was tried> → :x: **not solved**: <why> (escalated / needs decision / not fixable shot by shot)
• Scene <n>: <issue> → skipped: <reason, e.g. member said skip>
**Couldn't solve:** <count>. <one line each, or "none">
**Credits:** quoted <n> · spent <n> · balance now <n>
**Model overrides:** <none / scene n: model X at member's request>
**Customer note:** <one-line plain summary the member can send, if useful>
**Clone back to customer:** pending: <member> reminded to clone the fixed story into the customer's account
**Report:** ~/Downloads/story-fix-<id>/report.md on <member>'s machine
```

Rules:
- Send it even when everything failed or the member stopped early. Then the summary says what state the story was left in.
- If an issue was already escalated with template A, list it as "not solved, escalated earlier" and don't repeat the details.
- No customer emails, payment details or personal data, just story links, issues and fixes.

## After sending

- Tell the member: "I've sent this to Chinmaya on Slack" and show the message text.
- Escalation: put the issue in the final report as **Escalated**, not as fixed, and carry on with the other issues. One escalation doesn't stop the job.
- Summary: add "Summary sent to Chinmaya on Slack" to the end of `report.md`, with the time.
- If a send fails, re-look-up the user id and retry once. If it still fails, write the message in chat for the member to paste.
