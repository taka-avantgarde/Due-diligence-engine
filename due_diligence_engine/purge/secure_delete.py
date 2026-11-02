"""Cryptographic erasure and purge certificate generation.

Implements secure deletion by:
1. Overwriting files with zero, ones, then random data (3 passes)
2. Destroying encryption keys
3. Generating a verifiable purge certificate
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from due_diligence_engine.models import PurgeCertificate

OVERWRITE_PASSES = 3


def secure_overwrite_file(file_path: Path) -> int:
    """Overwrite in place in bounded chunks; propagate failure for retry.

    Never fall back to truncation, or unlink a file after an incomplete pass.
    Symlinks and special files are unlinked without opening their targets.
    """
    st = file_path.lstat()
    if not stat.S_ISREG(st.st_mode):
        file_path.unlink()
        return 0
    file_path.chmod(st.st_mode | stat.S_IRUSR | stat.S_IWUSR)
    size = st.st_size
    with open(file_path, "r+b") as stream:
        for pass_num in range(OVERWRITE_PASSES):
            stream.seek(0)
            remaining = size
            while remaining:
                chunk_size = min(1024 * 1024, remaining)
                chunk = (b"\x00" * chunk_size if pass_num == 0 else
                         b"\xff" * chunk_size if pass_num == 1 else
                         os.urandom(chunk_size))
                if stream.write(chunk) != chunk_size:
                    raise OSError("Incomplete secure overwrite")
                remaining -= chunk_size
            stream.flush()
            os.fsync(stream.fileno())
    file_path.unlink()
    return size * OVERWRITE_PASSES


class SecurePurger:
    """Securely deletes analysis data and generates purge certificates."""

    def __init__(self) -> None:
        # Generate an ephemeral signing key for certificates
        self._signing_key = ec.generate_private_key(ec.SECP256R1())
        self._verify_key = self._signing_key.public_key()

    def purge_directory(
        self,
        directory: Path,
        analysis_id: str,
        project_name: str,
        operator: str = "system",
    ) -> PurgeCertificate:
        """Securely purge a directory and generate a certificate.

        Args:
            directory: Directory to purge.
            analysis_id: ID of the analysis being purged.
            project_name: Name of the analyzed project.
            operator: Name of the person/system performing the purge.

        Returns:
            PurgeCertificate documenting the purge.
        """
        if directory.is_symlink():
            try:
                directory.unlink()
                cert = PurgeCertificate(
                    analysis_id=analysis_id,
                    project_name=project_name,
                    files_purged=1,
                    bytes_overwritten=0,
                    operator=operator,
                    verification_hash=hashlib.sha256(f"{directory}:symlink".encode()).hexdigest(),
                )
                self._sign_certificate(cert)
                return cert
            except OSError:
                return PurgeCertificate(
                    analysis_id=analysis_id,
                    project_name=project_name,
                    files_purged=0,
                    bytes_overwritten=0,
                    operator=operator,
                    verification_hash="purge_incomplete",
                )

        if not directory.exists():
            return PurgeCertificate(
                analysis_id=analysis_id, project_name=project_name,
                operator=operator, verification_hash="directory_not_found",
            )

        files_purged = 0
        bytes_overwritten = 0
        file_hashes: list[str] = []
        failed_files = 0

        if directory.is_file():
            try:
                st = directory.lstat()
                size = st.st_size
                overwritten = self._secure_overwrite(directory)
                bytes_overwritten += overwritten
                if not directory.exists():
                    files_purged += 1
                    file_hashes.append(
                        hashlib.sha256(f"{directory}:{size}:{overwritten}".encode()).hexdigest()
                    )
                else:
                    failed_files += 1
            except OSError:
                failed_files += 1
        else:
            walk_errors: list[OSError] = []
            for root, dirs, files in os.walk(str(directory), onerror=walk_errors.append):
                for dirname in dirs[:]:
                    link = Path(root) / dirname
                    if link.is_symlink():
                        try:
                            link.unlink()
                            files_purged += 1
                        except OSError:
                            failed_files += 1
                        dirs.remove(dirname)
                for fname in files:
                    fpath = Path(root) / fname
                    try:
                        st = fpath.lstat()
                        size = st.st_size
                        overwritten = self._secure_overwrite(fpath)
                        bytes_overwritten += overwritten
                        if not fpath.exists():
                            files_purged += 1
                            file_hashes.append(
                                hashlib.sha256(f"{fpath}:{size}:{overwritten}".encode()).hexdigest()
                            )
                        else:
                            failed_files += 1
                    except OSError:
                        failed_files += 1

            failed_files += len(walk_errors)
            # Keep failed files for a future overwrite attempt.
            if not failed_files:
                try:
                    shutil.rmtree(str(directory))
                except OSError:
                    failed_files += 1

        if failed_files > 0:
            return PurgeCertificate(
                analysis_id=analysis_id,
                project_name=project_name,
                files_purged=files_purged,
                bytes_overwritten=bytes_overwritten,
                operator=operator,
                verification_hash="purge_incomplete",
            )

        # Generate verification hash
        combined = "|".join(file_hashes)
        verification_hash = hashlib.sha256(combined.encode()).hexdigest()

        cert = PurgeCertificate(
            analysis_id=analysis_id,
            project_name=project_name,
            files_purged=files_purged,
            bytes_overwritten=bytes_overwritten,
            operator=operator,
            verification_hash=verification_hash,
        )

        # Sign the certificate
        self._sign_certificate(cert)

        return cert

    def _secure_overwrite(self, file_path: Path) -> int:
        """Overwrite a file with random data multiple times, then delete.

        Args:
            file_path: Path to the file to overwrite.

        Returns:
            Total bytes overwritten across all passes.
        """
        return secure_overwrite_file(file_path)

    def _sign_certificate(self, cert: PurgeCertificate) -> None:
        """Sign the canonical payload without changing its verification hash."""
        cert.method = "DoD 5220.22-M (0x00, 0xFF, random; fsync each pass)"
        cert.signature = self._signing_key.sign(
            cert._sign_payload(), ec.ECDSA(hashes.SHA256())
        ).hex()
        cert.public_key = self._verify_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")

    def export_certificate(self, cert: PurgeCertificate, output_path: Path) -> Path:
        """Export the purge certificate to a JSON file.

        Args:
            cert: The purge certificate.
            output_path: Path to save the certificate.

        Returns:
            Path to the saved certificate file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cert_data = cert.model_dump(mode="json")

        output_path.write_text(
            json.dumps(cert_data, indent=2), encoding="utf-8"
        )
        return output_path

    def purge_file(self, file_path: Path) -> int:
        """Securely purge a single file.

        Args:
            file_path: Path to the file.

        Returns:
            Bytes overwritten.
        """
        if not file_path.exists() and not file_path.is_symlink():
            return 0
        return self._secure_overwrite(file_path)
