"""Real files an explainer needs (a model, a scan, a dataset, an image), fetched with their licence recorded.

`plan` works out what would be fetched and whether its licence allows the use, without downloading the file;
`fetch` downloads it after consent and writes research/assets.json and a FACTS.md entry.
"""

from __future__ import annotations

import datetime
import html
import json
import os
import re
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .voice import http
from .voice.download import file_digest

ASSETS_DIR = "research/assets"
ASSETS_JSON = "research/assets.json"
ARCHIVES = (".zip", ".tar.gz", ".tgz", ".tar", ".tar.bz2", ".tar.xz", ".7z")


class AssetError(ValueError):
    """An asset cannot be fetched or recorded. The message says why and what to pass."""


# ---- licences -------------------------------------------------------------------------------------------------

# canonical SPDX-style id -> aliases, all compared after normalising case and separators
_ALLOWED = {
    "CC0-1.0": ("cc0", "cc0-1.0", "cc-zero", "cc0-1", "creative-commons-zero"),
    "PDM-1.0": ("pdm", "pdm-1.0", "cc-pdm", "public-domain-mark", "public-domain-mark-1.0"),
    "PD": ("pd", "public-domain", "publicdomain", "public-domain-dedication", "pd-us", "pd-old", "pd-usgov",
           "pd-art", "pd-self", "us-government-work", "pd-usgov-nasa"),
    "MIT": ("mit", "mit-license", "the-mit-license"),
    "BSD-2-Clause": ("bsd-2-clause", "bsd-2", "bsd-2-clause-license", "simplified-bsd", "freebsd"),
    "BSD-3-Clause": ("bsd-3-clause", "bsd-3", "bsd-3-clause-license", "new-bsd", "modified-bsd"),
    "Apache-2.0": ("apache-2.0", "apache-2", "apache-license-2.0", "apache-license-version-2.0", "apache2"),
    "ISC": ("isc", "isc-license"),
    "Unlicense": ("unlicense", "the-unlicense"),
    "ODC-By-1.0": ("odc-by", "odc-by-1.0", "odc-attribution", "open-data-commons-attribution-license"),
    "ODbL-1.0": ("odbl", "odbl-1.0", "open-database-license", "open-data-commons-open-database-license"),
    "PDDL-1.0": ("pddl", "pddl-1.0", "open-data-commons-public-domain-dedication-and-license"),
    "OGL-UK-3.0": ("ogl", "ogl-uk-3.0", "ogl-3.0", "open-government-licence", "open-government-licence-v3.0",
                   "open-government-licence-3.0", "uk-ogl"),
    "OGL-Canada-2.0": ("ogl-canada-2.0", "open-government-licence-canada"),
    "etalab-2.0": ("etalab-2.0", "etalab", "licence-ouverte-2.0"),
}
_ALIAS = {a: spdx for spdx, names in _ALLOWED.items() for a in names}

_CC_URL = re.compile(r"creativecommons\.org/(licenses|publicdomain)/([a-z-]+)/(\d(?:\.\d)?)", re.IGNORECASE)
_CC_TEXT = re.compile(r"^cc-by((?:-(?:nc|sa|nd))*)(?:-(\d(?:\.\d)?))?(?:-([a-z]{2,3}))?$")


@dataclass(frozen=True)
class Licence:
    id: str  # canonical, e.g. CC-BY-4.0; "" when unknown
    kind: str  # "free", "nc" (non-commercial), "nd" (no derivatives) or "unknown"
    stated: str = ""  # the text it was read from


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9.]+", "-", text.lower()).strip("-")


def normalise(text: str) -> Licence:
    """Read a licence from an id ("CC-BY-4.0"), a name ("CC BY-SA 3.0") or a URL."""
    raw = (text or "").strip()
    if not raw:
        return Licence("", "unknown", raw)
    m = _CC_URL.search(raw)
    if m:
        group, kind, version = m.group(1).lower(), m.group(2).lower(), m.group(3)
        if group == "publicdomain":
            return Licence({"zero": "CC0-1.0", "mark": "PDM-1.0"}.get(kind, ""), "free" if kind in ("zero", "mark")
                           else "unknown", raw)
        raw_slug = f"cc-{kind}-{version}"
    else:
        raw_slug = _slug(raw)
    raw_slug = re.sub(r"-(international|unported|generic|universal)$", "", re.sub(r"^cc(?=by)", "cc-", raw_slug))
    if raw_slug in _ALIAS:
        return Licence(_ALIAS[raw_slug], "free", raw)
    m = _CC_TEXT.match(raw_slug)
    if m:
        mods = [x for x in m.group(1).split("-") if x]
        version, port = m.group(2), m.group(3)
        cid = "-".join(["CC-BY", *(x.upper() for x in mods)] + ([version] if version else [])
                       + ([port.upper()] if port else []))
        kind = "nd" if "nd" in mods else "nc" if "nc" in mods else "free"
        return Licence(cid, kind, raw)
    return Licence("", "unknown", raw)


