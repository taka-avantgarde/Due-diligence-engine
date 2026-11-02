"""Shared Application API for Due Diligence Engine.

Provides an in-memory session registry and programmatic workflows for:
- Auditing local directories, zip archives, or Git repositories
- Inspecting evidence with line slicing and opaque identifiers
- Verifying public website claims
- Validating and parsing LLM consulting submissions
- Rendering 24-page due diligence PDFs atomically
- Securely shredding ephemeral workspace files
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import tempfile
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from due_diligence_engine.analyze.engine import AnalysisEngine
from due_diligence_engine.analyze.site_analyzer import SiteAnalyzer
from due_diligence_engine.config import Config
from due_diligence_engine.ingest.secure_loader import SecureLoader
from due_diligence_engine.models import (
    AnalysisResult,
    ConsultingReport,
    SiteAnalysisModel,
    SiteClaimModel,
)
from due_diligence_engine.prompt.response_parser import (
    parse_consulting_dict,
    validate_consulting_submission,
)
from due_diligence_engine.report.pdf_generator import PDFReportGenerator
from due_diligence_engine.score.site_scorer import SiteScorer

logger = logging.getLogger(__name__)


@dataclass
class AuditSession:
    """An active due diligence audit session."""

    audit_id: str
    project_name: str
    target: str
    lang: str
    stage: str
    loader: SecureLoader
    analysis_result: AnalysisResult
    snapshot_sha256: str
    file_id_map: dict[str, str]  # file_id -> rel_path
    rel_path_to_id: dict[str, str]  # rel_path -> file_id
    validated_reports: dict[str, ConsultingReport] = field(default_factory=dict)
    is_closed: bool = False


_SESSION_LOCK = threading.RLock()
_ACTIVE_SESSIONS: dict[str, AuditSession] = {}


def _get_session(audit_id: str) -> AuditSession:
    """Retrieve an active audit session or raise KeyError."""
    session = _ACTIVE_SESSIONS.get(audit_id)
    if not session or session.is_closed:
        raise KeyError(f"Audit session '{audit_id}' not found or already closed")
    return session


def prepare_audit(
    target: str | Path,
    *,
    name: str | None = None,
    lang: str = "en",
    stage: str = "unknown",
    skip_git: bool = False,
) -> dict[str, Any]:
    """Ingest a project, run local heuristic analysis, and create an audit session.

    Args:
        target: File path, directory, zip archive, or Git clone URL.
        name: Optional custom project name.
        lang: Primary report language (e.g. 'en', 'ja', 'es').
        stage: Funding stage ('seed', 'series_a', etc.).
        skip_git: Whether to skip Git forensics analysis.

    Returns:
        Structured audit metadata dict.
    """
    target_str = str(target)
    is_url = (
        target_str.startswith("http://")
        or target_str.startswith("https://")
        or target_str.startswith("git@")
        or ("github.com" in target_str and not Path(target_str).exists())
    )

    cfg = Config.from_env()
    loader = SecureLoader(config=cfg)

    if is_url:
        loader.load_from_url(target_str)
        repo_path = loader.cloned_repo_path
        proj_name = name or target_str.rstrip("/").split("/")[-1].replace(".git", "")
    else:
        source = Path(target).resolve()
        if not source.exists():
            raise FileNotFoundError(f"Target path not found: {target}")
        if source.suffix == ".zip":
            loader.load_archive(source)
            repo_path = None
        else:
            loader.load_directory(source)
            repo_path = source if source.is_dir() else None
        proj_name = name or source.name

    # Run local heuristic analysis (skip AI API calls)
    engine = AnalysisEngine(config=cfg, loader=loader)
    analysis_result = engine.run(
        project_name=proj_name,
        repo_path=repo_path,
        skip_git=skip_git,
        skip_ai=True,
    )

    # Compute snapshot_sha256 from sorted manifest entries
    sorted_manifest = sorted(loader.manifest, key=lambda e: e["path"])
    hasher = hashlib.sha256()
    for entry in sorted_manifest:
        p = entry["path"]
        h = entry.get("content_hash", "")
        hasher.update(f"{p}:{h}\n".encode("utf-8"))
    snapshot_sha256 = hasher.hexdigest()

    # Build opaque file_id map (e.g. f_0001 -> rel_path)
    file_id_map = {
        f"f_{idx:04d}": entry["path"]
        for idx, entry in enumerate(sorted_manifest, start=1)
    }
    rel_path_to_id = {v: k for k, v in file_id_map.items()}

    audit_id = uuid.uuid4().hex[:16]
    session = AuditSession(
        audit_id=audit_id,
        project_name=proj_name,
        target=target_str,
        lang=lang,
        stage=stage,
        loader=loader,
        analysis_result=analysis_result,
        snapshot_sha256=snapshot_sha256,
        file_id_map=file_id_map,
        rel_path_to_id=rel_path_to_id,
    )

    with _SESSION_LOCK:
        _ACTIVE_SESSIONS[audit_id] = session

    code_analysis = analysis_result.code_analysis
    score_obj = analysis_result.score
    prov_score = score_obj.overall_score if score_obj else 0.0
    prov_grade = score_obj.grade if score_obj else "F"
    red_flags_cnt = (
        len(score_obj.red_flags)
        if (score_obj and score_obj.red_flags)
        else len(code_analysis.red_flags)
    )

    return {
        "audit_id": audit_id,
        "project_name": proj_name,
        "snapshot_sha256": snapshot_sha256,
        "lang": lang,
        "stage": stage,
        "files_analyzed": code_analysis.total_files or len(sorted_manifest),
        "total_lines": code_analysis.total_lines,
        "provisional_score": prov_score,
        "provisional_grade": prov_grade,
        "red_flags_count": red_flags_cnt,
        "summary": (
            f"Analyzed {code_analysis.total_files} files "
            f"({code_analysis.total_lines} lines of code). "
            f"Provisional score: {prov_score:.1f} ({prov_grade})."
        ),
    }


def list_evidence(
    audit_id: str,
    *,
    offset: int = 0,
    limit: int = 100,
) -> dict[str, Any]:
    """Return paginated list of codebase evidence files with opaque IDs.

    Args:
        audit_id: Active audit ID.
        offset: Zero-based starting index.
        limit: Number of items to return (clamped to 1..500).

    Returns:
        Paginated evidence list.
    """
    with _SESSION_LOCK:
        session = _get_session(audit_id)

    total = len(session.file_id_map)
    offset = max(0, int(offset))
    limit = max(1, min(500, int(limit)))

    entry_by_path = {e["path"]: e for e in session.loader.manifest}
    items: list[dict[str, Any]] = []

    for fid, rel_path in list(session.file_id_map.items())[offset : offset + limit]:
        info = entry_by_path.get(rel_path, {})
        items.append({
            "file_id": fid,
            "path": rel_path,
            "category": info.get("category", "other"),
            "size_bytes": info.get("size_bytes", 0),
            "sha256": info.get("content_hash", ""),
        })

    return {
        "audit_id": audit_id,
        "offset": offset,
        "limit": limit,
        "total": total,
        "evidence": items,
        "files": items,
    }


def read_evidence(
    audit_id: str,
    file_id: str,
    *,
    start_line: int = 1,
    max_lines: int = 200,
) -> dict[str, Any]:
    """Read a slice of source code or documentation using an opaque file ID.

    Args:
        audit_id: Active audit ID.
        file_id: Opaque file identifier (e.g. 'f_0001'). Raw paths are rejected.
        start_line: 1-based start line.
        max_lines: Maximum lines to read (clamped to 1..300).

    Returns:
        File slice dict with total lines and SHA-256 hash.
    """
    with _SESSION_LOCK:
        session = _get_session(audit_id)

    if not isinstance(file_id, str) or not re.match(r"^f_\d{4,}$", file_id):
        raise ValueError(f"Invalid file_id: '{file_id}'. Raw file paths are not permitted.")

    if file_id not in session.file_id_map:
        raise KeyError(f"File ID '{file_id}' not found in audit session '{audit_id}'")

    rel_path = session.file_id_map[file_id]
    start_line = max(1, int(start_line))
    max_lines = max(1, min(300, int(max_lines)))

    content = session.loader.read_file(rel_path)
    lines = content.splitlines()
    total_lines = len(lines)

    if total_lines == 0 or start_line > total_lines:
        sliced_text = ""
        end_line = total_lines
    else:
        end_line = min(total_lines, start_line + max_lines - 1)
        sliced_text = "\n".join(lines[start_line - 1 : end_line])

    entry = next((e for e in session.loader.manifest if e["path"] == rel_path), {})
    sha256 = entry.get("content_hash", "")

    return {
        "file_id": file_id,
        "path": rel_path,
        "start_line": start_line,
        "end_line": end_line,
        "total_lines": total_lines,
        "content": sliced_text,
        "sha256": sha256,
    }


def verify_sites(audit_id: str, urls: list[str]) -> dict[str, Any]:
    """Verify up to 3 marketing or documentation URLs and attach findings.

    Args:
        audit_id: Active audit ID.
        urls: List of web URLs to scrape and verify.

    Returns:
        Structured site verification summary.
    """
    with _SESSION_LOCK:
        session = _get_session(audit_id)

    target_urls = urls[:3]
    analyzer = SiteAnalyzer()
    scorer = SiteScorer()

    site_results = []
    site_scores = []

    for u in target_urls:
        sr = analyzer.analyze(u)
        sc = scorer.score(sr)
        site_results.append(sr)
        site_scores.append(sc)

    if site_results:
        primary = site_results[0]
        claims = [
            SiteClaimModel(
                claim_type=c.claim_type,
                claim=c.claim,
                source_url=c.source_url,
                confidence=c.confidence,
            )
            for c in primary.claims
        ]
        session.analysis_result.site_analysis = SiteAnalysisModel(
            site_url=primary.site_url,
            pages_analyzed=primary.pages_analyzed,
            claims=claims,
            technologies_mentioned=primary.technologies_mentioned,
            traction_claims=primary.traction_claims,
            findings=primary.findings,
            red_flags=primary.red_flags,
        )

    return {
        "audit_id": audit_id,
        "urls_verified": [sr.site_url for sr in site_results],
        "results": [
            {
                "url": sr.site_url,
                "pages_analyzed": sr.pages_analyzed,
                "technologies": sr.technologies_mentioned,
                "score": sc.overall_score,
                "grade": sc.grade,
                "red_flags": len(sr.red_flags),
            }
            for sr, sc in zip(site_results, site_scores)
        ],
    }


def validate_report(
    audit_id: str,
    snapshot_sha256: str,
    report_data: dict[str, Any] | None = None,
    *,
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a consulting report submission against codebase snapshot.

    Args:
        audit_id: Active audit ID.
        snapshot_sha256: Codebase SHA-256 fingerprint generated during prepare_audit.
        report_data: Raw consulting report dictionary.
        report: Alias for report_data (used by MCP dde_validate_report tool).

    Returns:
        Validation outcome including validation_id, score, grade, errors, and warnings.
    """
    payload = report_data if report_data is not None else (report or {})
    with _SESSION_LOCK:
        session = _get_session(audit_id)

    if snapshot_sha256 != session.snapshot_sha256:
        return {
            "valid": False,
            "error_code": "SNAPSHOT_MISMATCH",
            "errors": [
                f"Snapshot mismatch: expected {session.snapshot_sha256}, got {snapshot_sha256}"
            ],
            "warnings": [],
        }

    is_valid, errors, warnings = validate_consulting_submission(payload)
    if not is_valid:
        return {
            "valid": False,
            "error_code": "VALIDATION_FAILED",
            "errors": errors,
            "warnings": warnings,
        }

    cr = parse_consulting_dict(payload)
    validation_id = uuid.uuid4().hex[:16]

    with _SESSION_LOCK:
        session.validated_reports[validation_id] = cr

    return {
        "valid": True,
        "validation_id": validation_id,
        "overall_score": cr.overall_score,
        "grade": cr.grade,
        "warnings": warnings,
        "errors": [],
    }


