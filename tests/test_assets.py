import hashlib
import io
import json
import shutil
from pathlib import Path

import pytest

from manimvox import assets, tools
from manimvox.cli import main
from manimvox.tools import ToolError
from manimvox.voice import http
from tests.http_fakes import Server

FIXTURE = Path(__file__).parent / "fixtures" / "hello"
DATA = b"mesh bytes " * 100
MD5 = hashlib.md5(DATA).hexdigest()
ZENODO_URL = "https://zenodo.org/records/42/files/heart.tar.gz"


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    return d


def zenodo(licence="cc-by-4.0", digest=MD5, files=None):
    return json.dumps({
        "doi": "10.5281/zenodo.42",
        "metadata": {"title": "A <b>Heart</b>", "license": {"id": licence} if licence else {},
                     "creators": [{"name": "Doe, Jane"}, {"name": "Roe, Rick"}], "publication_date": "2021-03-04"},
        "files": files or [{"key": "heart.tar.gz", "size": len(DATA), "checksum": f"md5:{digest}",
                            "links": {"self": "https://zenodo.org/api/records/42/files/heart.tar.gz/content"}}],
    }).encode()


def commons(licence="CC BY-SA 4.0", artist='<a href="x">Ann Artist</a>'):
    sha1 = hashlib.sha1(DATA).hexdigest()
    return json.dumps({"query": {"pages": [{"imageinfo": [{
        "url": "https://upload.wikimedia.org/wikipedia/commons/a/ab/Heart.stl", "size": len(DATA), "sha1": sha1,
        "extmetadata": {"LicenseShortName": {"value": licence}, "Artist": {"value": artist},
                        "DateTimeOriginal": {"value": "2019-05-01"}}}]}]}}).encode()


@pytest.fixture
def net(monkeypatch):
    """Queue API replies; downloads write DATA and are counted. Anything else fails the test."""
    state = {"downloads": []}

    def serve(*replies):
        monkeypatch.setattr(http, "_urlopen", Server(*replies))

    def stream(url, dest):
        state["downloads"].append(url)
        dest.write_bytes(DATA)

    monkeypatch.setattr(assets, "_stream", stream)
    monkeypatch.delenv("MANIMVOX_ASSUME_YES", raising=False)
    serve()
    state["serve"] = serve
    return state


# ---- licences ----

@pytest.mark.parametrize("text,lid", [
    ("CC-BY-4.0", "CC-BY-4.0"), ("cc by 4.0", "CC-BY-4.0"), ("https://creativecommons.org/licenses/by/4.0/", "CC-BY-4.0"),
    ("CC BY-SA 3.0", "CC-BY-SA-3.0"), ("cc-by-sa-4.0", "CC-BY-SA-4.0"), ("CC BY 2.0 DE", "CC-BY-2.0-DE"),
    ("CC0", "CC0-1.0"), ("CC0 1.0 Universal", "CC0-1.0"), ("https://creativecommons.org/publicdomain/zero/1.0/", "CC0-1.0"),
    ("https://creativecommons.org/publicdomain/mark/1.0/", "PDM-1.0"), ("Public domain", "PD"),
    ("mit", "MIT"), ("Apache License 2.0", "Apache-2.0"), ("BSD-3-Clause", "BSD-3-Clause"), ("ISC", "ISC"),
    ("ODC-By", "ODC-By-1.0"), ("odbl-1.0", "ODbL-1.0"), ("PDDL", "PDDL-1.0"), ("Open Government Licence v3.0", "OGL-UK-3.0"),
])
def test_accepted_licences_normalise(text, lid):
    lic = assets.normalise(text)
    assert lic.id == lid and lic.kind == "free"
    assets.decide(lic)


def test_non_commercial_needs_the_flag():
    lic = assets.normalise("CC BY-NC 4.0")
    assert lic.id == "CC-BY-NC-4.0" and lic.kind == "nc"
    with pytest.raises(assets.AssetError, match="--non-commercial"):
        assets.decide(lic)
    assets.decide(lic, non_commercial=True)
    assert assets.normalise("cc-by-nc-sa-4.0").kind == "nc"


