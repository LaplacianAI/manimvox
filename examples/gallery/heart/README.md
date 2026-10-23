# Inside the heart

An 80-second explainer: a real human heart, rebuilt from a CT scan, is sliced open on screen to its four chambers, and blood is followed through it. [Watch it in the gallery](https://laplacianai.github.io/manimvox/gallery/heart/).

**Made by Claude Code with manimvox.** A person directed it with a few prompts; the agent found the CT data, wrote the facts and the script, wrote this project's code, drafted, checked and rendered it. The prompts, with spelling tidied:

1. *"Give me a short, simple video explaining the various parts of the human heart, with a smooth rotating heart."*
2. *"The graphics are simple. This should be high-quality educational content made at low cost with Manim, so make the diagram cleaner and explain it clearly and briefly, like a professor. Cut it open and properly show the blood flow."*
3. *"Use the internet to download 3D models."*

## Make it

1. Install manimvox with a voice and the 3D extra: `uv tool install "manimvox[kokoro,pyvista]"` (or `pip install "manimvox[kokoro,pyvista]"`).
2. Download case 18 of the CT heart cohort (CC BY 4.0, about 54 MB) from [Zenodo](https://zenodo.org/records/4590294) and unpack it: `tar -xzf 18.tar.gz` gives `18.vtk`.
3. In this folder, prepare it: `python prep_ct.py path/to/18.vtk research/ct`.
4. Draft, look at the contact sheets in `sheets/`, then render:

   ```bash
   manimvox draft ep01
   manimvox render ep01
   ```

The video is `out/ep01_heart.mp4`, with subtitles in `out/ep01_heart.srt`.

## What is where

| File | What it is |
|---|---|
| `episodes/ep01_heart.py` | the episode: the turning heart, the cut, the labels and the blood streams |
| `episodes/ep01_heart.md` | the script, written before the code, with its critique |
| `blocks/heart_ct.py` | the CT heart in PyVista: its walls, landmarks, four-chamber cut and camera |
| `prep_ct.py` | turns the dataset's mesh into the walls and landmarks the episode reads |
| `FACTS.md` | every claim the video makes, with its source |
| `series.json` | the theme (blue for oxygen-poor blood, red for oxygen-rich) and the voice |

## Credits

- Made by: Claude Code with manimvox.
- Heart: Rodero C., Strocchi M., Marciniak M. et al., *Virtual cohort of adult healthy four-chamber heart meshes from CT images*, Zenodo, 2021, [doi:10.5281/zenodo.4590294](https://doi.org/10.5281/zenodo.4590294), CC BY 4.0.
- Facts: NHLBI, *How the Heart Works* (anatomy and blood flow), and Cleveland Clinic, *Heart Chambers*; the links are in `FACTS.md`.
