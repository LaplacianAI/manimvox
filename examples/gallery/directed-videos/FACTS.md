# Why every video looked the same: facts

Source: PR #37, https://github.com/LaplacianAI/manimvox/pull/37, "feat: directed videos, not templates", head commit 2f0eb49a2976efe05e218192e040394cf1a0ab14, base main. "main:" paths are the removed/old side of the diff, "head:" paths the new lines. Commits: 55b9986 `feat(kit): directed openings, transitions and grounds, all opt-in`; 4559ff6 `feat(blocks): kinetic-title, end-card and transitions-demo`; 2f0eb49 `docs(skills): a direction step before any scene`.

Labels: [SOURCE] stated by the PR; [BUILT] exists in the code at the head; [OPEN] not stated.

## The problem (old shape)
- [SOURCE] Every manimvox video had the same skeleton: one title card, faded "01" chapter numerals, a header and progress bar on every frame, everything clearing to the left, recap bullets, and a still end card. — PR description
- [BUILT] Old intro always cleared the stage (sweeping any cold open) and drew the title card: `def intro(self, narration, tts=None, question=None)` then `self.clear()`. — main:src/manimvox/kit/episode.py:169,173
- [BUILT] Old chapter always cleared with the default sweep and drew a faded numeral: `num = T(f"{self._chap_i:02d}", 150, ACCENT, BOLD).set_opacity(0.16)`. — main:src/manimvox/kit/episode.py:231,234
- [BUILT] Old outro drew a "Recap" heading and bullets: `h = heading("Recap") if recap else None`. — main:src/manimvox/kit/episode.py:280
- [BUILT] Old intro always added the header label and progress bar ("persistent chrome"). — main:src/manimvox/kit/episode.py:197-207
- [SOURCE] The brief already asks for openings like "straight in, no title card", but no code path honoured them. — PR description

## What changed (kit, all opt-in)
- [BUILT] `intro(..., card=True)` gained a `card` parameter. — head:src/manimvox/kit/episode.py:194
- [BUILT] With `card=False` there is no card and no motif; the cold open stays on screen and the title arrives as kinetic type over it, word by word. — head:src/manimvox/kit/episode.py:195-199,254-262
- [BUILT] `CHROME = ("label", "bar")` is a class attribute; `CHROME = ()` gives a frame with no header label or progress bar. — head:src/manimvox/kit/episode.py:86,235,243
- [BUILT] `chapter(..., transition=None, keep=(), number=True)`: transition (blur, down, dip, zoom_through, flood, iris, whip), objects kept across the seam, numeral on or off. — head:src/manimvox/kit/episode.py:279-280
- [BUILT] `outro(..., end=None)`: a built end card of up to 3 lines, typed in word by word with a rule wiped in. — head:src/manimvox/kit/episode.py:339-340,389-398
- [BUILT] New motion helpers: `words_in`, `letters_in`, `blur_in`, `slot`, `accent_word`; `zoom_through`, `flood`, `iris`, `whip`, `morph`, `dip`, `carry`. — head:src/manimvox/kit/motion.py:92,100,108,113,125,151,170,183,195,209,214,225
- [BUILT] Theme `ground` of kind solid, grain, grid or paper. — head:src/manimvox/kit/ground.py:25 (grid), PR description
- [SOURCE] Defaults are unchanged, so existing episodes render exactly as before. — PR description
- [SOURCE] A test compares the layout output with the options left out and with the defaults spelled out. — PR description (tests/test_directed.py)
- [BUILT] `check layout` warns when all chapter seams use the same explicit transition (3 or more chapters). — head:src/manimvox/checks/layout.py:74-78
- [SOURCE] Three blocks were added: `kinetic-title`, `end-card`, `transitions-demo`. — PR description; commit 4559ff6

## Skills
- [SOURCE] New skills/manimvox-creative/references/direction.md: three storylines first, one recommended; then DIRECTION.md with a look from one medium, motion timings by role, opening and ending shots, a transition per chapter seam, and a BANNED list. — PR description
- [SOURCE] All four workflow skills run the direction step after the brief. — PR description
- [BUILT] The direction file is at head:skills/manimvox-creative/references/direction.md (Step 1, Step 2, BANNED at lines 5, 20, 41).

## Real frames used on screen (research/screens/)
- [SOURCE] old-a-title.png, old-a-chapter.png, old-a-recap.png: frames of the gallery video "Made by your agent", made with the old kit. https://github.com/LaplacianAI/manimvox/releases/download/gallery/made-by-your-agent.mp4
- [SOURCE] old-b-title.png, old-b-chapter.png, old-b-ending.png: frames of the gallery video "Install manimvox and make a video", made with the old kit. https://github.com/LaplacianAI/manimvox/releases/download/gallery/install-tutorial.mp4
- [SOURCE] new-open.png, new-middle.png, new-ending.png: frames of the gallery video "How a hash map finds a key", made with this PR. https://github.com/LaplacianAI/manimvox/releases/download/gallery/hash-map.mp4
- The two old videos' endings differ in kind (a Recap list, an answer with a link); the narration says "the same kind of ending".
- The calls shown on screen (`intro(card=False)`, `chapter(card=False, transition=iris(...))`, `outro(keep=[...])`) are schematic: the parameters are those of the head signatures above and commit 9b8f6b5; the argument values ("Title", "...", `box`, `shelf`) are placeholders.

## Direction step (skills)
- [SOURCE] The agent writes a direction before any scene: three storylines (one recommended), a look from one medium, a transition per chapter seam, a BANNED list of tells. — head:skills/manimvox-creative/references/direction.md, PR description

## Open
- [OPEN] The PR does not state test coverage or risk beyond its Tests section; the video states neither.
- [OPEN] Not yet done, per the PR: an end-to-end comparison of two real videos made with the new direction step.