@pytest.mark.parametrize("text", ["CC BY-ND 4.0", "cc-by-nc-nd-4.0"])
def test_no_derivatives_always_refused(text):
    with pytest.raises(assets.AssetError, match="derivative"):
        assets.decide(assets.normalise(text), non_commercial=True)


@pytest.mark.parametrize("text", ["", "all rights reserved", "GPL-3.0", "see the website"])
def test_unknown_refused_naming_what_to_pass(text):
    with pytest.raises(assets.AssetError, match="--licence"):
        assets.decide(assets.normalise(text))


# ---- plan ----

def test_zenodo_detection(project, net):
    net["serve"](zenodo())
    p = assets.plan(project, ZENODO_URL)
    assert (p.licence, p.licence_basis, p.file, p.size) == ("CC-BY-4.0", "detected from Zenodo",
                                                          "research/assets/heart.tar.gz", len(DATA))
    assert p.credit == 'Doe, Jane; Roe, Rick, "A Heart" (2021), Zenodo, https://doi.org/10.5281/zenodo.42'
    assert p.download_url.endswith("/files/heart.tar.gz/content")
    assert net["downloads"] == []


def test_zenodo_record_with_many_files_asks_for_one(project, net):
    two = [{"key": "a.csv", "size": 1, "checksum": "md5:x", "links": {}}, {"key": "b.csv", "size": 1, "checksum": "md5:y", "links": {}}]
    net["serve"](zenodo(files=two))
    with pytest.raises(assets.AssetError, match="a.csv, b.csv"):
        assets.plan(project, "https://zenodo.org/records/42")


def test_wikimedia_detection(project, net):
    net["serve"](commons())
    p = assets.plan(project, "https://commons.wikimedia.org/wiki/File:Heart.stl")
    assert p.licence == "CC-BY-SA-4.0" and p.licence_basis == "detected from Wikimedia Commons"
    assert p.credit.startswith('Ann Artist, "Heart" (2019), Wikimedia Commons')
    assert p.file == "research/assets/Heart.stl" and p.algo == "sha1"


def test_a_commons_signature_loses_its_talk_link(project, net):
    signed = ('<a href="//commons.wikimedia.org/wiki/User:Ann" title="User:Ann">Ann Artist</a> (<a href="//commons.'
              'wikimedia.org/wiki/User_talk:Ann" title="User talk:Ann"><span class="signature-talk">leave a reply</span>'
              '</a>)')
    net["serve"](commons(artist=signed))
    p = assets.plan(project, "https://commons.wikimedia.org/wiki/File:Heart.stl")
    assert p.credit.startswith('Ann Artist, "Heart" (2019)')


def test_contradicting_licence_refused(project, net):
    net["serve"](zenodo())
    with pytest.raises(assets.AssetError, match="contradicts"):
        assets.plan(project, ZENODO_URL, licence="CC0")
    net["serve"](zenodo())
    assert assets.plan(project, ZENODO_URL, licence="cc by 4.0").licence == "CC-BY-4.0"


def test_published_nd_and_unpublished_licence(project, net):
    net["serve"](zenodo("cc-by-nd-4.0"))
    with pytest.raises(assets.AssetError, match="derivative"):
        assets.plan(project, ZENODO_URL)
    net["serve"](zenodo(licence=""))
    with pytest.raises(assets.AssetError, match="--licence"):
        assets.plan(project, ZENODO_URL)
    net["serve"](zenodo(licence=""))
    p = assets.plan(project, ZENODO_URL, licence="CC0")
    assert p.licence_basis == "stated by the agent"


def test_other_url_needs_a_licence(project, net):
    with pytest.raises(assets.AssetError, match="--licence"):
        assets.plan(project, "https://example.test/models/Heart%20v2.stl")
    p = assets.plan(project, "https://example.test/models/Heart%20v2.stl", licence="MIT", credit="Me, 2020")
    assert p.file == "research/assets/Heart v2.stl" and p.credit == "Me, 2020"
    assert p.licence_basis == "stated by the agent"


