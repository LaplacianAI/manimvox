# Inside the heart

<video controls preload="metadata" width="100%" poster="../../assets/heart-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/inside-the-heart.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/inside-the-heart.mp4">Download the video</a>.
</video>

An 80-second explainer for a beginner: what the four chambers of the heart are, and how blood moves through them.

!!! info "Made by Claude Code with manimvox"
    This video was made by an AI agent, [Claude Code](https://claude.com/claude-code), using manimvox's skills and library. A person directed it with a few prompts and reviewed the result. The agent did the research, the facts, the script, the code, the drafts and the render.

## The prompts

These are the prompts that shaped the video, with spelling tidied:

1. *"Give me a short, simple video explaining the various parts of the human heart, with a smooth rotating heart."*
2. *"The graphics are simple. This should be high-quality educational content made at low cost with Manim, so make the diagram cleaner and explain it clearly and briefly, like a professor. Cut it open and properly show the blood flow."*
3. *"Use the internet to download 3D models."*

## What the agent did

1. **Found a real heart.** It searched for an openly licensed model with the inside of the heart, checked the licences, and chose case 18 of a CT-derived four-chamber heart cohort ([Rodero et al. 2021](https://zenodo.org/records/4590294), CC BY 4.0). Its walls, great arteries and valve planes are labelled in the data.
2. **Wrote the facts first.** Every line of narration is in `FACTS.md`, sourced from NHLBI and the Cleveland Clinic. Claims it could not source, such as "the size of a fist", were left out.
3. **Cut the heart open on screen.** It found the classic four-chamber plane from the data itself (through the apex and the centres of the mitral and tricuspid valves), and used `from_pyvista` to render the heart turning and then the cut sweeping in from the front.
4. **Drew the labels and the blood.** `screen_xy` gave each landmark's pixel in the rendered frame, and `Clip.at` turned it into a scene point. Atlas-style labels and streams of blood (blue through the right side to the lungs, red through the left side to the body) are drawn there in Manim.
5. **Checked its work.** It drafted, read the contact sheets and the layout check, fixed overlapping labels and a confusing route, and rendered the final video only when every check passed.

While making it, the agent also extended manimvox: `from_pyvista`, `screen_xy`, `Clip.at` and `Clip.loop` were added for this video, and are now part of the library.

--8<-- "docs/.generated/leaderboard-heart.md"

## Source

The whole project is in [`examples/gallery/heart`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/heart): the episode, its script, the facts, and the script that prepares the CT data. To render it yourself:

```bash
uv tool install "manimvox[kokoro,pyvista]"
python prep_ct.py path/to/18.vtk research/ct
manimvox render ep01
```

## Credits

- **Heart mesh:** Rodero C., Strocchi M., Marciniak M. et al., *Virtual cohort of adult healthy four-chamber heart meshes from CT images*, Zenodo, 2021, [doi:10.5281/zenodo.4590294](https://doi.org/10.5281/zenodo.4590294), CC BY 4.0.
- **Facts:** NHLBI, *How the Heart Works*; Cleveland Clinic, *Heart Chambers*.
- **Voice:** Kokoro (`af_heart`).
- **Made by:** Claude Code with manimvox.