def decide(lic: Licence, non_commercial: bool = False) -> None:
    """Raise AssetError unless the licence allows the use."""
    shown = lic.stated or "nothing"
    if lic.kind == "free":
        return
    if lic.kind == "nd":
        raise AssetError(
            f"refused: {lic.id} (no derivatives). Cutting, simplifying or recolouring a model is a derivative, "
            "so a no-derivatives file cannot go in a video; find one under CC BY, CC BY-SA, CC0 or public domain")
    if lic.kind == "nc":
        if non_commercial:
            return
        raise AssetError(
            f"refused: {lic.id} is non-commercial. If the video will never be used commercially and the user "
            "agrees, pass --non-commercial (tool: non_commercial=true); FACTS.md then records the limit")
    raise AssetError(
        f"refused: the licence is unknown ({shown!r} is not one manimvox accepts). Pass --licence ID with the "
        "licence the source states (public domain, CC0, CC BY, CC BY-SA, MIT, BSD, Apache-2.0, ISC, ODC-By, ODbL, "
        "PDDL or OGL); if there is none, or it is all rights reserved, the file cannot be used")


# ---- sources --------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Source:
    url: str  # where the bytes come from
    name: str  # file name to save as
    page: str = ""  # the record or file page
    size: int | None = None
    algo: str = ""  # checksum the source publishes: md5, sha1
    digest: str = ""
    licence: str = ""  # as the source publishes it
    title: str = ""
    credit: str = ""  # built from what the source publishes
    site: str = ""  # "Zenodo", "Wikimedia Commons" or ""


def _json(url: str, service: str):
    body = http.request(service, "GET", url, headers={"Accept": "application/json"}, timeout=30)
    try:
        return json.loads(body)
    except ValueError:
        raise AssetError(f"{service} sent something that is not JSON: {url}") from None


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", text or ""))).strip()


_ZENODO = re.compile(r"^/(?:records?|api/records)/(\d+)(?:/files/(.+?)(?:/content)?)?/?$")


def _zenodo(url: str, p: urllib.parse.ParseResult) -> Source | None:
    if p.hostname not in ("zenodo.org", "www.zenodo.org"):
        return None
    m = _ZENODO.match(urllib.parse.unquote(p.path))
    if not m:
        raise AssetError(f"not a Zenodo record or file URL: {url} (use https://zenodo.org/records/<id>[/files/<name>])")
    rec, key = m.group(1), m.group(2)
    data = _json(f"https://zenodo.org/api/records/{rec}", "Zenodo")
    meta = data.get("metadata") or {}
    files = data.get("files") or []
    if key is None:
        if len(files) != 1:
            names = ", ".join(f["key"] for f in files[:12]) + (", ..." if len(files) > 12 else "")
            raise AssetError(f"Zenodo record {rec} has {len(files)} files ({names}); "
                             f"use the file's URL: https://zenodo.org/records/{rec}/files/<name>")
        key = files[0]["key"]
    f = next((x for x in files if x.get("key") == key), None)
    if f is None:
        raise AssetError(f"Zenodo record {rec} has no file {key!r}")
    algo, _, digest = (f.get("checksum") or "").partition(":")
    lic = (meta.get("license") or {}).get("id", "")
    title = _strip_html(meta.get("title", ""))
    names = [c.get("name", "") for c in meta.get("creators") or [] if c.get("name")]
    year = (meta.get("publication_date") or "")[:4]
    doi = data.get("doi") or meta.get("doi") or ""
    where = f"https://doi.org/{doi}" if doi else f"https://zenodo.org/records/{rec}"
    credit = _credit("; ".join(names) or "Unknown author", title, year, "Zenodo", where)
    return Source(
        url=(f.get("links") or {}).get("self") or f"https://zenodo.org/records/{rec}/files/{key}?download=1",
        name=key, page=f"https://zenodo.org/records/{rec}", size=f.get("size"), algo=algo.lower(), digest=digest,
        licence=lic, title=title, credit=credit, site="Zenodo")


def _credit(author: str, title: str, year: str, site: str, where: str) -> str:
    """Author, "Title" (year), Site, where."""
    head = f"{author}, \"{title}\"" if title else author
    return ", ".join([f"{head} ({year})" if year else head, site, where])