def test_plain_http_and_odd_names_refused(project, net):
    with pytest.raises(assets.AssetError, match="https"):
        assets.plan(project, "http://example.test/a.stl", licence="MIT")
    with pytest.raises(assets.AssetError, match="--name"):
        assets.plan(project, "https://example.test/a.stl", licence="MIT", name="../x.stl")
    with pytest.raises(assets.AssetError, match="--name"):
        assets.plan(project, "https://example.test/", licence="MIT")


# ---- fetch ----

def test_fetch_verifies_records_and_writes_facts(project, net):
    net["serve"](zenodo())
    p = assets.plan(project, ZENODO_URL)
    asked = []
    f = assets.fetch(project, p, lambda q: asked.append(q) or True)
    assert f.path.read_bytes() == DATA and f.archive and not list(f.path.parent.glob("*.part"))
    assert "heart.tar.gz" in asked[0] and "CC-BY-4.0" in asked[0] and "kB" in asked[0]
    rec = json.loads((project / "research/assets.json").read_text())["assets"][0]
    assert rec["sha256"] == hashlib.sha256(DATA).hexdigest() and rec["bytes"] == len(DATA)
    assert rec["licence"] == "CC-BY-4.0" and rec["licence_detected"] == "cc-by-4.0" and rec["licence_stated"] == ""
    assert rec["non_commercial"] is False and rec["credit"] == p.credit and rec["fetched"]
    facts = (project / "FACTS.md").read_text()
    assert "## Assets" in facts and "`research/assets/heart.tar.gz`" in facts and "Credit on screen" in facts
    assert "commercially" not in facts


def test_checksum_mismatch_discarded(project, net):
    net["serve"](zenodo(digest="0" * 32))
    p = assets.plan(project, ZENODO_URL)
    with pytest.raises(assets.AssetError, match="checksum"):
        assets.fetch(project, p, lambda q: True)
    assert not (project / "research/assets").exists() or not list((project / "research/assets").iterdir())
    assert not (project / "research/assets.json").exists()


def test_wikimedia_sha1_verified(project, net):
    net["serve"](commons())
    f = assets.fetch(project, assets.plan(project, "https://commons.wikimedia.org/wiki/File:Heart.stl"), lambda q: True)
    assert f.path.name == "Heart.stl" and not f.archive


def test_declined_downloads_nothing(project, net):
    p = assets.plan(project, "https://example.test/a.stl", licence="MIT")
    with pytest.raises(assets.AssetError, match="--yes"):
        assets.fetch(project, p, lambda q: False)
    assert net["downloads"] == [] and not (project / "research/assets.json").exists()


def test_refuse_overwrite_of_a_different_file(project, net):
    dest = project / "research/assets/a.stl"
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"mine")
    with pytest.raises(assets.AssetError, match="already exists"):
        assets.plan(project, "https://example.test/a.stl", licence="MIT")
    assert dest.read_bytes() == b"mine"


def test_same_file_is_recorded_without_download_or_question(project, net):
    net["serve"](zenodo(), zenodo())
    assets.fetch(project, assets.plan(project, ZENODO_URL), lambda q: True)
    net["downloads"].clear()
    p = assets.plan(project, ZENODO_URL)
    assert p.present
    assets.fetch(project, p, lambda q: pytest.fail("asked"))
    assert net["downloads"] == []
    assert len(assets.load(project)) == 1 and (project / "FACTS.md").read_text().count("heart.tar.gz") == 1


def test_non_commercial_recorded_in_facts(project, net):
    net["serve"](zenodo("cc-by-nc-4.0"))
    p = assets.plan(project, ZENODO_URL, non_commercial=True)
    assets.fetch(project, p, lambda q: True)
    assert "must not be used commercially" in (project / "FACTS.md").read_text()
    assert assets.load(project)[0]["non_commercial"] is True


