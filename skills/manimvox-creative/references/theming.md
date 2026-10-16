# Theming a series

A viewer learning a subject should see that subject's own colours: a node that is blue on the product's screen is blue in the video, and the accent is the brand's accent. manimvox has no presets. Build the theme for each video from the request and the topic, put it in `series.json` under `theme`, and check it.

## Where to look, in order

Take the first source that has an answer for a role, and record what you used in `source`.

1. **The user's explicit request.** "Dark chalkboard", "our brand blue", "like this channel". It wins over everything below.
2. **The subject's own brand.** A brand file, `brand/`, a design-system package, design tokens (CSS custom properties in `:root` or `.dark`, a Tailwind config, `tokens.json`), a logo. These are usually what the product's interface copies. `oklch()` values must be converted to `#RRGGBB`.
3. **The subject's domain colours.** A status colour, a node kind on a graph page, a chart series, the colours of a paper's figures. Search for hex values next to domain words. These go under `named`, because the video draws the same entities.
4. **Mood from topic and audience.** When there is no brand, choose by what the viewer needs, and say so in `source`. Examples:
   - mathematical intuition: a dark chalkboard stage with a few saturated colours, one per object, kept the same all video;
   - policy or finance: calm neutrals and a single restrained accent, so nothing looks like an alarm;
   - a security post-mortem: high contrast, `error` and `warn` kept for what failed and what was exposed;
   - a children's or beginner topic: warmer hues and more of them, with the same contrast limits.
5. **The kit's neutral dark default.** If nothing above applies, leave the roles out. `manimvox check theme` prints a note that they come from the default, and `source` should say "kit neutral default".

Videos are dark. If a brand has only a light theme, keep its accent and hues, take the kit's dark neutrals, and say so in `source`.

## The roles

`bg panel panel2 line ink muted accent ok warn error code_bg blue orange violet pink teal named`. Roles you leave out fall back to the kit's neutral dark values, except `code_bg`, which falls back to your `bg`.

| Role | Take | Used for |
|---|---|---|
| `bg` | page background | the stage |
| `panel` | card or surface | boxes, cards, table rows |
| `panel2` | one step above `panel` | headers, icon fills |
| `line` | border | outlines, connectors at rest |
| `ink` | body text | text |
| `muted` | muted text | captions, labels |
| `accent` | primary or brand accent | "the point", progress bar, selection |
| `ok` `warn` `error` | success, warning, destructive | allowed, a limit, refused |
| `code_bg` | a shade darker than `bg` | code panels |
| `blue orange violet pink teal` | the chart palette, or harmonised hues | things with no role of their own |
| `named` | domain colours | `{"agent": "#3987E5"}` becomes `AGENT` in scenes |

Colours are `#RRGGBB`, six digits. A `named` key must not be a name Manim already has (`red`, `blue`, `gold`): it would replace Manim's colour, and the check refuses it. Keep the meaning of a colour the same in every episode.

Also set `source` (one sentence on where the values came from), and when needed `font`, `mono`, `font_files` and `mark_svg`.

## Fonts

- Pango must be able to see the font. Without a `font` or `mono`, the theme uses fonts every install of that OS has, so the default is always safe.
- Pango loads TTF and OTF only. A package that ships web fonts (woff or woff2) will not work.
- A font file already in the project or on the machine goes in a `fonts/` folder with its licence file, and is listed under `font_files`. Copy Regular, Bold and Italic: `note()` is italic.
- Downloading a font is a download: ask the user first, naming the font and where it comes from. If you cannot ask, do not download; use a font already installed and say so in the report.
- Change fonts before the finals, never after. A new font changes every text width, so every episode must be drafted again and its sheets looked at again.

## The mark

A logo goes in `mark_svg`, a path to an SVG file. Manim's SVG parser ignores `<style>` blocks and `prefers-color-scheme`, so use a copy of the logo with its colours written inline (`fill="..."`, `stroke="..."`). The kit draws it on the title card in a tint of the accent, keeping outlines unfilled. Look at the title card in the first draft: an outline that came out filled, or edges showing through shapes, means the copy is wrong. Read the logo file's comments too; brand rules in them ("never on a circle") apply to the video.

