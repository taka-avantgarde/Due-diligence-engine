"""Tests for cryptographic purge + certificate (src/purge/secure_delete.py).

Covers: multi-pass overwrite byte accounting, file/directory removal,
missing-target handling, purge-certificate fields, signing, JSON export, and
end-to-end signature verification with the exported public key.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from src.purge import secure_delete as sd
from src.purge.secure_delete import OVERWRITE_PASSES, SecurePurger


def _file(tmp_path: Path, name: str = "f.bin", size: int = 1000) -> Path:
    p = tmp_path / name
    p.write_bytes(b"A" * size)
    return p


# ── purge_file ───────────────────────────────────────────────────────────────


def test_purge_file_returns_three_times_size(tmp_path):
    assert SecurePurger().purge_file(_file(tmp_path, size=1000)) == OVERWRITE_PASSES * 1000


def test_purge_file_removes_file(tmp_path):
    p = _file(tmp_path)
    SecurePurger().purge_file(p)
    assert not p.exists()


def test_purge_file_missing_returns_zero(tmp_path):
    assert SecurePurger().purge_file(tmp_path / "nope.bin") == 0


def test_purge_file_empty_file(tmp_path):
    p = tmp_path / "empty.bin"
    p.write_bytes(b"")
    assert SecurePurger().purge_file(p) == 0
    assert not p.exists()


def test_secure_overwrite_uses_random_then_zero_pass(tmp_path, monkeypatch):
    purger = SecurePurger()  # construct before patching os.urandom
    real = os.urandom
    calls: list[int] = []

    def counting_urandom(n: int) -> bytes:
        calls.append(n)
        return real(n)

    monkeypatch.setattr(sd.os, "urandom", counting_urandom)
    purger.purge_file(_file(tmp_path, size=64))
    # OVERWRITE_PASSES-1 random passes of `size`, final pass writes zeros.
    assert calls == [64] * (OVERWRITE_PASSES - 1)


# ── purge_directory ──────────────────────────────────────────────────────────


def test_purge_directory_counts_and_removes(tmp_path):
    d = tmp_path / "workspace"
    (d / "sub").mkdir(parents=True)
    (d / "a.py").write_bytes(b"x" * 100)
    (d / "sub" / "b.txt").write_bytes(b"y" * 200)

    cert = SecurePurger().purge_directory(d, analysis_id="A1", project_name="Proj")
    assert cert.files_purged == 2
    assert cert.bytes_overwritten == OVERWRITE_PASSES * (100 + 200)
    assert not d.exists()


def test_purge_directory_missing_returns_unsigned_cert(tmp_path):
    cert = SecurePurger().purge_directory(
        tmp_path / "gone", analysis_id="A", project_name="P",
    )
    assert cert.verification_hash == "directory_not_found"  # exact, no "|sig:"
    assert cert.files_purged == 0
    assert cert.bytes_overwritten == 0


def test_purge_directory_cert_is_signed(tmp_path):
    d = tmp_path / "w"
    d.mkdir()
    (d / "f.py").write_bytes(b"z" * 10)
    cert = SecurePurger().purge_directory(d, analysis_id="A", project_name="P")
    assert "|sig:" in cert.verification_hash
    digest = cert.verification_hash.split("|sig:")[0]
    assert len(digest) == 64
    int(digest, 16)  # valid hex — raises ValueError otherwise


def test_purge_directory_operator_recorded(tmp_path):
    d = tmp_path / "w"
    d.mkdir()
    (d / "f.py").write_bytes(b"z")
    default_cert = SecurePurger().purge_directory(d, analysis_id="A", project_name="P")
    assert default_cert.operator == "system"

    d2 = tmp_path / "w2"
    d2.mkdir()
    (d2 / "f.py").write_bytes(b"z")
    named = SecurePurger().purge_directory(
        d2, analysis_id="A", project_name="P", operator="auditor",
    )
    assert named.operator == "auditor"


# ── Certificate export + signature verification ──────────────────────────────


def test_export_certificate_writes_full_json(tmp_path):
    d = tmp_path / "w"
    d.mkdir()
    (d / "f.py").write_bytes(b"z" * 10)
    purger = SecurePurger()
    cert = purger.purge_directory(d, analysis_id="A", project_name="P")

    out = tmp_path / "nested" / "cert.json"
    purger.export_certificate(cert, out)
    assert out.exists()  # parent dirs created

    data = json.loads(out.read_text(encoding="utf-8"))
    for key in ("certificate_id", "analysis_id", "project_name", "purge_timestamp",
                "files_purged", "bytes_overwritten", "method", "verification_hash",
                "operator", "public_key"):
        assert key in data
    assert data["method"] == "cryptographic_erasure"
    assert data["public_key"].startswith("-----BEGIN PUBLIC KEY-----")


def test_certificate_signature_verifies_with_exported_key(tmp_path):
    d = tmp_path / "w"
    d.mkdir()
    (d / "f.py").write_bytes(b"z" * 10)
    purger = SecurePurger()
    cert = purger.purge_directory(d, analysis_id="A", project_name="Proj")

    out = tmp_path / "cert.json"
    purger.export_certificate(cert, out)
    pem = json.loads(out.read_text(encoding="utf-8"))["public_key"]
    pubkey = load_pem_public_key(pem.encode())

    digest, sig_hex = cert.verification_hash.split("|sig:")
    signed = (
        f"{cert.certificate_id}|{cert.analysis_id}|{cert.project_name}|"
        f"{cert.purge_timestamp.isoformat()}|{cert.files_purged}|"
        f"{cert.bytes_overwritten}|{digest}"
    ).encode()
    # Raises cryptography.exceptions.InvalidSignature if verification fails.
    pubkey.verify(bytes.fromhex(sig_hex), signed, ec.ECDSA(hashes.SHA256()))
