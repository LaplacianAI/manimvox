# Which site am I on?

A 40-second explainer for anyone who uses a browser: on a real Firefox window, the strip at the top lifts out and its parts are named in turn (the tab, the address bar, the domain and the shield) until the answer is clear: the domain in the address bar, and the shield beside it. It is also a test of manimvox's pointing labels on a real screenshot (`leaders` with `side="above"` and `side="below"`, placed with `clip.at(x, y)`) and of `manimvox assets`.

**Made by Claude Code with manimvox,** following the skills: the brief, three storylines in `DIRECTION.md`, the facts, the script, the code, drafts and the render. A person reviewed the first version, called it confusing, and asked for a real interface and a real question instead of a frame of manimvox's own video. This is the rebuilt version.

## Make it

1. Install manimvox with the offline voice: `uv tool install "manimvox[kokoro]"` (or `pip install "manimvox[kokoro]"`).
2. The screenshot is not committed. Fetch it once from this folder; `manimvox assets` reads its licence from Wikimedia Commons, checks the file and records the credit in `research/assets.json` and `FACTS.md`:

   ```bash
   manimvox assets add https://commons.wikimedia.org/wiki/File:Firefox_157.0_opening_Wikipedia_article_on_Linux_screenshot.png -y
   manimvox render ep01
   ```

The video is `out/ep01_address.mp4`, with subtitles in `out/ep01_address.srt`. The credit line on screen is read from `research/assets.json`.

## What is where

| File | What it is |
|---|---|
| `episodes/ep01_address.py` | the episode: the window, the strip lifted out and named, the answer over the window |
| `episodes/ep01_address.md` | the script, written before the code |
| `BRIEF.md`, `DIRECTION.md` | the brief, three storylines, the chosen look and the BANNED list |
| `FACTS.md` | every claim, with its source, and what the video does not claim |
| `research/assets.json` | the screenshot's source, licence, checksum and credit line |
| `series.json` | the paper theme and the voice |

## Credits and licence

- Made by: Claude Code with manimvox. Voice: Kokoro (`af_heart`).
- Screenshot: Exploraz, ["Firefox 157.0 opening Wikipedia article on Linux screenshot"](https://commons.wikimedia.org/wiki/File:Firefox_157.0_opening_Wikipedia_article_on_Linux_screenshot.png) (2026), Wikimedia Commons, CC BY-SA 4.0. Firefox: Mozilla Foundation. Page: Wikimedia Foundation.
- Facts: Mozilla Support, [How do I tell if my connection to a website is secure?](https://support.mozilla.org/en-US/kb/how-do-i-tell-if-my-connection-is-secure); MDN, [What is a URL?](https://developer.mozilla.org/en-US/docs/Learn_web_development/Howto/Web_mechanics/What_is_a_URL) and [`<title>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/title). The video says "encrypted", never "safe".
- The video adapts a CC BY-SA 4.0 screenshot, so **the video is licensed CC BY-SA 4.0**. The code in this folder is MIT, like the rest of manimvox.
