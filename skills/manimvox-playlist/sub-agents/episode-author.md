# The brief for an episode author

One author per episode. The brief is the author's only context; fill every bracket before handing it over.

```text
Write episode [NN] of the "[series]" playlist, in the project folder [series dir].

Read first, in this order:
1. manimvox-core's SKILL.md, then its references/author-guide.md   the rules, the kit API, the lessons
2. [series dir]/SERIES.md    the viewer, the ladder, your beats, the running example
3. [series dir]/FACTS.md     the only claims you may make
4. [earlier finished episode path, if one exists]   pacing and scene variety

Your episode: [NN] · [title] · [level]
File: episodes/[stem].py, class [cls], NCHAP = [n]
Beats: the "[NN]" section of SERIES.md. Episodes before yours taught: [one line
each]. Do not re-teach them; a one-sentence reminder is fine. Episodes after
yours will teach: [one line each]. Do not take their material.

Commands: manimvox draft [stem] --every 5 only. Never run manimvox render; the
orchestrator renders finals. Read every sheet image in sheets/, fix what is
wrong, draft again, until every sheet is clean and the draft prints
"layout check: ok". If you cannot view images, run manimvox check layout [stem]
and fix every finding. Edit only your own file. Install nothing, download
nothing and fetch nothing from the web; if you need something, say so in the report.

Every on-screen or spoken claim must be a line in FACTS.md. If you need a claim
that is not there, find its source, use it labelled, and report it.

Report as the author guide's Report section asks.
```