def _commons_title(p: urllib.parse.ParseResult) -> str | None:
    path = urllib.parse.unquote(p.path)
    if p.hostname == "commons.wikimedia.org" and path.startswith("/wiki/File:"):
        return path[len("/wiki/"):]
    if p.hostname == "upload.wikimedia.org" and path.startswith("/wikipedia/commons/") and "/thumb/" not in path:
        return "File:" + path.rsplit("/", 1)[1]
    return None


def _wikimedia(url: str, p: urllib.parse.ParseResult) -> Source | None:
    title = _commons_title(p)
    if title is None:
        return None
    q = urllib.parse.urlencode({"action": "query", "titles": title.replace("_", " "), "prop": "imageinfo",
                                "iiprop": "url|size|sha1|extmetadata", "format": "json", "formatversion": "2"})
    data = _json(f"https://commons.wikimedia.org/w/api.php?{q}", "Wikimedia Commons")
    pages = (data.get("query") or {}).get("pages") or []
    info = (pages[0].get("imageinfo") or [None])[0] if pages else None
    if not info:
        raise AssetError(f"Wikimedia Commons has no file {title!r}")
    ext = info.get("extmetadata") or {}

    def val(k: str) -> str:
        return _strip_html((ext.get(k) or {}).get("value", ""))

    lic = val("LicenseShortName") or val("License")
    artist = val("Artist") or val("Credit") or "Unknown author"
    name = title.split(":", 1)[1].replace(" ", "_")
    page = f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'), safe=':')}"
    date = val("DateTimeOriginal") or val("DateTime")
    year = (re.search(r"\b(1[5-9]\d\d|20\d\d)\b", date) or [""])[0] if date else ""
    credit = _credit(artist, name.rsplit(".", 1)[0].replace("_", " "), year, "Wikimedia Commons", page)
    return Source(url=info["url"], name=name, page=page, size=info.get("size"), algo="sha1",
                  digest=info.get("sha1", ""), licence=lic, title=title, credit=credit, site="Wikimedia Commons")


def resolve(url: str) -> Source:
    """What `url` is: for Zenodo and Wikimedia Commons from their API, otherwise just the URL."""
    p = urllib.parse.urlparse(url)
    if p.scheme != "https":
        raise AssetError(f"only https URLs are fetched: {url}")
    found = _zenodo(url, p) or _wikimedia(url, p)
    if found:
        return found
    name = urllib.parse.unquote(p.path.rstrip("/").rsplit("/", 1)[-1])
    return Source(url=url, name=name, page=url)


# ---- plan and fetch -------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Plan:
    url: str
    download_url: str
    file: str  # relative to the project root
    size: int | None
    licence: str  # canonical id
    licence_stated: str  # what the caller passed
    licence_detected: str  # what the source publishes
    licence_basis: str  # "detected from Zenodo", "stated by the agent", ...
    credit: str
    non_commercial: bool
    algo: str = ""
    digest: str = ""
    page: str = ""
    present: bool = False  # the same file is already there: nothing to download

    def question(self) -> str:
        size = f", {_megabytes(self.size)}" if self.size else ""
        nc = " (non-commercial use only)" if self.non_commercial else ""
        return (f"Download {self.url}{size} to {self.file}? Licence {self.licence}{nc}, {self.licence_basis}. "
                f"Credit: {self.credit}")


def _megabytes(n: int) -> str:
    return f"{n / 1e6:.1f} MB" if n >= 100_000 else f"{n / 1e3:.1f} kB" if n >= 1000 else f"{n} bytes"


def _safe_name(name: str) -> str:
    name = (name or "").strip()
    if (not name or name in (".", "..") or "/" in name or "\\" in name or name.startswith(".")
            or len(name) > 200 or "\x00" in name):
        raise AssetError(f"cannot save as {name!r}: pass --name with a plain file name (no folders)")
    return name


