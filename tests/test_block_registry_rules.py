"""Registry folders: the name rule and listing a registry with a broken or shadowed block.json."""
import pytest

from manimvox.blocks import all_blocks, get_block_multi
from manimvox.cli import main
from tests.test_blocks import _project, _registry


@pytest.mark.parametrize("name", ["venn\n", "\nvenn", "venn\n\n"])
def test_a_name_with_a_newline_is_refused(tmp_path, name):
    with pytest.raises(ValueError, match="no block named"):
        get_block_multi(name, [_registry(tmp_path, "team")])


def test_a_name_with_a_trailing_newline_is_refused_everywhere(tmp_path, monkeypatch, capsys):
    from manimvox import blocks

    assert blocks.NAME.fullmatch("venn") and not blocks.NAME.fullmatch("venn\n")
    team = _registry(tmp_path, "team")
    with pytest.raises(ValueError, match="no block named"):
        get_block_multi("venn\n", [team])
    d = _project(tmp_path, monkeypatch)
    assert main(["add", "venn\n", "--root", str(team)]) == 1
    assert "no block named" in capsys.readouterr().err
    assert not (d / "blocks").exists()
    bad = _registry(tmp_path, "bad")
    f = bad / "venn" / "block.json"
    f.write_text(f.read_text(encoding="utf-8").replace('"name": "venn"', '"name": "venn\\n"'), encoding="utf-8")
    with pytest.raises(ValueError, match="must equal the folder name"):
        all_blocks(bad)
