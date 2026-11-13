# Your footage, edited

<div class="mvx-film" markdown="0">
<video id="tour" controls preload="metadata" playsinline poster="../../assets/editing-tour-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/editing-tour.mp4" type="video/mp4">
  <track kind="subtitles" srclang="en" label="English" src="../../assets/editing-tour.vtt">
  <track kind="chapters" srclang="en" label="Chapters" src="../../assets/editing-tour-chapters.vtt">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/editing-tour.mp4">Download the video</a>.
</video>
</div>

<!-- chapters -->
<ol class="mvx-chapters" data-video="tour">
  <li><a href="?t=0" data-t="0.0"><span class="t">0:00</span> Four broken recordings</a></li>
  <li><a href="?t=38" data-t="38.2"><span class="t">0:38</span> The edit file</a></li>
  <li><a href="?t=109" data-t="109.4"><span class="t">1:49</span> Cut by what is said</a></li>
  <li><a href="?t=220" data-t="219.9"><span class="t">3:39</span> Captions and spellings</a></li>
  <li><a href="?t=301" data-t="300.8"><span class="t">5:00</span> Joining pieces</a></li>
  <li><a href="?t=393" data-t="393.4"><span class="t">6:33</span> Frame and speed</a></li>
  <li><a href="?t=492" data-t="492.0"><span class="t">8:12</span> Over the picture</a></li>
  <li><a href="?t=589" data-t="588.6"><span class="t">9:48</span> Your own code</a></li>
  <li><a href="?t=656" data-t="656.5"><span class="t">10:56</span> Sound</a></li>
  <li><a href="?t=738" data-t="738.2"><span class="t">12:18</span> Colour</a></li>
  <li><a href="?t=809" data-t="809.2"><span class="t">13:29</span> Green screen</a></li>
  <li><a href="?t=880" data-t="879.9"><span class="t">14:39</span> Steady</a></li>
  <li><a href="?t=961" data-t="960.6"><span class="t">16:00</span> Two cameras</a></li>
  <li><a href="?t=1044" data-t="1044.2"><span class="t">17:24</span> Render and share</a></li>
  <li><a href="?t=1111" data-t="1111.2"><span class="t">18:31</span> Back to the four recordings</a></li>
</ol>
<!-- /chapters -->

**manimvox, explaining itself.** This 20-minute film was made end to end by an AI agent with manimvox: the script, the fourteen narrated explainers, the voice, the edit, every fix to the footage. The film is about the tools it was made with.

It is a full tutorial on every editing tool in manimvox 0.8.0 and 0.8.5, for someone who has never written an edit file. Four real, openly licensed recordings arrive broken: an interview with long pauses and an "um", a tower block demolition filmed by a shaking hand, a green-screen shoot, and a street filmed by two cameras. Each chapter fixes one kind of problem, one tool at a time:

1. what the tool does;
2. the line you write in the edit file;
3. the result, full frame;
4. before and after;
5. the mistake people make with it, and what manimvox says about it.

Pick a chapter above to jump to it. Subtitles of every spoken line are under the player's captions button.

