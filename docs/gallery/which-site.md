# Which site am I on?

<video controls preload="metadata" width="100%" poster="../../assets/which-site-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/which-site.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/which-site.mp4">Download the video</a>.
</video>

A 40-second explainer for anyone who uses a browser. A page can write its own tab title, but not the address bar: the domain there, and the shield beside it, tell you where you really are.

!!! info "Made by Claude Code with manimvox"
    This video was made by [Claude Code](https://claude.com/claude-code) (Sonnet 5.5), following manimvox's skills: the brief, a direction, the facts, the script, the code, drafts and the render. A person reviewed the first version, which labelled a frame of manimvox's own video, called it confusing, and asked for a real interface and a real question.

## A real screenshot, named part by part

- **The real window, from the first frame to the last.** A Firefox screenshot from Wikimedia Commons, fetched with `manimvox assets`, which read its licence and recorded the credit shown on screen.
- **The part that matters, lifted out.** The strip at the top comes out of the window at full width, so its parts are big enough to read.
- **Named in the order they are explained:** the tab, the address bar, the domain, the shield, each with a pointing label in a row above or below the strip.
- **The ending answers the opening,** over the whole window with the address bar outlined.

## Made with

`screenshot` from `manimvox.scenes`, `leaders` with `side="above"` and `side="below"` placed with `clip.at(x, y)`, and `manimvox assets`.

## Sources

- Mozilla Support, [How do I tell if my connection to a website is secure?](https://support.mozilla.org/en-US/kb/how-do-i-tell-if-my-connection-is-secure)
- MDN, [What is a URL?](https://developer.mozilla.org/en-US/docs/Learn_web_development/Howto/Web_mechanics/What_is_a_URL) and [`<title>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/title).

The video says "encrypted", never "safe".

## Source project

The brief, the direction, the facts, the script and the episode are in [`examples/gallery/which-site`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/which-site).

**Credits:** made by Claude Code with manimvox. Screenshot: Exploraz, ["Firefox 157.0 opening Wikipedia article on Linux screenshot"](https://commons.wikimedia.org/wiki/File:Firefox_157.0_opening_Wikipedia_article_on_Linux_screenshot.png), Wikimedia Commons, CC BY-SA 4.0; Firefox by the Mozilla Foundation, the page by the Wikimedia Foundation. Voice: Kokoro (`af_heart`). Because it adapts a CC BY-SA screenshot, this video is licensed CC BY-SA 4.0.
