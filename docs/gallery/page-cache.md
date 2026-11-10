# Why is the same page faster the second time?

<video controls preload="metadata" width="100%" poster="../../assets/page-cache-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/page-cache.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/page-cache.mp4">Download the video</a>.
</video>

A 45-second explainer for anyone who uses the web. The same request makes two trips through four boxes, and the second trip is shorter: the answer was saved in a cache.

!!! info "Made by Claude Code with manimvox"
    This video was made by [Claude Code](https://claude.com/claude-code) (Sonnet 5.5), following manimvox's skills: the brief, a direction, the facts, the script, the code, drafts and the render. A person reviewed the first version, called it confusing, and asked for a real question, flows that match the narration, and a fuller frame.

## The diagram does the explaining

- **Flows that match the voice.** When the narration says the app server asks the cache, the dots go to the cache; when the cache is empty, they go on to the database; the saved copy goes back to the cache in its own colour.
- **Attention moves with the story.** Flows the narration is not talking about fade back, and the database dims on the second trip.
- **Named where they are.** Each part is named by a pointing label, not a box of text.
- **The ending answers the opening,** over the short trip, still flowing.

## Made with

`stream` with `fade_to` and `brighten`, `leader`, `enters` and `leaves`, and the theme's `"style": "calm"`.

## Sources

- Microsoft Azure, [Cache-Aside pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside).
- AWS, [Caching overview](https://aws.amazon.com/caching/).

The video shows one common design, says on screen that real sites differ, and states no timings.

## Source project

The brief, the direction, the facts, the script and the episode are in [`examples/gallery/page-cache`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/page-cache).

**Credits:** made by Claude Code with manimvox. Voice: Kokoro (`af_heart`).
