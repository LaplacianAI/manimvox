---
name: manimvox-animation
description: "Motion patterns for manimvox episodes in Manim: carrying an object from one scene into the next, revealing items as they are named, tables lit row by row, graphs drawn node by node, before and after, zooming into a part, sequence diagrams, 3D scenes with a camera that tilts and orbits (Episode3D) and 3D models from glTF, OBJ or STL files, and recipes for what the kit lacks (coloured words, a plane without LaTeX, live numbers). Use when designing or improving the visuals of an episode."
license: MIT
---

# manimvox animation

How things move in an episode. A scene is picture and voice together, so each pattern below is tied to the line that names what appears. The kit, the stage and the rules for writing an episode are in [manimvox-core](../manimvox-core/SKILL.md); read its author guide first. For what the narration says and how the video is shaped, see [manimvox-creative](../manimvox-creative/SKILL.md).

**[references/patterns.md](references/patterns.md) is the runnable reference.** Each pattern there is a complete chapter that has been run through `manimvox draft` and read on its contact sheets. Paste it in and change the words. The Recipes section of the core author guide names three of these in a line each; `patterns.md` has the full code.

## The patterns

- **Carry an object between scenes.** The same thing is in two scenes: `ReplacementTransform` it, and fade the rest of the stage yourself instead of calling `clear()`, which would take it too.
- **Reveal as named.** A line lists things: `steps(text, [FadeIn(a), FadeIn(b), ...])` shows each as its word is spoken.
- **Table lit row by row.** Read a table one row at a time: set the stroke on `row[0]`, never `Indicate` a row.
- **Graph node by node.** A set of linked things: `gnode` and `gedge` with `steps`, each node arriving with its edges.
- **Before and after.** A change: put the old state down, then `swap` it for the new one in the same place.
- **Zoom into a box.** One part needs detail: fade the others, scale the chosen box up, draw what is inside.
- **Sequence diagram.** A conversation between parts: `lifeline` for each, `message` for each step, replies dashed.
- **Hub and spoke.** One thing linked to many: lines from the hub, sent behind the cards with `set_z_index(-1)`.
- **Recipes for what the kit lacks.** Coloured words by slicing a `Text`, a 2D plane without `Axes`, and a live number from `always_redraw` and a `ValueTracker`. None needs LaTeX.

## 3D

When depth is the idea (a surface, a landscape, vectors in space, stacked layers), subclass `Episode3D` and tilt the camera while a line is spoken. Pin labels to the screen with `pin()`; the kit keeps its header flat and draws every card flat. Use it for one or two scenes, not the whole video. [references/three-d.md](references/three-d.md) has the camera calls, the limits and a drafted pattern. For a real object (an organ, a machine, a building), load a 3D model file (glTF from Blender, OBJ, STL): the `mesh-model` block when Manim's camera should orbit it and the narration points at its parts, or `from_model` for a lit, realistic clip; the same file has both routes.

## Rules for motion

- One idea moves at a time. If two things change in a scene, give each its own line of narration.
- Reveal when the word is spoken, not before. Pass the animations to `say` or `steps`; never hard-code a wait.
- Animate only mobjects that are on stage or are introduced by that same animation, and `.copy()` a mobject rather than putting it in two parents.
- Move a diagram's parts together. `flow()` returns nodes and arrows as separate groups, so `VGroup(nodes, arrows).move_to(...)` moves both.
- An `always_redraw` mobject keeps redrawing until you call `clear_updaters()` on it; stop it before it fades.
- After writing a scene, run `manimvox draft epNN --every 3` and read the contact sheets, or `manimvox check layout epNN` where you cannot view images. A pattern that staged cleanly in `patterns.md` can still collide with your own content.

## Charts and frames from other libraries

`manimvox.scenes` turns frames from Matplotlib, Plotly, Pillow, Cairo or a 3D model into a clip you place and play like any mobject, in the theme's colours: see [references/adapters.md](references/adapters.md). For a simple chart prefer a block (`manimvox add --list`, see [manimvox-blocks](../manimvox-blocks/SKILL.md)) or kit shapes, which reveal part by part as the narration speaks. Use an adapter for what Manim draws badly: dense data, real plots, heatmaps, image processing.
