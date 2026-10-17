from fractions import Fraction
from pathlib import Path

import av
import numpy as np
import pytest
import soundfile as sf

from manimvox.checks.audio import Cue
from manimvox.kit.theme import Theme
from manimvox.playlist import duration
from manimvox.post.audio import RATE, gain, read_audio
from manimvox.post.draw import caption_overlay, card_image
from manimvox.post.encode import Writer, video_info
from manimvox.post.finish import concat, finish, srt_text
from manimvox.post.options import PostError, PostOptions
from tests.media import make_mp4

TH = Theme.from_dict({"source": "test"})


def rms(x):
    return float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0


def frames_at(path):
    with av.open(str(path)) as c:
        s = c.streams.video[0]
        return [(float(f.pts * s.time_base), f.to_ndarray(format="rgb24")) for f in c.decode(s)]


def test_writer_pads_audio_to_the_video(tmp_path):
    o = tmp_path / "o.mp4"
    w = Writer(o, (64, 36), 10)
    w.audio(np.zeros((2, RATE), np.float32))  # 1 s of sound
    for _ in range(20):  # 2 s of picture
        w.add(np.zeros((36, 64, 3), np.uint8))
    w.close()
    assert duration(o) == pytest.approx(2.0, abs=0.15)
    assert read_audio(o).shape[1] / RATE == pytest.approx(2.0, abs=0.1)


def test_writer_cuts_audio_longer_than_the_video(tmp_path):
    o = tmp_path / "o.mp4"
    w = Writer(o, (64, 36), 10)
    w.audio(np.full((2, 3 * RATE), 0.1, np.float32))
    for _ in range(10):
        w.add(np.zeros((36, 64, 3), np.uint8))
    w.close()
    assert read_audio(o).shape[1] / RATE == pytest.approx(1.0, abs=0.1)


def test_end_card_is_appended_on_the_theme_background(tmp_path):
    src = make_mp4(tmp_path / "s.mp4", 2.0)
    dst = tmp_path / "d.mp4"
    lines = finish(src, dst, [], PostOptions(end_card=("Thanks",), card_seconds=1), TH, tmp_path)
    assert duration(dst) == pytest.approx(3.0, abs=0.15)
    corner = frames_at(dst)[-1][1][2, 2].astype(int)
    assert np.abs(corner - np.array([0x11, 0x14, 0x17])).max() <= 12
    assert any("end card" in s for s in lines)


def test_music_is_ducked_under_narration(tmp_path):
    src = make_mp4(tmp_path / "s.mp4", 8.0, audio=np.zeros(8 * 24000))
    t = np.arange(22050) / 22050
    sf.write(str(tmp_path / "bed.wav"), (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), 22050)
    dst = tmp_path / "d.mp4"
    lines = finish(src, dst, [Cue(3.0, 4.0, "speaking")],
                   PostOptions(music=Path("bed.wav"), music_db=-6, duck_db=-12), TH, tmp_path)
    a = read_audio(dst)[0]
    free, ducked = rms(a[int(1.3 * RATE):int(2.3 * RATE)]), rms(a[int(3.2 * RATE):int(3.8 * RATE)])
    assert free == pytest.approx(0.3536 * gain(-6), rel=0.2)
    assert 3.0 < free / ducked < 5.0
    assert lines and lines[0].startswith("music bed bed.wav")


def test_music_bed_spans_the_whole_video_and_the_end_card(tmp_path):
    # Manim's narration track ends before the picture does: 4 s of sound under 6 s of video
    src = make_mp4(tmp_path / "s.mp4", 6.0, audio=np.zeros(4 * 24000))
    t = np.arange(22050) / 22050
    sf.write(str(tmp_path / "bed.wav"), (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), 22050)
    dst = tmp_path / "d.mp4"
    finish(src, dst, [], PostOptions(music=Path("bed.wav"), music_db=-6, end_card=("Bye",), card_seconds=1), TH,
           tmp_path)
    a = read_audio(dst)[0]
    level = 0.3536 * gain(-6)
    assert len(a) / RATE == pytest.approx(duration(dst), abs=0.1) == pytest.approx(7.0, abs=0.15)
    assert rms(a[int(4.5 * RATE):int(5.0 * RATE)]) == pytest.approx(level, rel=0.2)  # past the narration's end
    under_card = rms(a[int(6.0 * RATE):int(6.5 * RATE)])
    assert 0.2 * level < under_card < 0.9 * level  # audible, fading
    assert rms(a[int(6.9 * RATE):]) < 0.15 * level  # the fade ends with the card