## Check

Run `manimvox check theme`. It must print `theme check: ok` before any episode is drafted. It reports:

- **Text roles** (`ink muted accent ok warn error`): contrast of at least 4.5:1 on both `bg` and `panel`. A line such as `accent: contrast 3.10 on bg, 3.40 on panel; text needs 4.5` means that colour is too dim to read.
- **Hues and named colours** (`blue orange violet pink teal` and everything in `named`): contrast of at least 3:1 on `bg`.
- **Fonts:** `font`, `mono` and each file in `font_files` must load in Pango.
- **Colour format and names:** every value is `#RRGGBB`, and no `named` key shadows a Manim colour.
- **Source:** `source` is not empty.

If the subject's own palette fails, lighten the colour for the video and record that in `source`, for example "brand accent #2A6FDB lightened to #5B93E8 for contrast". Do not silently swap a brand colour. The output is explained in [manimvox-cli](../../manimvox-cli/SKILL.md).

## Brand rules that reach the video

Read the brand rules and apply those that touch text, the mark or colour use. The kit prints the series name exactly as `series.json` writes it. A brand can forbid capitals: write the series name exactly as the brand does, for example `"acme runtime, explained"` in lowercase, and fix the spoken form with `pron` (see [manimvox-voice](../../manimvox-voice/SKILL.md)). The same goes for other rules, such as a forbidden colour pairing or a required clear space around the mark.

## Worked example: in the spirit of 3Blue1Brown

For a video on mathematical intuition, the request was a look like the 3Blue1Brown channel. This is a style reference, not their official palette. It is the example in the README (Configuration, Themes), and it passes `manimvox check theme`:

```json
"theme": {
  "source": "in the spirit of 3Blue1Brown: near-black stage, Manim's blue, yellow, green and red",
  "bg": "#0E1113", "panel": "#1A1F24", "panel2": "#252B31", "line": "#3A434B",
  "ink": "#ECECEC", "muted": "#A3ABB2", "accent": "#58C4DD",
  "ok": "#83C167", "warn": "#FFFF00", "error": "#FC6255",
  "blue": "#58C4DD", "orange": "#FF862F", "violet": "#9A72AC", "pink": "#D147BD", "teal": "#5CD0B3",
  "named": { "vector_i": "#83C167", "vector_j": "#FC6255" }
}
```

How it was derived: the colours come from Manim's own palette (its light blue, green, red and orange), because that is what the channel's look is built from. The stage is a near-black rather than pure black, with panels a step lighter, so cards show without heavy outlines. Yellow is kept for `warn` because on a dark stage it reads as "look here". The two `named` colours give the basis vectors of a linear-algebra video a fixed colour that never changes between scenes. Every value was run through `manimvox check theme`, which is the only judge of whether it is readable.

## Worked example: a product with a brand file

A video explains a product whose repository has a brand file and a logo.

1. Read the brand file. It names a primary blue, a background and a rule that the wordmark is always lowercase.
2. Find the dark mode in the design tokens. Convert any `oklch()` values to hex. Map: page background to `bg`, card to `panel`, the step above to `panel2`, border to `line`, body text to `ink`, muted text to `muted`, primary to `accent`, and the success, warning and destructive tokens to `ok`, `warn`, `error`.
3. Search the product's interface for the colours of its own entities, such as an agent, a queue, a policy. Put them under `named` with the entity's name.
4. Take `font` and `mono` from the interface's CSS. Check Pango sees them. If the font is not installed and the files are not in the project, ask before downloading; if you cannot ask, leave `font` out and use the OS default.
5. Copy the logo to `mark.svg` with inline colours and set `mark_svg`.
6. Write the series name as the brand writes it, and add `pron` pairs where that changes how it is said.
7. Run `manimvox check theme`. Lighten any colour that fails and record it in `source`. A sentence such as "dark tokens from the brand file; entity colours from the interface; accent lightened for contrast" is enough.
