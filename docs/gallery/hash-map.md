# How a hash map finds a key

<video controls preload="metadata" width="100%" poster="../../assets/hash-map-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/hash-map.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/hash-map.mp4">Download the video</a>.
</video>

A one-minute concept video for beginner programmers. A dict does not search a shelf of boxes: it turns the key into a shelf number and jumps straight there.

!!! info "Made by Claude Code with manimvox"
    This video was made by [Claude Code](https://claude.com/claude-code) (Sonnet 5.5), following manimvox's skills end to end: the brief, a direction, the facts, the script, the code, drafts, a review of its own tells, and the render. A person reviewed each render and asked for revisions: a bigger shelf, no chapter cards, no dead air, and every step shown rather than said.

## A directed video

It is the first gallery video made with the direction step: before any scene, the agent wrote three storylines, chose one, and fixed a look, a transition for each chapter seam and a list of banned tells in `DIRECTION.md`. So it does not look like the others:

- **No title card.** Frame 0 is the subject: a shelf of eight boxes searched one by one, counting the looks. The title types in over it.
- **Paper and ink.** A light paper ground, rust for the slow search, blue ink only for what is being named.
- **One object throughout.** The same shelf is searched, addressed, crowded by two keys, and brought back to its opening place for the answer.
- **Chapters without cards.** Each chapter goes straight into the picture through an iris, a whip or a colour flood, spoken over as it plays, so there is no dead air.
- **Shown, not said.** The remainder is division with something left over (`7401935 = 8 × 925241 + 7`), the value lives in its box, and two keys in one box are told apart by a check.
- **The ending answers the opening.** The question is answered over the opening's shelf: 8 looks become 1.

## The prompt

*"Make a ~70 second concept video: how does a hash map find a key so fast? For a beginner programmer."*

The brief: for beginner programmers who use dicts; open on the problem happening; end by answering the opening; a light, paper-and-ink look.

## Sources

- The Python documentation: [`hash()`](https://docs.python.org/3/library/functions.html#hash), [hashable](https://docs.python.org/3/glossary.html#term-hashable).
- General hash-table design (linear search, the division method, collisions), labelled external: Cormen et al., *Introduction to Algorithms*, chapter 11.

The keys, values and the hash number are an invented example, marked on screen.

## Source project

The brief, the direction, the facts, the script and the episode are in [`examples/gallery/hash-map`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/hash-map).

**Credits:** made by Claude Code with manimvox. Voice: Sarvam AI Bulbul v3 (`shubh`).
