"""Secure data ingestion to encrypted temporary directory.

All ingested data is stored in a temporary directory with restricted permissions.
On completion or error, the data can be cryptographically purged.

Supports:
  - Local directory
  - Zip archive
  - GitHub URL (auto-clone + cleanup)
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Iterator
from urllib.parse import urlparse

from cryptography.fernet import Fernet

from due_diligence_engine.config import Config

logger = logging.getLogger(__name__)

# File extensions to analyze
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".kt",
    ".c", ".cpp", ".h", ".hpp", ".rb", ".php", ".swift", ".dart",
    ".scala", ".clj", ".ex", ".exs", ".hs", ".ml",
}

DOC_EXTENSIONS = {
    ".md", ".txt", ".rst", ".pdf", ".docx", ".csv", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg",
}

IGNORED_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".next", ".nuxt", "target", "vendor",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB per file


class SecureLoader:
    """Securely loads and manages project data in an encrypted temp directory."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._encryption_key: bytes | None = Fernet.generate_key()
        self._fernet: Fernet | None = Fernet(self._encryption_key)
        self._work_dir: Path | None = None
        self._clone_dir: Path | None = None
        self._git_repo_path: Path | None = None
        self._manifest: list[dict[str, str]] = []

    @property
    def work_dir(self) -> Path:
        if self._work_dir is None:
            raise RuntimeError("Loader not initialized. Call load_directory or load_archive first.")
        return self._work_dir

    @property
    def manifest(self) -> list[dict[str, str]]:
        return list(self._manifest)

    def _create_secure_temp(self, prefix: str = "dde_secure_") -> Path:
        """Create a temporary directory with restricted permissions.

        Unix/macOS: chmod 0o700 (owner-only). Windows: chmod does not map to
        NTFS ACLs, so inherited ACEs are stripped and full control granted to
        the current user only via ``icacls`` (stdlib subprocess, no pywin32).
        Best-effort — a hardening failure is logged, never fatal.
        """
        base = self._config.temp_dir
        base.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkdtemp(prefix=prefix, dir=str(base)))
        # Restrict to owner only
        tmp.chmod(stat.S_IRWXU)
        if sys.platform == "win32":
            self._restrict_acl_windows(tmp)
        return tmp

    @staticmethod
    def _restrict_acl_windows(path: Path) -> None:
        """Owner-only NTFS ACL: remove inheritance, grant only the current user."""
        import getpass

        try:
            user = getpass.getuser()
            proc = subprocess.run(
                ["icacls", str(path), "/inheritance:r",
                 "/grant:r", f"{user}:(OI)(CI)F"],
                capture_output=True, text=True, timeout=30,
            )
            if proc.returncode != 0:
                logger.warning(
                    "Windows ACL hardening failed for %s: %s",
                    path, (proc.stderr or proc.stdout).strip(),
                )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("Windows ACL hardening failed for %s: %s", path, exc)

    def load_from_url(self, url: str) -> Path:
        """Load a project from a GitHub URL (or any Git-compatible URL).

        Clones the repo into a secure temp directory, loads files, then
        removes the clone. Only code/doc files are retained (encrypted).

        Args:
            url: GitHub URL. Accepts formats like:
                 - https://github.com/owner/repo
                 - https://github.com/owner/repo.git
                 - https://github.com/owner/repo/tree/branch
                 - github.com/owner/repo
                 - owner/repo (assumes GitHub)
                 - git@github.com:owner/repo.git

        Returns:
            Path to the secure working directory.

        Raises:
            ValueError: If the URL is invalid.
            RuntimeError: If git clone fails.
        """
        if self._work_dir is not None or self._clone_dir is not None:
            self.destroy()

        normalized = self._normalize_github_url(url)
        branch = self._extract_branch(url)

        clone_dir = self._create_secure_temp(prefix="dde_clone_")
        self._clone_dir = clone_dir

        try:
            logger.info(f"Cloning {normalized} ...")
            cmd = ["git", "clone", "--depth", "50"]
            if branch:
                cmd.extend(["--branch", branch])
            cmd.extend([normalized, str(clone_dir / "repo")])

            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"git clone failed (exit {proc.returncode}): {proc.stderr.strip()}"
                )

            repo_dir = clone_dir / "repo"
            self._git_repo_path = repo_dir

            # Load into encrypted workspace
            return self.load_directory(repo_dir)

        except subprocess.TimeoutExpired:
            if self._clone_dir is not None and self._clone_dir.exists():
                self._shred_tree(self._clone_dir)
            self._clone_dir = None
            raise RuntimeError(f"git clone timed out after 5 minutes: {normalized}")
        except Exception:
            if self._clone_dir is not None and self._clone_dir.exists():
                self._shred_tree(self._clone_dir)
            self._clone_dir = None
            raise

    @property
    def cloned_repo_path(self) -> Path | None:
        """Return the path to the cloned repo, if loaded via URL."""
        return getattr(self, "_git_repo_path", None)

    @staticmethod
    def _normalize_github_url(url: str) -> str:
        """Normalize various GitHub URL formats to a clone-able HTTPS URL.

        Accepts:
            owner/repo              → https://github.com/owner/repo.git
            owner/repo.git          → https://github.com/owner/repo.git
            github.com/owner/repo   → https://github.com/owner/repo.git
            git@github.com:o/r.git  → https://github.com/o/r.git
            https://github.com/...  → https://github.com/owner/repo.git
        """
        url = url.strip().rstrip("/")

        # SSH format: git@github.com:owner/repo(.git) -> https://github.com/owner/repo.git
        ssh_match = re.match(r"^git@github\.com:([^/]+)/(.+?)(?:\.git)?$", url)
        if ssh_match:
            return f"https://github.com/{ssh_match.group(1)}/{ssh_match.group(2)}.git"

        # Remove tree/branch suffix: .../tree/branch or .../tree/feature/fix -> ...
        url = re.sub(r"/tree/.*$", "", url).rstrip("/")

        # Short form: owner/repo or owner/repo.git
        short_match = re.match(r"^([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+?)(?:\.git)?$", url)
        if short_match:
            return f"https://github.com/{short_match.group(1)}/{short_match.group(2)}.git"

        # Missing scheme: github.com/owner/repo
        if url.startswith("github.com/"):
            url = "https://" + url

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL format: {url}")

        # Ensure .git suffix for clone without double .git
        path = parsed.path.rstrip("/")
        if path.endswith(".git"):
            path = path[:-4]
        path += ".git"

        return f"{parsed.scheme}://{parsed.netloc}{path}"

    @staticmethod
    def _extract_branch(url: str) -> str | None:
        """Extract branch name from GitHub URL if present.

        e.g., https://github.com/owner/repo/tree/develop → 'develop'
        e.g., https://github.com/owner/repo/tree/feature/fix → 'feature/fix'
        """
        match = re.search(r"/tree/(.+)$", url.strip().rstrip("/"))
        if match:
            branch = match.group(1).rstrip("/")
            if branch.endswith(".git"):
                branch = branch[:-4]
            return branch
        return None

    def load_directory(self, source: Path) -> Path:
        """Load a project directory into the secure workspace.

        Args:
            source: Path to the project directory.

        Returns:
            Path to the secure working directory.

        Raises:
            FileNotFoundError: If the source directory does not exist.
            PermissionError: If the source directory is not readable.
        """
        if not source.exists():
            raise FileNotFoundError(f"Source directory not found: {source}")
        if not source.is_dir():
            raise ValueError(f"Source is not a directory: {source}")

        is_from_clone = False
        if self._clone_dir is not None:
            try:
                is_from_clone = source.resolve().is_relative_to(self._clone_dir.resolve())
            except (ValueError, OSError):
                is_from_clone = False

        if self._work_dir is not None or (self._clone_dir is not None and not is_from_clone):
            self.destroy()

        if self._fernet is None:
            self._encryption_key = Fernet.generate_key()
            self._fernet = Fernet(self._encryption_key)

        self._work_dir = self._create_secure_temp(prefix="dde_secure_")

        for file_path in self._walk_files(source):
            rel_path = file_path.relative_to(source)
            dest = self._work_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)

            try:
                st = file_path.stat(follow_symlinks=False)
                if not stat.S_ISREG(st.st_mode):
                    continue
                if st.st_size > MAX_FILE_SIZE_BYTES:
                    continue

                content = file_path.read_bytes()

                # Encrypt at rest
                encrypted = self._fernet.encrypt(content)
                dest.with_suffix(dest.suffix + ".enc").write_bytes(encrypted)

                file_hash = hashlib.sha256(content).hexdigest()
                self._manifest.append({
                    "path": str(rel_path),
                    "hash": file_hash,
                    "size": str(len(content)),
                    "type": _classify_file(file_path),
                })
            except (PermissionError, OSError):
                continue

        return self._work_dir

    def load_archive(self, archive_path: Path) -> Path:
        """Load a zip archive into the secure workspace.

        Args:
            archive_path: Path to the zip file.

        Returns:
            Path to the secure working directory.
        """
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        if self._work_dir is not None or self._clone_dir is not None:
            self.destroy()

        staging = self._create_secure_temp(prefix="dde_staging_")
        try:
            extract_dir = staging / "_extracted"
            extract_dir.mkdir()
            extract_root = extract_dir.resolve()
            total_uncompressed = 0
            max_uncompressed = 500 * 1024 * 1024  # 500 MB

            with zipfile.ZipFile(str(archive_path), "r") as zf:
                for member in zf.infolist():
                    # Reject symlinks
                    if ((member.external_attr >> 16) & 0o170000) == 0o120000:
                        raise ValueError(f"Zip symlink rejected: {member.filename}")
                    # Security: check for path traversal
                    target = (extract_dir / member.filename).resolve()
                    if not target.is_relative_to(extract_root):
                        raise ValueError(f"Zip path traversal detected: {member.filename}")
                    total_uncompressed += member.file_size
                    if total_uncompressed > max_uncompressed:
                        raise ValueError(f"Zip uncompressed size exceeds limit: {total_uncompressed}")
                zf.extractall(str(extract_dir))

            # Re-process extracted files through secure loading (sets _work_dir
            # to a new encrypted workspace, distinct from `staging`).
            return self.load_directory(extract_dir)
        finally:
            self._shred_tree(staging)

    def read_file(self, relative_path: str) -> str:
        """Read and decrypt a file from the secure workspace.

        Args:
            relative_path: Path relative to the workspace root.

        Returns:
            Decrypted file content as a string.
        """
        if self._fernet is None or self._work_dir is None:
            raise RuntimeError("Workspace not initialized. Call load_* first.")
        enc_path = self.work_dir / (relative_path + ".enc")
        if not enc_path.exists():
            raise FileNotFoundError(f"File not found in workspace: {relative_path}")

        encrypted = enc_path.read_bytes()
        decrypted = self._fernet.decrypt(encrypted)
        return decrypted.decode("utf-8", errors="replace")

    def read_file_bytes(self, relative_path: str) -> bytes:
        """Read and decrypt a file as raw bytes."""
        if self._fernet is None or self._work_dir is None:
            raise RuntimeError("Workspace not initialized. Call load_* first.")
        enc_path = self.work_dir / (relative_path + ".enc")
        if not enc_path.exists():
            raise FileNotFoundError(f"File not found in workspace: {relative_path}")

        encrypted = enc_path.read_bytes()
        return self._fernet.decrypt(encrypted)

    def get_code_files(self) -> list[dict[str, str]]:
        """Return manifest entries for code files only."""
        return [f for f in self._manifest if f["type"] == "code"]

    def get_doc_files(self) -> list[dict[str, str]]:
        """Return manifest entries for document files only."""
        return [f for f in self._manifest if f["type"] == "doc"]

    def destroy(self) -> int:
        """Securely destroy the workspace. Returns bytes overwritten."""
        total_bytes = 0
        errors: list[Exception] = []
        try:
            if self._work_dir is not None and self._work_dir.exists():
                try:
                    total_bytes += self._shred_tree(self._work_dir)
                    if not self._work_dir.exists():
                        self._work_dir = None
                except Exception as exc:
                    errors.append(exc)
            else:
                self._work_dir = None

            if self._clone_dir is not None and self._clone_dir.exists():
                try:
                    total_bytes += self._shred_tree(self._clone_dir)
                    if not self._clone_dir.exists():
                        self._clone_dir = None
                except Exception as exc:
                    errors.append(exc)
            else:
                self._clone_dir = None

            self._git_repo_path = None
            if errors:
                raise errors[0]
            return total_bytes
        finally:
            self._encryption_key = b""
            self._fernet = None
            self._manifest.clear()

    @staticmethod
    def _shred_tree(target: Path) -> int:
        """Overwrite every file under ``target`` with random bytes, then remove
        the whole tree. Returns the number of bytes overwritten.

        Shared by destroy() and the archive-staging cleanup so both teardown
        paths give the same best-effort secure erase. (Overwrite-in-place is
        best-effort only — see the README security notes on SSD/COW media.)
        """
        bytes_overwritten = 0
        shred_errors: list[OSError] = []

        for root, _dirs, files in os.walk(str(target), onerror=shred_errors.append):
            for fname in files:
                fpath = Path(root) / fname
                try:
                    if fpath.is_symlink():
                        fpath.unlink()
                        continue

                    # Clear read-only attributes (e.g. git pack objects)
                    try:
                        fpath.chmod(stat.S_IRUSR | stat.S_IWUSR)
                    except OSError:
                        pass

                    st = fpath.stat(follow_symlinks=False)
                    if not stat.S_ISREG(st.st_mode):
                        try:
                            fpath.unlink()
                        except OSError as e:
                            shred_errors.append(e)
                        continue

                    size = st.st_size
                    with open(fpath, "wb") as f:
                        f.write(os.urandom(size))
                        f.flush()
                        os.fsync(f.fileno())
                    bytes_overwritten += size
                    fpath.unlink()
                except OSError as exc:
                    shred_errors.append(exc)
        # Only remove tree if all files were successfully overwritten/unlinked
        if not shred_errors:
            if sys.version_info >= (3, 12):
                def _on_rmtree_exc(func, path, exc):
                    try:
                        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                        func(path)
                    except OSError as e:
                        shred_errors.append(e)

                shutil.rmtree(str(target), onexc=_on_rmtree_exc)
            else:
                def _on_rmtree_error(func, path, exc_info):
                    try:
                        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
                        func(path)
                    except OSError as e:
                        shred_errors.append(e)

                shutil.rmtree(str(target), onerror=_on_rmtree_error)

        if shred_errors or target.exists():
            err_msg = f"Failed to securely shred {target}: {len(shred_errors)} error(s), remaining={target.exists()}"
            logger.error(err_msg)
            if shred_errors:
                raise shred_errors[0]
            raise OSError(err_msg)

        return bytes_overwritten

    def _walk_files(self, source: Path) -> Iterator[Path]:
        """Walk directory yielding analyzable files, skipping ignored dirs."""
        root_resolved = source.resolve()
        for root, dirs, files in os.walk(str(source), followlinks=False):
            dirs[:] = [
                d for d in dirs
                if d not in IGNORED_DIRS
                and not (d.startswith(".") and d not in {".github", ".circleci"})
                and not (Path(root) / d).is_symlink()
            ]
            for fname in files:
                file_path = Path(root) / fname
                if file_path.is_symlink():
                    continue
                try:
                    if not file_path.resolve().is_relative_to(root_resolved):
                        continue
                    st = file_path.stat(follow_symlinks=False)
                    if not stat.S_ISREG(st.st_mode):
                        continue
                    if st.st_size > MAX_FILE_SIZE_BYTES:
                        continue
                except (OSError, ValueError):
                    continue
                if file_path.suffix in CODE_EXTENSIONS | DOC_EXTENSIONS or _classify_file(file_path) in {"code", "doc"}:
                    yield file_path


def _classify_file(path: Path) -> str:
    """Classify a file as code, doc, or other."""
    if path.name in {"Jenkinsfile", "Dockerfile", "Makefile", ".gitlab-ci.yml", ".travis.yml"}:
        return "code"
    if path.suffix in CODE_EXTENSIONS:
        return "code"
    if path.suffix in DOC_EXTENSIONS:
        return "doc"
    return "other"