def plan(root: Path, url: str, licence: str = "", credit: str = "", name: str = "",
         non_commercial: bool = False) -> Plan:
    """Look up the source, check the licence and the destination. Reads the source's API; never the file."""
    src = resolve(url)
    detected = normalise(src.licence) if src.licence else None
    stated = normalise(licence) if licence else None
    if detected is not None:
        if stated is not None and stated.id != detected.id:
            raise AssetError(
                f"refused: --licence {licence!r} contradicts the {src.site} record, which says "
                f"{src.licence!r}. Leave --licence out to use the published one")
        lic, basis = detected, f"detected from {src.site}"
        if not detected.id:
            raise AssetError(f"refused: {src.site} publishes the licence {src.licence!r}, which manimvox does not "
                             "accept (public domain, CC0, CC BY, CC BY-SA, MIT, BSD, Apache-2.0, ISC, ODC-By, ODbL, "
                             "PDDL and OGL are); find another file")
    elif stated is not None:
        lic, basis = stated, "stated by the agent"
    else:
        lic, basis = Licence("", "unknown"), ""
    decide(lic, non_commercial)
    fname = _safe_name(name or src.name)
    dest = root / ASSETS_DIR / fname
    rel = f"{ASSETS_DIR}/{fname}"
    present = False
    if dest.exists():
        same = src.digest and src.algo and file_digest(dest, src.algo) == src.digest
        if not same:
            raise AssetError(f"{rel} already exists and is not this file; pass --name to save it under another name")
        present = True
    return Plan(url=url, download_url=src.url, file=rel, size=src.size, licence=lic.id, licence_stated=licence,
                licence_detected=src.licence, licence_basis=basis,
                credit=credit.strip() or src.credit or f"{src.page or url} ({lic.id})",
                non_commercial=lic.kind == "nc", algo=src.algo, digest=src.digest, page=src.page, present=present)


def _stream(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": http.USER_AGENT})
    try:
        with http._urlopen(req, timeout=60) as r, open(dest, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
    except OSError as e:
        raise AssetError(f"download failed: {type(e).__name__}: {e}") from None


@dataclass(frozen=True)
class Fetched:
    plan: Plan
    path: Path
    sha256: str
    bytes: int
    archive: bool


def fetch(root: Path, p: Plan, confirm: Callable[[str], bool], download: Callable[[str, Path], None] | None = None,
          today: datetime.date | None = None) -> Fetched:
    """Ask, download, verify the published checksum, then record the asset. Nothing is kept on a mismatch."""
    dest = root / p.file
    if not p.present:
        if not confirm(p.question()):
            raise AssetError(f"not downloaded: {p.question()} Ask the user, then rerun with --yes")
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_name(dest.name + ".part")
        try:
            (download or _stream)(p.download_url, part)
            if p.digest and file_digest(part, p.algo) != p.digest:
                raise AssetError(f"checksum mismatch for {p.url}: the {p.algo} of the download is not the one the "
                                 "source publishes; the file was discarded")
            if dest.exists():
                raise AssetError(f"{p.file} appeared while downloading; pass --name to save under another name")
            os.replace(part, dest)
        finally:
            part.unlink(missing_ok=True)
    f = Fetched(p, dest, file_digest(dest), dest.stat().st_size, dest.name.lower().endswith(ARCHIVES))
    record(root, f, today or datetime.date.today())
    return f


# ---- records --------------------------------------------------------------------------------------------------


def load(root: Path) -> list[dict]:
    path = root / ASSETS_JSON
    if not path.is_file():
        return []
    try:
        return list(json.loads(path.read_text(encoding="utf-8")).get("assets", []))
    except (ValueError, AttributeError):
        raise AssetError(f"{ASSETS_JSON} is not valid JSON; fix or remove it") from None


def record(root: Path, f: Fetched, today: datetime.date) -> None:
    p = f.plan
    entry = {"url": p.url, "page": p.page, "file": p.file, "sha256": f.sha256, "bytes": f.bytes,
             "licence": p.licence, "licence_stated": p.licence_stated, "licence_detected": p.licence_detected,
             "licence_basis": p.licence_basis, "credit": p.credit, "non_commercial": p.non_commercial,
             "fetched": today.isoformat()}
    items = [a for a in load(root) if a.get("file") != p.file] + [entry]
    path = root / ASSETS_JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"assets": items}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _facts(root, entry)


def _facts(root: Path, e: dict) -> None:
    path = root / "FACTS.md"
    text = path.read_text(encoding="utf-8") if path.is_file() else "# Facts\n"
    marker = f"`{e['file']}`"
    if marker in text:
        return
    line = (f"- [EXTERNAL] {marker} — {e['page'] or e['url']}. Licence: {e['licence']} ({e['licence_basis']}). "
            f"Credit on screen: \"{e['credit']}\". Fetched {e['fetched']}, sha256 {e['sha256'][:12]}.")
    if e["non_commercial"]:
        line += " Non-commercial licence: this video must not be used commercially."
    m = re.search(r"^## Assets\s*$", text, re.MULTILINE)
    if m is None:
        text = text.rstrip("\n") + "\n\n## Assets\n\n" + line + "\n"
    else:
        nxt = re.search(r"^## ", text[m.end():], re.MULTILINE)
        end = m.end() + nxt.start() if nxt else len(text)
        text = text[:end].rstrip("\n") + "\n" + line + "\n" + ("\n" + text[end:] if nxt else "")
    path.write_text(text, encoding="utf-8")

