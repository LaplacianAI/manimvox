"""decode_video: footage with a damaged packet plays on from the next good one instead of stopping the read."""
import av
import numpy as np
import pytest

from manimvox.post.encode import decode_video


class Stream:
    def __init__(self, bad):
        self.bad = bad

    def decode(self, packet):
        if packet in self.bad:
            raise av.error.InvalidDataError(1094995529, "Invalid data found when processing input")
        return [f"frame{packet}"]


class Container:
    def __init__(self, n):
        self.n = n

    def demux(self, stream):
        return iter(range(self.n))


def test_a_damaged_packet_is_skipped_and_the_rest_decoded():
    assert list(decode_video(Container(6), Stream({2, 3}))) == ["frame0", "frame1", "frame4", "frame5"]


def test_other_errors_still_stop_the_read():
    class Broken(Stream):
        def decode(self, packet):
            raise av.error.PermissionError(13, "denied")

    with pytest.raises(av.error.PermissionError):
        list(decode_video(Container(2), Broken(set())))


def test_a_written_film_starts_with_its_index(tmp_path):
    """The moov box comes before the media, so a browser can play a long film before it has all of it."""
    from manimvox.post.encode import Writer

    dst = tmp_path / "a.mp4"
    w = Writer(dst, (64, 48), 10)
    for i in range(10):
        w.add(np.full((48, 64, 3), i * 20, np.uint8))
    w.close()
    data = dst.read_bytes()
    assert 0 <= data.find(b"moov") < data.find(b"mdat")