def test_captions_are_burned_only_while_a_cue_speaks(tmp_path):
    src = make_mp4(tmp_path / "s.mp4", 3.0, shade=lambda i: 40)
    dst = tmp_path / "d.mp4"
    finish(src, dst, [Cue(1.0, 2.0, "A caption")], PostOptions(captions="burn"), TH, tmp_path)
    got = {round(t, 1): img for t, img in frames_at(dst)}

    def changed(img):  # pixels visibly off the source's flat grey
        return int((np.abs(img.astype(int) - 40).max(axis=2) > 12).sum())

    assert changed(got[1.5]) > 150
    assert changed(got[0.5]) < 20 and changed(got[2.5]) < 20


def test_missing_music_fails_and_leaves_nothing(tmp_path):
    src = make_mp4(tmp_path / "s.mp4", 1.0)
    dst = tmp_path / "d.mp4"
    with pytest.raises(PostError, match="post.music"):
        finish(src, dst, [], PostOptions(music=Path("nope.wav")), TH, tmp_path)
    assert not dst.exists()


def test_caption_overlay_wraps_and_stays_inside_the_frame():
    ov = caption_overlay("word " * 60, 1920, 1080, TH)
    h, w = ov.rgba.shape[:2]
    assert ov.x >= 0 and ov.y >= 0 and ov.x + w <= 1920 and ov.y + h <= 1080
    assert w <= 0.8 * 1920 + 60


@pytest.mark.parametrize("text", ["<b>&amp; café ✓ 数学 مرحبا 🎬", "x" * 300, ""])
def test_caption_overlay_survives_odd_text(text):
    ov = caption_overlay(text, 320, 180, TH)
    h, w = ov.rgba.shape[:2]
    assert ov.x >= 0 and ov.y >= 0 and ov.x + w <= 320 and ov.y + h <= 180
    frame = np.zeros((180, 320, 3), np.uint8)
    ov.blend(frame)


def test_card_image_fills_the_frame():
    img = card_image("Series", ["a tagline"], 320, 180, TH)
    assert img.shape == (180, 320, 3) and img.dtype == np.uint8


def test_concat_joins_with_cards_and_reports_where_each_part_starts(tmp_path):
    a = make_mp4(tmp_path / "a.mp4", 1.0)
    b = make_mp4(tmp_path / "b.mp4", 2.0, size=(160, 90))
    dst = tmp_path / "film.mp4"
    starts = concat([a, b], dst, TH, title=["Series", "tagline"], end=("bye",), card_seconds=1.0)
    assert starts == pytest.approx([1.0, 2.0], abs=0.11)
    assert duration(dst) == pytest.approx(5.0, abs=0.2)
    w, h, fps = video_info(dst)
    assert (w, h) == (320, 180) and fps == Fraction(10)


def test_concat_starts_each_part_sound_where_the_part_starts(tmp_path):
    a = make_mp4(tmp_path / "a.mp4", 2.0, audio=np.zeros(2 * 24000))
    b = make_mp4(tmp_path / "b.mp4", 2.0)  # a 220 Hz tone, 0.3 peak
    dst = tmp_path / "film.mp4"
    starts = concat([a, b], dst, TH, title=["Series"], card_seconds=1.0)
    s = read_audio(dst)[0]
    assert starts == pytest.approx([1.0, 3.0], abs=0.11)
    assert rms(s[:int((starts[1] - 0.1) * RATE)]) < 0.01
    assert rms(s[int((starts[1] + 0.2) * RATE):int((starts[1] + 1.8) * RATE)]) == pytest.approx(0.3 / 2 ** 0.5, rel=0.2)


def test_concat_refuses_mixed_frame_rates(tmp_path):
    a = make_mp4(tmp_path / "a.mp4", 1.0, fps=10)
    b = make_mp4(tmp_path / "b.mp4", 1.0, fps=15)
    with pytest.raises(PostError, match="frame rate"):
        concat([a, b], tmp_path / "f.mp4", TH)
    assert not (tmp_path / "f.mp4").exists()


def test_srt_text_numbers_and_times_the_cues():
    text = srt_text([Cue(0.5, 1.25, "one"), Cue(3661.0, 3662.0, "two")])
    assert text.startswith("1\n00:00:00,500 --> 00:00:01,250\none\n")
    assert "2\n01:01:01,000 --> 01:01:02,000\ntwo\n" in text