!!! info "Made by Claude Code with manimvox"
    This film was made by [Claude Code](https://claude.com/claude-code) (Opus 5.5). It asked who the film was for, chose a storyline with the person, wrote and checked the script, and found openly licensed footage. Then it built each chapter as a narrated explainer and stitched them with the fixes into one edit file. Every terminal line and every error on screen is real manimvox output, captured by running the commands. Making it found and fixed five problems in manimvox (see [What making it fixed](#what-making-it-fixed)).

## Every tool, and its chapter

| Chapter | Tools |
|---|---|
| The edit file | `segments`, `overlays`, `audio`; the two clocks; `manimvox edit probe`, contact sheets; `manimvox check edit` |
| Cut by what is said | `--transcribe`; `from_words`, `to_words`; `cut_silences`, `cut_fillers` |
| Captions and spellings | `captions` (`srt`, `burn`, `none`); `spellings`; levelling |
| Joining pieces | `cut`, `fade`, `dip`; `title`, `image` with `move`, `episode` segments; `from_video(..., sound=True)` |
| Frame and speed | `fit` (`contain`, `cover`, `crop`); `speed`, steady or as keyframes |
| Over the picture | `text` (lower third, title, label), `image`, `clip` (picture-in-picture), `draw`, `scene` overlays |
| Your own code | `frames` segments, `from_moviepy`, `effects` |
| Sound | `say`, `music` with `duck_db`, `sound`; footage levelled under narration |
| Colour | `grade` (exposure, temperature, tint, lift, gamma, gain, contrast, saturation), a `.cube` `lut` |
| Green screen | `key` (`auto`, `similarity`, `softness`, `spill`) |
| Steady | `stabilize` (`smooth`, `zoom`) |
| Two cameras | `manimvox edit sync`, `multicam` (`cuts`, `sound`, `offsets`) |
| Render and share | `--draft`, `--from`/`--to`, `--copy`, `manimvox edit export` (OpenTimelineIO) |

## How it is made

Each chapter is a narrated explainer, rendered by manimvox, that stands on its own like a video in a playlist. It opens by linking back to the chapter before, explains the tool with its edit file beside the raw footage, plays the fix full frame with its sound, shows it before and after, and ends on the common mistake, the takeaway and the next chapter.

Every fix is rendered by one edit file, [`edits/results.json`](https://github.com/LaplacianAI/manimvox/blob/main/examples/gallery/editing-tour/edits/results.json): the cuts, captions, ramps, overlays, grade, key, stabilising and the two-camera cut, with the narration heard over them. Footage sits 18 dB down under narration (`duck_db`), and crowd and street noise stay 8 dB down even when nobody speaks; the interview's own voice is left at full level where her words are the point. The film itself is [`edits/tour.json`](https://github.com/LaplacianAI/manimvox/blob/main/examples/gallery/editing-tour/edits/tour.json), the fourteen explainers joined with fades and a dip between the 0.8.0 and 0.8.5 halves.

Overlay and narration times are seconds of the finished film, so they move whenever a segment's length changes: [`make_edit.py`](https://github.com/LaplacianAI/manimvox/blob/main/examples/gallery/editing-tour/make_edit.py) asks `check edit` where each segment lands and writes both edit files from there.

## What the footage could not show

Both street recordings carry the same soundtrack, sample for sample, so `manimvox edit sync` finds them 0.000 s apart. That's right, but it proves little; the film says so on screen. No openly licensed pair of recordings with separate sound could be found. On separate recordings sync finds the real offset to within 10 ms, as its tests show.

## What making it fixed

- **Ramp keyframes in the wrong clock passed silently.** Keyframes given in the film's seconds missed a clip that starts later in its file, so the ramp never happened. `check edit` now says so.
- **Long films had to download before playing.** MP4s were written with their index at the end. Every MP4 manimvox writes now has its index at the front, so a browser starts playing at once and can seek before the download ends.
- **Damaged packets stopped the read.** The chroma-key film has 96 damaged Theora packets, and reading stopped at the first. Frames are now read past a damaged packet.
- **`"auto"` keyed the ground.** On a low-angle shot, `key: "auto"` took the backing's colour from a border that was mostly grass. It now takes the clearly green or blue pixels round the border.
- **A Commons credit kept the talk link.** The credit kept the "(leave a reply)" link from the uploader's signature.

## Source project

The script, the direction, the facts, every explainer and the edit files are in [`examples/gallery/editing-tour`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/editing-tour), with how to render it yourself.

**Credits:** UNESCO-IHE Archive, ["Interview Prof Joyeeta Gupta on strengthening water governance education and research"](https://commons.wikimedia.org/wiki/File:Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm) (2013), CC BY 3.0. Laerol, ["Dundee Alexander Street Hilltown Multis Demolition 2011"](https://commons.wikimedia.org/wiki/File:Dundee_Alexander_Street_Hilltown_Multis_Demolition_2011.webm), CC BY-SA 4.0. Pixelmaniac pictures, ["Chroma key demonstration"](https://commons.wikimedia.org/wiki/File:Chroma_key_demonstration.ogv) (2014), public domain. Albin Olsson, ["Urilift, Göteborg, Kungsportsplatsen"](https://commons.wikimedia.org/wiki/File:Urilift,_G%C3%B6teborg,_Kungsportsplatsen_-_angle_1.webm), angles 1 and 2 (2014), CC BY-SA 3.0. All from Wikimedia Commons. Made by Claude Code with manimvox. Voice: Kokoro (`af_heart`). Music and whoosh synthesised for the film. The film is CC BY-SA 4.0.
