# What lets a loaded wheel turn so freely?

<video controls preload="metadata" width="100%" poster="../../assets/tapered-bearing-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/tapered-bearing.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/tapered-bearing.mp4">Download the video</a>.
</video>

A one-minute explainer for a curious non-engineer. A car wheel carries the whole car and still spins freely: the answer is a ring of slanted rollers between the axle and the wheel.

!!! info "Made by Claude Code with manimvox"
    This video was made by [Claude Code](https://claude.com/claude-code) (Sonnet 5.5), following manimvox's skills: the brief, a direction, the facts, the script, the code, drafts and the render. A person reviewed it and sent it back three times: the first version was an edge-on slice with no context, then the bearing lay on its side so the weight pointed the wrong way, then the close-up lost the ring.

## A real part, cut open

- **From the wheel to the part.** It opens on a wheel and its axle, shows where the bearing sits between them, then brings the real bearing out, standing upright as it does in the wheel.
- **A quarter cut, one camera.** A 90° wedge is removed, so the outside and the inside show together, and the camera that watched the bearing turn is the one that looks into the cut, so the viewer never loses their place.
- **Steel and one accent.** The metal is steel grey; only the part being named, or the roller carrying the weight, turns orange.
- **The mechanism.** The weight goes down through a roller, a turn pushes sideways along the axle, and a simplified drawing shows why the rollers are tapered: their lines meet at one point on the axle, so they roll instead of sliding.
- **The ending answers the opening,** over the wheel it began with.

## Made with

`Cutaway` from `manimvox.scenes` with `axis=` for the quarter cut and one shared camera for `turning`, `sweep` and `opened`; `leaders` for the names; `manimvox assets` to fetch the model with its licence and credit.

## Sources

- Wikipedia, [Tapered roller bearing](https://en.wikipedia.org/wiki/Tapered_roller_bearing) and [Rolling-element bearing](https://en.wikipedia.org/wiki/Rolling-element_bearing).
- Schaeffler, [Tapered roller bearings](https://medias-at.schaeffler.com/en/tapered-roller-bearings) (the rollers' lines meeting at one point on the axis).

## Source project

The brief, the direction, the facts, the script and the episode are in [`examples/gallery/tapered-bearing`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/tapered-bearing).

**Credits:** made by Claude Code with manimvox. Model: Dape13, ["Bearing with Tapered Roller"](https://commons.wikimedia.org/wiki/File:Bearing_with_Tapered_Roller.stl), Wikimedia Commons, CC BY-SA 4.0. Voice: Kokoro (`af_heart`). Because it adapts a CC BY-SA model, this video is licensed CC BY-SA 4.0.
