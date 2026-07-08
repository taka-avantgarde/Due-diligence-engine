"""Tests for the secure ingestion loader (src/ingest/secure_loader.py).

Covers: 0o700 temp permissions (POSIX), encryption-at-rest, manifest
classification, walk/ignore rules, per-file size cap, archive extraction +
path-traversal rejection, plaintext-staging cleanup, secure destroy(), URL
normalization, and the Windows ACL hardening argv (cross-platform via
monkeypatch + a Windows-only integration check).
"""

from __future__ import annotations

import getpass
import hashlib
import logging
import stat
import sys
import zipfile
from pathlib import Path

import pytest

from src.config import Config
from src.ingest import secure_loader as sl
from src.ingest.secure_loader import SecureLoader, _classify_file

POSIX_ONLY = pytest.mark.skipif(sys.platform == "win32", reason="POSIX file mode only")


def _config(tmp_path: Path) -> Config:
    return Config(temp_dir=tmp_path / "dde_tmp")


def _loader(tmp_path: Path) -> SecureLoader:
    return SecureLoader(_config(tmp_path))


def _make_source(tmp_path: Path) -> Path:
    """A small project tree: 2 code files + 1 doc file."""
    src = tmp_path / "project"
    (src / "pkg").mkdir(parents=True)
    (src / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (src / "README.md").write_text("# Title\n", encoding="utf-8")
    (src / "pkg" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    return src


def _make_zip(tmp_path: Path, members: dict[str, str]) -> Path:
    zpath = tmp_path / "arc.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return zpath


# ── Temp dir creation & permissions ──────────────────────────────────────────


@POSIX_ONLY
def test_create_secure_temp_mode_0o700(tmp_path):
    tmp = _loader(tmp_path)._create_secure_temp()
    assert stat.S_IMODE(tmp.stat().st_mode) == 0o700


@POSIX_ONLY
def test_workdir_mode_0o700_after_load(tmp_path):
    loader = _loader(tmp_path)
    loader.load_directory(_make_source(tmp_path))
    assert stat.S_IMODE(loader.work_dir.stat().st_mode) == 0o700


def test_temp_under_config_dir_with_prefix(tmp_path):
    cfg = _config(tmp_path)
    loader = SecureLoader(cfg)
    loader.load_directory(_make_source(tmp_path))
    assert loader.work_dir.name.startswith("dde_")
    assert loader.work_dir.parent.samefile(cfg.temp_dir)


def test_workdir_property_raises_before_load(tmp_path):
    with pytest.raises(RuntimeError):
        _ = _loader(tmp_path).work_dir


# ── Encryption at rest + read-back ───────────────────────────────────────────


def test_encryption_at_rest_and_roundtrip(tmp_path):
    loader = _loader(tmp_path)
    src = _make_source(tmp_path)
    content = (src / "main.py").read_bytes()
    loader.load_directory(src)

    enc = loader.work_dir / "main.py.enc"
    assert enc.exists()
    assert not (loader.work_dir / "main.py").exists()
    assert enc.read_bytes() != content  # stored ciphertext != plaintext
    assert loader.read_file("main.py") == content.decode("utf-8")
    assert loader.read_file_bytes("main.py") == content


def test_read_file_missing_raises(tmp_path):
    loader = _loader(tmp_path)
    loader.load_directory(_make_source(tmp_path))
    with pytest.raises(FileNotFoundError):
        loader.read_file("nope.py")


# ── Manifest classification, hashing, walk rules ─────────────────────────────


def test_manifest_classifies_code_and_doc(tmp_path):
    loader = _loader(tmp_path)
    loader.load_directory(_make_source(tmp_path))
    assert len(loader.get_code_files()) == 2  # main.py + pkg/mod.py
    assert len(loader.get_doc_files()) == 1   # README.md
    assert {e["type"] for e in loader.manifest} == {"code", "doc"}


def test_manifest_hash_and_size_match_plaintext(tmp_path):
    loader = _loader(tmp_path)
    src = _make_source(tmp_path)
    loader.load_directory(src)
    entry = next(e for e in loader.manifest if e["path"] == "main.py")
    content = (src / "main.py").read_bytes()
    assert entry["hash"] == hashlib.sha256(content).hexdigest()
    assert entry["size"] == str(len(content))


def test_manifest_is_a_copy(tmp_path):
    loader = _loader(tmp_path)
    loader.load_directory(_make_source(tmp_path))
    loader.manifest.clear()  # mutating the returned list must not affect state
    assert len(loader.manifest) == 3


def test_ignored_and_hidden_dirs_skipped(tmp_path):
    src = _make_source(tmp_path)
    (src / "node_modules").mkdir()
    (src / "node_modules" / "x.py").write_text("junk\n", encoding="utf-8")
    (src / ".secret").mkdir()
    (src / ".secret" / "k.py").write_text("secret\n", encoding="utf-8")
    (src / ".github" / "workflows").mkdir(parents=True)
    (src / ".github" / "workflows" / "ci.yml").write_text("on: push\n", encoding="utf-8")

    loader = _loader(tmp_path)
    loader.load_directory(src)
    paths = {e["path"].replace("\\", "/") for e in loader.manifest}
    assert "node_modules/x.py" not in paths      # IGNORED_DIRS
    assert ".secret/k.py" not in paths           # hidden dir skipped
    assert ".github/workflows/ci.yml" in paths   # .github is the exception


def test_oversized_file_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(sl, "MAX_FILE_SIZE_BYTES", 8)
    src = _make_source(tmp_path)
    (src / "big.py").write_text("x = 123456789\n", encoding="utf-8")  # > 8 bytes
    loader = _loader(tmp_path)
    loader.load_directory(src)
    paths = {e["path"].replace("\\", "/") for e in loader.manifest}
    assert "big.py" not in paths
    with pytest.raises(FileNotFoundError):
        loader.read_file("big.py")


def test_load_directory_missing_source_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        _loader(tmp_path).load_directory(tmp_path / "nope")


def test_load_directory_file_source_raises(tmp_path):
    afile = tmp_path / "a.py"
    afile.write_text("x = 1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        _loader(tmp_path).load_directory(afile)


# ── Archive loading + path-traversal + plaintext-staging cleanup ─────────────


def test_load_archive_extracts_and_loads(tmp_path):
    z = _make_zip(tmp_path, {"pkg/mod.py": "y = 2\n", "README.md": "# hi\n"})
    loader = _loader(tmp_path)
    loader.load_archive(z)
    assert loader.read_file("pkg/mod.py") == "y = 2\n"


def test_load_archive_rejects_path_traversal(tmp_path):
    z = _make_zip(tmp_path, {"../evil.txt": "pwned"})
    loader = _loader(tmp_path)
    with pytest.raises(ValueError, match="traversal"):
        loader.load_archive(z)


def test_load_archive_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        _loader(tmp_path).load_archive(tmp_path / "nope.zip")


def test_load_archive_no_plaintext_staging_leak(tmp_path):
    """Regression: the plaintext extraction staging dir must be shredded, so no
    decrypted copy survives under temp_dir once the archive is ingested."""
    z = _make_zip(tmp_path, {"secret.py": "TOP_SECRET = 1\n"})
    cfg = _config(tmp_path)
    loader = SecureLoader(cfg)
    loader.load_archive(z)

    dde_dirs = [p for p in cfg.temp_dir.iterdir() if p.name.startswith("dde_")]
    assert len(dde_dirs) == 1                      # only the encrypted workspace
    assert loader.work_dir.samefile(dde_dirs[0])
    for p in cfg.temp_dir.rglob("*"):              # no plaintext anywhere
        if p.is_file():
            assert b"TOP_SECRET" not in p.read_bytes()

    loader.destroy()
    assert [p for p in cfg.temp_dir.iterdir() if p.name.startswith("dde_")] == []


# ── Secure destroy() ─────────────────────────────────────────────────────────


def test_destroy_removes_workdir_and_returns_bytes(tmp_path):
    loader = _loader(tmp_path)
    loader.load_directory(_make_source(tmp_path))
    wd = loader.work_dir
    assert loader.destroy() > 0
    assert not wd.exists()


def test_destroy_clears_state(tmp_path):
    loader = _loader(tmp_path)
    loader.load_directory(_make_source(tmp_path))
    loader.destroy()
    assert loader.manifest == []
    with pytest.raises(RuntimeError):
        _ = loader.work_dir


def test_destroy_idempotent_and_before_load(tmp_path):
    loader = _loader(tmp_path)
    assert loader.destroy() == 0  # never loaded
    loader.load_directory(_make_source(tmp_path))
    loader.destroy()
    assert loader.destroy() == 0  # already destroyed


# ── URL normalization / branch / classify (pure static helpers) ──────────────


@pytest.mark.parametrize("raw,expected", [
    ("owner/repo", "https://github.com/owner/repo.git"),
    ("github.com/o/r", "https://github.com/o/r.git"),
    ("https://github.com/o/r/tree/main", "https://github.com/o/r.git"),
    ("https://github.com/o/r.git", "https://github.com/o/r.git"),
    ("https://github.com/o/r", "https://github.com/o/r.git"),
])
def test_normalize_github_url(raw, expected):
    assert SecureLoader._normalize_github_url(raw) == expected


def test_normalize_github_url_invalid_raises():
    with pytest.raises(ValueError):
        SecureLoader._normalize_github_url("not a url")


def test_extract_branch():
    assert SecureLoader._extract_branch("https://github.com/o/r/tree/develop") == "develop"
    assert SecureLoader._extract_branch("https://github.com/o/r") is None


def test_classify_file():
    assert _classify_file(Path("a.py")) == "code"
    assert _classify_file(Path("a.md")) == "doc"
    assert _classify_file(Path("a.png")) == "other"


# ── Windows ACL hardening (cross-platform argv + non-fatal failure) ──────────


def test_restrict_acl_argv_construction(tmp_path, monkeypatch):
    captured: dict = {}

    class _Done:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _Done()

    monkeypatch.setattr(sl.subprocess, "run", fake_run)
    target = tmp_path / "acltest"
    target.mkdir()
    SecureLoader._restrict_acl_windows(target)

    user = getpass.getuser()
    assert captured["args"] == [
        "icacls", str(target), "/inheritance:r", "/grant:r", f"{user}:(OI)(CI)F",
    ]
    assert captured["kwargs"].get("timeout") == 30
    assert captured["kwargs"].get("capture_output") is True
    assert captured["kwargs"].get("text") is True


def test_restrict_acl_nonzero_exit_is_nonfatal(tmp_path, monkeypatch, caplog):
    class _Fail:
        returncode = 1
        stdout = ""
        stderr = "Access is denied."

    monkeypatch.setattr(sl.subprocess, "run", lambda *a, **k: _Fail())
    with caplog.at_level(logging.WARNING):
        SecureLoader._restrict_acl_windows(tmp_path)  # must not raise
    assert "ACL hardening failed" in caplog.text


def test_restrict_acl_oserror_is_nonfatal(tmp_path, monkeypatch, caplog):
    def boom(*a, **k):
        raise OSError("icacls not found")

    monkeypatch.setattr(sl.subprocess, "run", boom)
    with caplog.at_level(logging.WARNING):
        SecureLoader._restrict_acl_windows(tmp_path)  # must not raise
    assert "ACL hardening failed" in caplog.text


@pytest.mark.skipif(sys.platform != "win32", reason="Windows NTFS ACL only")
def test_restrict_acl_windows_owner_only(tmp_path):
    """On Windows, the real temp dir must be owner-only with inheritance stripped."""
    import subprocess

    tmp = _loader(tmp_path)._create_secure_temp()
    out = subprocess.run(
        ["icacls", str(tmp)], capture_output=True, text=True,
    ).stdout
    user = getpass.getuser()
    assert user in out
    assert "(F)" in out  # full control granted to the owner
    assert "BUILTIN\\Users" not in out
    assert "Everyone" not in out