def test_assets_section_reuses_and_keeps_later_sections(project, net):
    (project / "FACTS.md").write_text("# F\n\n## Assets\n\n- old\n\n## Other\n\n- x\n", encoding="utf-8")
    assets.fetch(project, assets.plan(project, "https://example.test/a.stl", licence="MIT"), lambda q: True)
    text = (project / "FACTS.md").read_text()
    assert text.index("- old") < text.index("a.stl") < text.index("## Other") and text.count("## Assets") == 1


# ---- tool ----

def test_tool_does_not_download_without_yes(project, net):
    net["serve"](zenodo())
    r = tools.fetch_asset(str(project), ZENODO_URL)
    assert not r.ok and not r.downloaded and "CC-BY-4.0" in r.ask and "yes=true" in r.next
    assert net["downloads"] == [] and not (project / "research").exists() or not (project / "research/assets").exists()


def test_tool_ignores_assume_yes_env(project, net, monkeypatch):
    monkeypatch.setenv("MANIMVOX_ASSUME_YES", "1")
    r = tools.fetch_asset(str(project), "https://example.test/a.stl", licence="MIT")
    assert not r.ok and net["downloads"] == []


def test_tool_downloads_with_yes_and_lists(project, net):
    net["serve"](zenodo())
    r = tools.fetch_asset(str(project), ZENODO_URL, yes=True)
    assert r.ok and r.downloaded and r.archive and (project / r.file).is_file()
    listed = tools.list_assets(str(project))
    assert [a["file"] for a in listed.assets] == [r.file]


def test_tool_refusals_are_tool_errors(project, net):
    with pytest.raises(ToolError, match="--licence"):
        tools.fetch_asset(str(project), "https://example.test/a.stl")
    with pytest.raises(ToolError, match="derivative"):
        tools.fetch_asset(str(project), "https://example.test/a.stl", licence="CC BY-ND 4.0", yes=True)


# ---- command ----

def test_cli_add_and_list(project, net, monkeypatch, capsys):
    monkeypatch.chdir(project)
    net["serve"](zenodo())
    assert main(["assets", "add", ZENODO_URL, "--yes"]) == 0
    out = capsys.readouterr().out
    assert "saved:" in out and "CC-BY-4.0 (detected from Zenodo)" in out and "archive" in out
    assert main(["assets", "list"]) == 0
    listed = capsys.readouterr().out
    assert "research/assets/heart.tar.gz" in listed and "Doe, Jane" in listed


def test_cli_global_yes_and_name(project, net, monkeypatch, capsys):
    monkeypatch.chdir(project)
    assert main(["--yes", "assets", "add", "https://example.test/a.stl", "--licence", "CC0", "--name", "b.stl"]) == 0
    assert (project / "research/assets/b.stl").is_file()


def test_cli_non_interactive_without_yes_refuses(project, net, monkeypatch, capsys):
    monkeypatch.chdir(project)
    monkeypatch.setattr("sys.stdin", io.StringIO(""))  # not a terminal
    assert main(["assets", "add", "https://example.test/a.stl", "--licence", "MIT"]) == 1
    err = capsys.readouterr().err
    assert "--yes" in err and "example.test/a.stl" in err and net["downloads"] == []


def test_cli_refuses_licence_and_empty_list(project, net, monkeypatch, capsys):
    monkeypatch.chdir(project)
    assert main(["assets", "list"]) == 0 and "no assets yet" in capsys.readouterr().out
    assert main(["assets", "add", "https://example.test/a.stl", "-y"]) == 1
    assert "--licence" in capsys.readouterr().err
    assert main(["assets", "add", "https://example.test/a.stl", "--licence", "cc-by-nc-4.0", "-y"]) == 1
    assert "--non-commercial" in capsys.readouterr().err
    assert main(["assets", "add", "https://example.test/a.stl", "--licence", "cc-by-nc-4.0", "-y", "--non-commercial"]) == 0