def render_report(
    audit_id: str,
    validation_id: str,
    *,
    output_dir: str | Path | None = None,
    lang: str | None = None,
) -> dict[str, Any]:
    """Render a validated consulting report into a publication-grade PDF atomically.

    Args:
        audit_id: Active audit ID.
        validation_id: Identifier returned by validate_report.
        output_dir: Target destination directory (defaults to cwd / 'dde_output').
        lang: Target language code override (e.g. 'ja', 'en').

    Returns:
        Metadata dictionary with pdf_path, sha256, and byte size.
    """
    with _SESSION_LOCK:
        session = _get_session(audit_id)
        if validation_id not in session.validated_reports:
            raise KeyError(
                f"Validation ID '{validation_id}' not found for audit session '{audit_id}'"
            )
        cr = session.validated_reports[validation_id]

    use_lang = lang or session.lang or "en"
    dest_dir = Path(output_dir) if output_dir else Path.cwd() / "dde_output"
    dest_dir.mkdir(parents=True, exist_ok=True)

    clean_name = re.sub(r"[^\w\-]", "_", session.project_name.lower()) or "report"
    final_path = dest_dir / f"{clean_name}_technical_dd_{use_lang}.pdf"

    # Attach the consulting report to analysis_result
    res = session.analysis_result
    res.consulting_report = cr

    # Generate to an atomic temporary file in the destination directory
    fd, tmp_path_str = tempfile.mkstemp(
        prefix="dde_pdf_", suffix=".tmp", dir=str(dest_dir)
    )
    os.close(fd)
    tmp_path = Path(tmp_path_str)

    try:
        PDFReportGenerator().generate_to_file(res, tmp_path, lang=use_lang)
        os.replace(tmp_path, final_path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise

    pdf_bytes = final_path.read_bytes()
    sha256_hex = hashlib.sha256(pdf_bytes).hexdigest()
    size_bytes = len(pdf_bytes)

    return {
        "pdf_path": str(final_path),
        "sha256": sha256_hex,
        "bytes": size_bytes,
        "lang": use_lang,
    }


def close_audit(audit_id: str) -> dict[str, Any]:
    """Close an active audit session and cryptographically shred decrypted temp files.

    Args:
        audit_id: Audit ID to terminate.

    Returns:
        Status dictionary confirming cleanup and overwritten byte counts.
    """
    with _SESSION_LOCK:
        session = _get_session(audit_id)
        _ACTIVE_SESSIONS.pop(audit_id, None)
        session.is_closed = True

    bytes_overwritten = session.loader.destroy()

    return {
        "audit_id": audit_id,
        "closed": True,
        "cleanup_status": "complete",
        "bytes_overwritten": bytes_overwritten,
    }
