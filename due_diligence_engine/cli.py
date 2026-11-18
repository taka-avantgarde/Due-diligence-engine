"""Click CLI for the Due Diligence Engine.

Commands:
  analyze     - Run due diligence on a project directory or zip
  prompt      - Generate AI evaluation prompt for IDE terminals
  report      - Generate report from a previous analysis
  purge       - Securely delete analysis data
  leaderboard - Show scoring leaderboard across analyses
  doctor      - Diagnose the local environment for running DDE
  mcp         - Start the native Model Context Protocol (MCP) server
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from due_diligence_engine import __version__
from due_diligence_engine.config import Config, get_config

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="dde")
def cli() -> None:
    """Due Diligence Engine - AI startup technical due diligence."""
    pass


@cli.command()
@click.argument("target")
@click.option("--name", "-n", default=None, help="Project name (auto-detected from URL/path if omitted)")
@click.option("--output", "-o", type=click.Path(), default=None, help="Output directory")
@click.option("--skip-git", is_flag=True, help="Skip git forensics analysis")
@click.option("--skip-ai", is_flag=True, help="Skip AI-enhanced analysis (local only)")
@click.option("--format", "-f", "formats", multiple=True, default=["md", "html"],
              type=click.Choice(["md", "html", "sarif"]), help="Output formats (default: md, html; optional: sarif)")
def analyze(
    target: str,
    name: str | None,
    output: str | None,
    skip_git: bool,
    skip_ai: bool,
    formats: tuple[str, ...],
) -> None:
    """Run technical due diligence on a project.

    TARGET can be:

    \b
      GitHub URL:  https://github.com/owner/repo
      Short form:  owner/repo
      Local path:  /path/to/project
      Zip archive: /path/to/project.zip

    \b
    Examples:
      dde analyze https://github.com/langchain-ai/langchain
      dde analyze openai/whisper
      dde analyze ./my-startup-code
      dde analyze startup.zip
    """
    from due_diligence_engine.analyze.engine import AnalysisEngine
    from due_diligence_engine.ingest.secure_loader import SecureLoader
    from due_diligence_engine.report.generator import ReportGenerator
    from due_diligence_engine.report.slides import SlideGenerator

    config = get_config()

    if skip_ai:
        config.anthropic_api_key = ""

    errors = config.validate()
    if errors and not skip_ai:
        console.print(
            Panel(
                "\n".join(f"[red]- {e}[/red]" for e in errors),
                title="Configuration Errors",
                border_style="red",
            )
        )
        console.print("[yellow]Tip: Set ANTHROPIC_API_KEY or use --skip-ai[/yellow]")
        sys.exit(1)

    config.ensure_dirs()

    output_dir = Path(output) if output else config.output_dir

    # Detect target type: URL or local path
    is_url = _is_github_url(target)

    # Auto-detect project name
    if name is None:
        name = _extract_project_name(target)

    loader = SecureLoader(config)
    saved: list[Path] = []
    result = None

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Ingest
            task = progress.add_task("Ingesting project data...", total=None)

            try:
                if is_url:
                    progress.update(task, description=f"Cloning {target} ...")
                    loader.load_from_url(target)
                    repo_path = loader.cloned_repo_path
                else:
                    source = Path(target)
                    if not source.exists():
                        console.print(f"[red]Path not found: {target}[/red]")
                        console.print("[yellow]Tip: Did you mean a GitHub URL? Try: dde analyze owner/repo[/yellow]")
                        sys.exit(1)
                    if source.suffix == ".zip":
                        loader.load_archive(source)
                        repo_path = None
                    else:
                        loader.load_directory(source)
                        repo_path = source if source.is_dir() else None
            except (FileNotFoundError, ValueError, RuntimeError) as e:
                console.print(f"[red]Ingestion error: {e}[/red]")
                sys.exit(1)

            progress.update(task, description=f"Ingested {len(loader.manifest)} files")

            # Analyze
            progress.update(task, description="Running analysis...")
            engine = AnalysisEngine(config, loader)
            result = engine.run(
                project_name=name,
                repo_path=repo_path,
                skip_git=skip_git,
                skip_ai=skip_ai,
            )
            progress.update(task, description="Analysis complete")

            # Generate reports
            progress.update(task, description="Generating reports...")
            report_gen = ReportGenerator()
            saved = report_gen.save_report(result, output_dir, formats=list(formats))

            # Generate slides
            slide_gen = SlideGenerator()
            safe_name = name.replace("/", "_").replace("\\", "_")
            safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", result.analysis_id)
            slide_path = output_dir / f"dde_slides_{safe_name}_{safe_id}.html"
            slide_gen.save(result, slide_path)
            saved.append(slide_path)

            progress.update(task, description="Done!")
    finally:
        # Cleanup workspace (cryptographic purge)
        loader.destroy()

    # Display results
    if result:
        score = result.score
        if score:
            _display_score_summary(result, score)

        console.print()
        console.print("[bold]Generated Reports:[/bold]")
        for p in saved:
            console.print(f"  [cyan]{p}[/cyan]")

        if result.total_cost_usd > 0:
            console.print(f"\n[dim]API cost: ${result.total_cost_usd:.4f}[/dim]")


_ALL_20_LANGS = [
    "en", "ja", "es", "fr", "de", "pt", "nl", "it", "id",
    "zh", "zh-tw", "ko", "vi", "th", "ar", "hi", "tr", "pl", "ru", "sv",
]


@cli.command()
@click.argument("target", default=".", required=False)
@click.option("--name", "-n", default=None, help="Project name (auto-detected if omitted)")
@click.option("--lang", "-l", default="en", type=click.Choice(_ALL_20_LANGS),
              help="Report language — 20 supported: en/ja/es/fr/de/pt/nl/it/id/zh/zh-tw/ko/vi/th/ar/hi/tr/pl/ru/sv")
@click.option("--stage", "-s", default="unknown",
              type=click.Choice(["seed", "series_a", "series_b", "growth", "unknown"]),
              help="Startup development stage (adjusts evaluation criteria)")
@click.option("--output", "-o", type=click.Path(), default=None,
              help="Save prompt to file instead of stdout")
@click.option("--copy", "-c", is_flag=True, help="Copy prompt to clipboard")
@click.option("--skip-git", is_flag=True, help="Skip git forensics analysis")
@click.option("--pdf", "-p", is_flag=True,
              help="Generate consulting-grade PDF (requires AI terminal like Claude Code)")
@click.option("--url", "-u", "urls", multiple=True,
              help="Product/service URL for site verification (up to 3, repeatable)")
@click.option("--format", "-f", "prompt_format", default="default",
              type=click.Choice(["default", "blueprint", "md", "html"], case_sensitive=False),
              help="Prompt output style (default/blueprint include 5-dim scores & remediation patches automatically)")
@click.option("--emit-patch/--no-emit-patch", default=True,
              help="Include concrete remediation patch proposals (enabled by default)")
@click.option(
    "--industry",
    default="auto",
    type=click.Choice(
        ["auto", "messaging_cyber", "fintech", "medical", "ai_agent", "gaming", "enterprise_saas"],
        case_sensitive=False,
    ),
    help="Industry-specific domain evaluation pack (auto-detected if 'auto')",
)
def prompt(
    target: str,
    name: str | None,
    lang: str,
    stage: str,
    output: str | None,
    copy: bool,
    skip_git: bool,
    pdf: bool,
    urls: tuple[str, ...],
    prompt_format: str = "default",
    emit_patch: bool = True,
    industry: str = "auto",
) -> None:
    """Generate an AI evaluation prompt for IDE terminals.

    Runs heuristic analysis (no AI API needed), then outputs a structured
    prompt that you can paste into Claude Code, Cursor, GitHub Copilot, etc.

    \b
    TARGET can be (defaults to current directory if omitted):
      GitHub URL:  https://github.com/owner/repo
      Short form:  owner/repo
      Local path:  /path/to/project (default: .)
      Zip archive: /path/to/project.zip

    \b
    Examples:
      dde prompt --pdf --lang ja             # Current dir → consulting PDF
      dde prompt owner/repo --pdf            # GitHub repo → consulting PDF
      dde prompt . --lang ja                 # Current dir, Japanese output
      dde prompt owner/repo --lang ja        # GitHub repo, Japanese output
      dde prompt ./my-startup -s seed -c     # Seed stage, copy to clipboard
    """
    from due_diligence_engine.analyze.engine import AnalysisEngine
    from due_diligence_engine.ingest.secure_loader import SecureLoader
    from due_diligence_engine.prompt.generator import generate_prompt

    # --pdf mode: ask language if not explicitly given AND stdin is a TTY
    if pdf:
        import os
        ctx = click.get_current_context()
        lang_source = ctx.get_parameter_source("lang")
        if lang_source != click.core.ParameterSource.COMMANDLINE:
            if os.isatty(sys.stdin.fileno()):
                _supported_langs = _ALL_20_LANGS
                console.print()
                console.print(
                    Panel(
                        "[bold]Which language for the PDF report?[/bold]\n"
                        "PDFレポートの出力言語を選択してください。\n\n"
                        "  [cyan]1[/cyan]  English (en)\n"
                        "  [cyan]2[/cyan]  日本語 (ja)\n"
                        "  [dim]Or enter code: es, fr, de, pt, nl, it, id, zh, zh-tw, ko, vi, th, ar, hi, tr, pl, ru, sv[/dim]",
                        title="Atlas DDE — Language / 言語 (20 supported)",
                        border_style="cyan",
                    )
                )
                choice = click.prompt(
                    "  Select / 選択 (1-2 or language code)",
                    type=click.Choice(["1", "2", *_supported_langs], case_sensitive=False),
                ).lower()
                lang = "en" if choice == "1" else ("ja" if choice == "2" else choice)
                console.print()
            # else: non-interactive — use default "en"

    # Site URLs: prefer --url flags; fall back to interactive prompt
    site_urls: list[str] = [u.strip() for u in urls[:3] if u.strip()]
    if pdf and not site_urls:
        # Only prompt interactively when no --url flags were given
        # AND stdin is a TTY (skip if piped / non-interactive)
        import os
        if os.isatty(sys.stdin.fileno()):
            console.print(
                Panel(
                    "[bold]Enter product/service URLs for site verification (up to 3)[/bold]\n"
                    "サイト検証用URLを入力してください（最大3つ、空白でスキップ）",
                    title="DDE — Site URLs",
                    border_style="cyan",
                )
            )
            for i in range(1, 4):
                url = click.prompt(f"  URL {i} (blank to skip / 空白でスキップ)", default="", show_default=False)
                if url.strip():
                    site_urls.append(url.strip())
                else:
                    break
    if site_urls:
        console.print(f"  [dim]{len(site_urls)} URL(s) registered[/dim]")
        console.print()

    config = get_config()
    # Force skip AI — prompt mode never calls AI APIs
    config.anthropic_api_key = ""
    config.ensure_dirs()

    is_url = _is_github_url(target)
    if name is None:
        name = _extract_project_name(target)

    loader = SecureLoader(config)
    result = None

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Collecting project data...", total=None)

            try:
                if is_url:
                    progress.update(task, description=f"Cloning {target} ...")
                    loader.load_from_url(target)
                    repo_path = loader.cloned_repo_path
                else:
                    source = Path(target)
                    if not source.exists():
                        console.print(f"[red]Path not found: {target}[/red]")
                        sys.exit(1)
                    if source.suffix == ".zip":
                        loader.load_archive(source)
                        repo_path = None
                    else:
                        loader.load_directory(source)
                        repo_path = source if source.is_dir() else None
            except (FileNotFoundError, ValueError, RuntimeError) as e:
                console.print(f"[red]Ingestion error: {e}[/red]")
                sys.exit(1)

            progress.update(task, description="Running heuristic analysis...")
            engine = AnalysisEngine(config, loader)
            result = engine.run(
                project_name=name,
                repo_path=repo_path,
                skip_git=skip_git,
                skip_ai=True,
            )
            if industry and industry.lower() != "auto":
                from due_diligence_engine.score.scorer import Scorer
                result.code_analysis.complexity_metrics["industry_override"] = industry.lower()
                result.code_analysis.complexity_metrics["industry_pack"] = Scorer.detect_industry_pack(
                    result, override_industry=industry.lower()
                )
            progress.update(task, description="Generating prompt...")
    finally:
        # Cleanup
        loader.destroy()

    # Generate the structured prompt
    if pdf:
        # --pdf mode: check if running inside an AI terminal
        if not _detect_ai_terminal():
            console.print(
                Panel(
                    "[bold yellow]⚠ AI terminal not detected[/bold yellow]\n\n"
                    "This command requires an AI-powered terminal to generate the PDF.\n"
                    "Please run inside one of:\n"
                    "  • [cyan]Claude Code[/cyan] (claude)\n"
                    "  • [cyan]Cursor[/cyan] Terminal\n"
                    "  • [cyan]GitHub Copilot[/cyan] Chat\n\n"
                    "Without AI, use: [dim]dde prompt owner/repo --lang ja[/dim] (prompt-only)",
                    title="DDE",
                    border_style="yellow",
                )
            )
            # Continue anyway — the user may know what they're doing
            console.print("[dim]Continuing anyway...[/dim]\n")

        from due_diligence_engine.prompt.generator import generate_consulting_prompt
        prompt_text = generate_consulting_prompt(result, lang=lang, stage=stage, urls=site_urls)
    else:
        prompt_text = generate_prompt(result, lang=lang, stage=stage)

    # Output
    if output:
        out_path = Path(output)
        out_path.write_text(prompt_text, encoding="utf-8")
        console.print(f"[green]Prompt saved to: {out_path}[/green]")
    else:
        # Print to stdout (use print, not console, to avoid Rich markup)
        print(prompt_text)

    if copy:
        try:
            import subprocess
            # Cross-platform clipboard: Windows (clip), macOS (pbcopy), Linux (xclip)
            if sys.platform == "win32":
                clip_cmd = ["clip"]
            elif sys.platform == "darwin":
                clip_cmd = ["pbcopy"]
            else:
                clip_cmd = ["xclip", "-selection", "clipboard"]
            process = subprocess.Popen(clip_cmd, stdin=subprocess.PIPE)
            process.communicate(prompt_text.encode("utf-8"))
            console.print("[green]Prompt copied to clipboard![/green]")
        except (FileNotFoundError, OSError):
            console.print("[yellow]Could not copy to clipboard (clip/pbcopy/xclip not found)[/yellow]")

    if not pdf:
        console.print(
            Panel(
                f"[bold]Next step[/bold]: Paste the prompt into your AI terminal\n"
                f"(Claude Code, Cursor, GitHub Copilot, etc.)\n\n"
                f"The AI will read the data and generate a full evaluation report.\n"
                f"[dim]No API keys needed — your IDE's AI handles the analysis.[/dim]",
                title="DDE Prompt Generated",
                border_style="green",
            )
        )
    # --pdf mode: no trailing panel — the prompt itself contains all instructions for the AI


@cli.command()
@click.argument("result_file", type=click.Path(exists=True), required=False, default=None)
@click.option("--format", "-f", "fmt", default="md", type=click.Choice(["md", "html"]))
@click.option("--output", "-o", type=click.Path(), default=None)
@click.option("--consulting", type=click.Path(exists=True), default=None,
              help="Consulting report JSON from AI evaluation (generates consulting-grade PDF)")
@click.option("--pdf", "-p", is_flag=True, help="Generate PDF output")
@click.option("--lang", "-l", default="en", type=click.Choice(_ALL_20_LANGS),
              help="PDF language — 20 supported: en/ja/es/fr/de/pt/nl/it/id/zh/zh-tw/ko/vi/th/ar/hi/tr/pl/ru/sv")
@click.option("--baseline", "-b", type=click.Path(exists=True), default=None,
              help="Previous AnalysisResult JSON file to compute historical score & Red Flag deltas")
def report(
    result_file: str | None,
    fmt: str,
    output: str | None,
    consulting: str | None,
    pdf: bool,
    lang: str,
    baseline: str | None = None,
) -> None:
    """Generate a report from a saved analysis result JSON.

    \b
    Standard mode:
      dde report result.json                    # Markdown report
      dde report result.json -f html            # HTML report

    \b
    Consulting mode (from AI evaluation):
      dde report --consulting ai_result.json --pdf --lang ja
    """
    from due_diligence_engine.models import AnalysisResult
    from due_diligence_engine.report.generator import ReportGenerator

    config = get_config()
    config.ensure_dirs()
    output_dir = Path(output) if output else config.output_dir

    if consulting:
        # Consulting PDF mode — always save to ~/Downloads
        from due_diligence_engine.prompt.response_parser import parse_consulting_json
        from due_diligence_engine.report.pdf_generator import PDFReportGenerator

        cr = parse_consulting_json(consulting)

        # Build a minimal AnalysisResult with consulting report attached
        if result_file:
            result_path = Path(result_file)
            data = json.loads(result_path.read_text(encoding="utf-8"))
            result = AnalysisResult(**data)
        else:
            result = AnalysisResult(
                project_name=cr.project_name or "unknown",
                analysis_id=cr.analysis_id or "consulting",
            )

        result.consulting_report = cr

        pdf_gen = PDFReportGenerator()
        m_slug = re.match(r"^dde_consulting_(.+)_\d{8}\.json$", Path(consulting).name)
        raw_name = m_slug.group(1) if m_slug else result.project_name
        safe_name = raw_name.replace("/", "_").replace("\\", "_")

        # Date stamp in filename (ja: 2026年04月02日, en: 2026-04-02).
        # NOTE: no non-ASCII inside strftime — on Windows it delegates to the
        # C runtime with the ANSI code page and raises UnicodeEncodeError.
        now = datetime.now()
        if lang == "ja":
            date_str = f"{now.year}年{now.month:02d}月{now.day:02d}日"
        else:
            date_str = now.strftime("%Y-%m-%d")

        # Use ~/Downloads as default output for consulting PDFs
        downloads_dir = Path.home() / "Downloads"
        consulting_output = Path(output) if output else downloads_dir
        consulting_output.mkdir(parents=True, exist_ok=True)
        pdf_path = consulting_output / f"dde_consulting_{safe_name}_{date_str}.pdf"
        pdf_gen.generate_to_file(result, pdf_path, lang=lang)

        console.print(
            Panel(
                f"[bold green]Consulting PDF generated![/bold green]\n\n"
                f"  [cyan]{pdf_path}[/cyan]\n\n"
                f"Grade: {cr.grade} | Score: {cr.overall_score:.0f}/100\n"
                f"AI Model: {cr.ai_model_used or 'unknown'}",
                title="DDE Consulting Report",
                border_style="green",
            )
        )
        return

    # Standard report mode
    if not result_file:
        console.print("[red]Error: RESULT_FILE is required (or use --consulting)[/red]")
        sys.exit(1)

    result_path = Path(result_file)
    data = json.loads(result_path.read_text(encoding="utf-8"))
    result = AnalysisResult(**data)

    if baseline:
        from due_diligence_engine.api import compute_historical_delta
        base_data = json.loads(Path(baseline).read_text(encoding="utf-8"))
        compute_historical_delta(result, base_data)

    report_gen = ReportGenerator()
    saved = report_gen.save_report(result, output_dir, formats=[fmt])

    if pdf:
        from due_diligence_engine.report.pdf_generator import PDFReportGenerator
        pdf_gen = PDFReportGenerator()
        safe_name = result.project_name.replace("/", "_").replace("\\", "_")
        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", result.analysis_id)
        pdf_path = output_dir / f"dde_report_{safe_name}_{safe_id}.pdf"
        pdf_gen.generate_to_file(result, pdf_path, lang=lang)
        saved.append(pdf_path)

    for p in saved:
        console.print(f"[green]Report saved: {p}[/green]")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--analysis-id", "-a", required=True, help="Analysis ID to purge")
@click.option("--project-name", "-n", default="unknown", help="Project name")
@click.option("--operator", default="cli_user", help="Operator name for certificate")
@click.option("--cert-output", "-c", type=click.Path(), default=None, help="Certificate output path")
@click.confirmation_option(prompt="Are you sure you want to securely purge this data?")
def purge(
    path: str,
    analysis_id: str,
    project_name: str,
    operator: str,
    cert_output: str | None,
) -> None:
    """Securely purge analysis data and generate a purge certificate."""
    from due_diligence_engine.purge.secure_delete import SecurePurger

    target = Path(path)
    purger = SecurePurger()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Securely purging data...", total=None)

        cert = purger.purge_directory(
            directory=target,
            analysis_id=analysis_id,
            project_name=project_name,
            operator=operator,
        )

        progress.update(task, description="Purge complete")

    console.print(
        Panel(
            f"Files purged: {cert.files_purged}\n"
            f"Bytes overwritten: {cert.bytes_overwritten:,}\n"
            f"Method: {cert.method}\n"
            f"Certificate ID: {cert.certificate_id}",
            title="Purge Certificate",
            border_style="green",
        )
    )

    if cert_output:
        cert_path = Path(cert_output)
    else:
        config = get_config()
        config.ensure_dirs()
        safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", analysis_id)
        cert_path = config.output_dir / f"purge_cert_{safe_id}.json"

    purger.export_certificate(cert, cert_path)
    console.print(f"[green]Certificate saved: {cert_path}[/green]")

    if cert.verification_hash in ("purge_incomplete", "directory_not_found"):
        if cert.verification_hash == "purge_incomplete":
            console.print(
                Panel(
                    "Purge incomplete: some files could not be securely deleted.",
                    title="Purge Error",
                    border_style="red",
                )
            )
            sys.exit(1)


@cli.command()
@click.option("--data-dir", type=click.Path(), default=None, help="Data directory with results")
def leaderboard(data_dir: str | None) -> None:
    """Show a scoring leaderboard across all completed analyses."""
    from due_diligence_engine.models import AnalysisResult

    config = get_config()
    search_dir = Path(data_dir) if data_dir else config.output_dir

    if not search_dir.exists():
        console.print("[yellow]No analysis data found.[/yellow]")
        return

    # Find all report files and extract scores
    entries: list[tuple[str, float, str, str]] = []

    for md_file in sorted(search_dir.glob("dde_report_*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
            # Parse score from the markdown header
            for line in content.splitlines():
                if "Overall Score:" in line:
                    parts = line.split("Overall Score:**")
                    if len(parts) >= 2:
                        score_part = parts[1].strip()
                        score_str = score_part.split("/")[0].strip()
                        grade_match = score_part.split("Grade: ")
                        grade = grade_match[1].rstrip(")") if len(grade_match) > 1 else "?"
                        # Extract project name from filename
                        fname = md_file.stem
                        proj_name = fname.replace("dde_report_", "").rsplit("_", 1)[0]
                        entries.append(
                            (proj_name, float(score_str), grade, str(md_file))
                        )
                    break
        except (ValueError, IndexError):
            continue

    if not entries:
        console.print("[yellow]No completed analyses found.[/yellow]")
        return

    # Sort by score descending
    entries.sort(key=lambda x: x[1], reverse=True)

    table = Table(title="Due Diligence Leaderboard")
    table.add_column("Rank", style="bold", width=6)
    table.add_column("Project", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Grade", justify="center")
    table.add_column("Report", style="dim")

    for i, (proj, score, grade, path) in enumerate(entries, 1):
        grade_color = {
            "A": "green", "B": "green", "C": "yellow", "D": "red", "F": "red",
        }.get(grade, "white")

        table.add_row(
            str(i),
            proj,
            f"{score:.1f}/100",
            f"[{grade_color}]{grade}[/{grade_color}]",
            Path(path).name,
        )

    console.print(table)


@cli.command()
def doctor() -> None:
    """Diagnose the local environment for running DDE.

    Runs self-checks (git, Python, bundled fonts, reportlab, ~/Downloads,
    AI terminal, optional AI SDKs, Arabic libs) and prints a status table.

    \b
    Exit code is non-zero ONLY when a hard requirement is missing
    (Python < 3.11, or reportlab not importable). Warnings and
    informational rows never fail the command.

    \b
    Example:
      dde doctor
    """
    import importlib.util
    import os
    import platform
    import shutil
    import subprocess
    import tempfile

    def _has(mod: str) -> bool:
        try:
            return importlib.util.find_spec(mod) is not None
        except (ImportError, ValueError):
            return False

    OK, WARN, FAIL, INFO = (
        "[green]OK[/green]", "[yellow]WARN[/yellow]",
        "[red]FAIL[/red]", "[cyan]INFO[/cyan]",
    )
    rows: list[tuple[str, str, str]] = []
    hard_fail = False

    # 1. git on PATH (+version) — WARN only
    if shutil.which("git"):
        try:
            out = subprocess.run(
                ["git", "--version"],
                capture_output=True, text=True, timeout=5, check=False,
            )
            rows.append(("git on PATH", OK, out.stdout.strip() or "version unknown"))
        except (OSError, subprocess.SubprocessError) as e:
            rows.append(("git on PATH", WARN, f"found but not runnable: {e}"))
    else:
        rows.append((
            "git on PATH", WARN,
            "not found - URL clone & git forensics unavailable "
            "(local paths + --skip-git still work)",
        ))

    # 2. Python >= 3.11 — HARD FAIL
    if sys.version_info >= (3, 11):
        rows.append(("Python >= 3.11", OK, platform.python_version()))
    else:
        hard_fail = True
        rows.append((
            "Python >= 3.11", FAIL,
            f"{platform.python_version()} (requires-python >= 3.11)",
        ))

    # 3. Bundled TTF fonts — WARN only (vi/th/ar; en/ja/CJK use CID fonts)
    font_dir = Path(__file__).resolve().parent / "report" / "fonts"
    expected = [
        "NotoSans-Regular.ttf", "NotoSansThai-Regular.ttf",
        "NotoNaskhArabic-Regular.ttf",
    ]
    missing = [
        f for f in expected
        if not (font_dir / f).is_file() or (font_dir / f).stat().st_size == 0
    ]
    if not missing:
        rows.append(("Bundled TTF fonts", OK, f"{len(expected)} present ({font_dir})"))
    else:
        rows.append((
            "Bundled TTF fonts", WARN,
            f"missing/empty: {', '.join(missing)} -> vi/th/ar PDFs will fail",
        ))

    # 4. reportlab importable — HARD FAIL (core PDF engine)
    if _has("reportlab"):
        try:
            import reportlab
            ver = getattr(reportlab, "Version", getattr(reportlab, "__version__", "?"))
        except Exception:
            ver = "?"
        rows.append(("reportlab", OK, f"v{ver}"))
    else:
        hard_fail = True
        rows.append(("reportlab", FAIL, "not importable - run: pip install -e ."))

    # 5. ~/Downloads writable/creatable — WARN only (-o overrides).
    # Path.home() itself raises RuntimeError (NOT OSError) when HOME is unset and
    # the UID has no passwd entry (minimal Docker/CI) — keep it inside the try so
    # doctor never crashes in exactly the broken environments it diagnoses.
    probe: Path | None = None
    try:
        downloads = Path.home() / "Downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".dde_doctor_", dir=str(downloads))
        os.close(fd)
        probe = Path(tmp)
        rows.append(("~/Downloads writable", OK, str(downloads)))
    except (OSError, RuntimeError) as e:
        rows.append((
            "~/Downloads writable", WARN,
            f"~/Downloads not resolvable/writable ({e}); pass -o to override",
        ))
    finally:
        if probe is not None:
            probe.unlink(missing_ok=True)

    # 6. AI terminal — INFO only (reuse existing helper)
    if _detect_ai_terminal():
        rows.append((
            "AI terminal", INFO,
            "detected (Claude Code / Codex / Gemini CLI / Antigravity / Cursor / VS Code)",
        ))
    else:
        rows.append((
            "AI terminal", INFO,
            "not detected - standalone shell (best-effort; --pdf still runs)",
        ))

    # 7. Optional BYOK AI SDKs — INFO only (absence is NOT a failure)
    sdks = {
        "anthropic": "anthropic", "openai": "openai",
        "google-genai": "google.genai",
    }
    present = [d for d, m in sdks.items() if _has(m)]
    absent = [d for d in sdks if d not in present]
    detail = "present: " + (", ".join(present) or "none")
    if absent:
        detail += " | absent: " + ", ".join(absent) + " (BYOK AI-key mode only)"
    rows.append(("BYOK AI SDKs", INFO, detail))

    # 8. Arabic rendering libs — WARN only.
    # Import names differ from dist names: arabic-reshaper -> arabic_reshaper,
    # python-bidi -> bidi.
    ar_missing = [
        d for d, m in (("arabic-reshaper", "arabic_reshaper"),
                       ("python-bidi", "bidi")) if not _has(m)
    ]
    if not ar_missing:
        rows.append(("Arabic libs", OK, "arabic-reshaper + python-bidi present"))
    else:
        rows.append((
            "Arabic libs", WARN,
            f"missing: {', '.join(ar_missing)} -> Arabic (ar) reports won't shape/RTL",
        ))

    # ---- Render ----
    table = Table(title="DDE Environment Doctor")
    table.add_column("Check", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim", overflow="fold")
    for check, status, det in rows:
        table.add_row(check, status, det)
    console.print(table)

    warn_count = sum(1 for _, s, _ in rows if s == WARN)
    if hard_fail:
        console.print(Panel(
            "[bold red]One or more hard requirements are missing.[/bold red]\n"
            "DDE cannot generate reports until the FAIL rows above are resolved.",
            title="Doctor: FAIL", border_style="red"))
        sys.exit(1)
    elif warn_count:
        console.print(Panel(
            f"[yellow]{warn_count} warning(s).[/yellow] Core PDF workflow is functional; "
            "some optional features are degraded (see WARN rows).",
            title="Doctor: OK (with warnings)", border_style="yellow"))
    else:
        console.print(Panel(
            "[bold green]All checks passed.[/bold green] Environment is fully configured.",
            title="Doctor: OK", border_style="green"))


@cli.command("mcp")
@click.option("--transport", default="stdio", type=click.Choice(["stdio"]), help="MCP transport protocol (default: stdio)")
def mcp_cmd(transport: str) -> None:
    """Start the Atlas DDE MCP server over stdio."""
    from due_diligence_engine.mcp_server import run_stdio_mcp_server
    run_stdio_mcp_server()


@cli.command("batch")
@click.argument("targets", nargs=-1, required=True)
@click.option("--output-dir", "-o", type=click.Path(), default=None, help="Output directory for batch comparison reports")
@click.option("--lang", "-l", default="en", type=click.Choice(_ALL_20_LANGS), help="Report language (20 supported)")
@click.option("--pdf/--no-pdf", "-p", default=True, help="Generate 1-Page Executive Portfolio Batch Comparison PDF (default: enabled)")
@click.option("--skip-git", is_flag=True, help="Skip git forensics analysis")
def batch_cmd(
    targets: tuple[str, ...],
    output_dir: str | None,
    lang: str,
    pdf: bool,
    skip_git: bool,
) -> None:
    """Audit multiple repositories in one command and output a 1-Page Portfolio Comparison Matrix.

    \b
    Examples:
      dde batch ./repo-a ./repo-b --lang ja
      dde batch owner/repo1 owner/repo2 -o ~/Downloads --lang en
    """
    from due_diligence_engine.api import batch_audit

    summary = batch_audit(
        list(targets),
        lang=lang,
        skip_git=skip_git,
        output_dir=output_dir,
        render_pdf=pdf,
    )

    tbl = Table(
        title=f"Atlas DDE — Executive Portfolio Comparison ({summary['targets_audited']} Targets)",
        border_style="#0284c7",
    )
    tbl.add_column("#", justify="right", style="bold #0284c7")
    tbl.add_column("Project", style="bold")
    tbl.add_column("Grade", justify="center")
    tbl.add_column("Score", justify="right")
    tbl.add_column("Verdict", justify="center")
    tbl.add_column("Files / LOC", justify="right")
    tbl.add_column("Tests & CI", justify="center")
    tbl.add_column("Top Priority Risk")

    for row in summary["ranking"]:
        v = row["verdict"]
        v_col = "#059669" if v == "GO" else ("#d97706" if v == "CONDITIONAL" else "#e11d48")
        t_badge = (
            "[#059669]○ Tests+CI[/#059669]"
            if row["has_tests"] and row["has_ci_cd"]
            else ("[#d97706]△ Tests[/#d97706]" if row["has_tests"] else "[#e11d48]× None[/#e11d48]")
        )
        tbl.add_row(
            str(row["rank"]),
            row["project_name"],
            f"[{v_col}]{row['grade']}[/{v_col}]",
            f"[{v_col}]{row['overall_score']:.1f}/100[/{v_col}]",
            f"[bold {v_col}]{v}[/bold {v_col}]",
            f"{row['files_analyzed']} / {row['lines_of_code']:,}",
            t_badge,
            row["top_risk"],
        )

    console.print()
    console.print(tbl)
    console.print()
    console.print("[bold #0284c7]Generated Portfolio Comparison Reports:[/bold #0284c7]")
    if summary.get("pdf_path"):
        console.print(f"  [cyan]PDF : {summary['pdf_path']}[/cyan]")
    console.print(f"  [cyan]MD  : {summary['markdown_path']}[/cyan]")
    console.print(f"  [cyan]HTML: {summary['html_path']}[/cyan]")


@cli.command("sbom")
@click.argument("target", default=".", required=False)
@click.option("--output", "-o", type=click.Path(), default=None, help="Output CycloneDX 1.6 SBOM JSON file path")
def sbom_cmd(target: str, output: str | None) -> None:
    """Generate a U.S. EO 14028 CycloneDX 1.6 Software Bill of Materials (SBOM) JSON."""
    import json as _json
    from due_diligence_engine.api import generate_sbom

    bom = generate_sbom(target, output_path=output)
    if output:
        console.print(
            f"[bold #059669]✓ CycloneDX 1.6 SBOM generated:[/bold #059669] [cyan]{Path(output).resolve()}[/cyan] "
            f"([bold]{len(bom.get('components', []))}[/bold] components)"
        )
    else:
        click.echo(_json.dumps(bom, indent=2, ensure_ascii=False))


def _display_score_summary(result, score) -> None:
    """Display a Quiet Luxury Executive Summary & comparison tables in the terminal."""
    from due_diligence_engine.report.generator import (
        _determine_verdict,
        _extract_file_line,
        _extract_one_line_fix,
    )

    grade_colors = {
        "A": "#059669",
        "B": "#0284c7",
        "C": "#d97706",
        "D": "#e11d48",
        "F": "#e11d48",
    }
    color = grade_colors.get(score.grade, "#0284c7")
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    sorted_flags = sorted(
        score.red_flags,
        key=lambda f: sev_order.get(getattr(f.severity, "value", str(f.severity)).lower(), 99),
    )
    has_critical = any(getattr(f.severity, "value", "") == "critical" for f in sorted_flags)
    verdict = _determine_verdict(score.overall_score, has_critical)
    verdict_style = "#059669" if verdict == "GO" else ("#d97706" if verdict == "CONDITIONAL" else "#e11d48")

    top_risks = "\n".join(
        f"  • [{getattr(f.severity, 'value', '').upper()}] {f.title} ({_extract_file_line(f)})"
        for f in sorted_flags[:3]
    ) or "  • None — zero code-verified blockers detected"

    # 1. Executive Summary Hero Panel
    console.print()
    console.print(
        Panel(
            f"[bold {color}]Grade {score.grade}  ·  {score.overall_score:.0f} / 100[/bold {color}]   "
            f"[bold {verdict_style}][ {verdict} ][/bold {verdict_style}]\n"
            f"[dim]{score.recommendation}[/dim]\n\n"
            f"[bold #0284c7]Top Priority Risks (Max 3):[/bold #0284c7]\n{top_risks}",
            title=f"Atlas DDE — Executive Summary: {result.project_name}",
            border_style="#0284c7",
            padding=(1, 2),
        )
    )

    # 2. Standard 5-Dimension Score Table
    table = Table(title="1. Standard 5-Dimension Score Table (20% Equal Weights)", border_style="#0284c7")
    table.add_column("Dimension", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Weight", justify="right")
    table.add_column("Weighted", justify="right")

    for dim in score.dimensions:
        sc_color = "#059669" if dim.score >= 75 else ("#0284c7" if dim.score >= 60 else ("#d97706" if dim.score >= 40 else "#e11d48"))
        table.add_row(
            dim.name,
            f"[{sc_color}]{dim.score:.0f}/100[/{sc_color}]",
            f"{dim.weight:.0%}",
            f"{dim.weighted_score:.1f}",
        )

    console.print(table)

    # 3. Atlas 4-Axis Assessment Table (20 / 20 / 5 / 55)
    code = result.code_analysis
    consistency = result.consistency
    atlas_tbl = Table(title="2. Atlas 4-Axis Assessment (20 / 20 / 5 / 55)", border_style="#0284c7")
    atlas_tbl.add_column("Atlas Axis", style="bold")
    atlas_tbl.add_column("Weight", justify="right")
    atlas_tbl.add_column("Assessment", justify="left")
    atlas_tbl.add_row("Performance & Concurrency", "20%", f"{score.overall_score:.0f}/100 Baseline")
    atlas_tbl.add_row(
        "Stability & Test Hygiene",
        "20%",
        "[#059669]○ Tests + CI[/#059669]" if code.has_tests and code.has_ci_cd else ("[#d97706]△ Tests Only[/#d97706]" if code.has_tests else "[#e11d48]× No Tests[/#e11d48]"),
    )
    atlas_tbl.add_row("Lightweight & Dependencies", "5%", f"{code.dependency_count} deps · {code.api_wrapper_ratio:.0%} wrapper")
    atlas_tbl.add_row("[bold #0284c7]Security & Crypto Strength[/bold #0284c7]", "55%", f"{consistency.consistency_score:.0f}% Claim-to-Code Integrity")
    console.print(atlas_tbl)

    # 4. Company Claim vs. Code Evidence 2-Column Table
    claim_tbl = Table(title="3. Company Claim vs. Code Evidence", border_style="#0284c7")
    claim_tbl.add_column("Web / Pitch Claim", ratio=1)
    claim_tbl.add_column("Code Evidence & Verdict Badge", ratio=1)
    rows_added = 0
    for c_text in consistency.verified_claims[:4]:
        claim_tbl.add_row(c_text, "[#059669]○ 実装済 (Verified)[/#059669] — Confirmed in AST/config")
        rows_added += 1
    for c_text in consistency.unverified_claims[:4]:
        claim_tbl.add_row(c_text, "[#d97706]△ 一部のみ (Unverified)[/#d97706] — ⚠️ No backing code")
        rows_added += 1
    for c_text in consistency.contradictions[:4]:
        claim_tbl.add_row(c_text, "[#e11d48]× 未実装 (Contradiction)[/#e11d48] — Contradicts repo")
        rows_added += 1
    if rows_added == 0:
        claim_tbl.add_row("Repository Baseline Integrity", f"[#059669]○ 実装済 (Verified)[/#059669] — {consistency.consistency_score:.0f}% ({code.total_files} files)")
    console.print(claim_tbl)

    # 5. Priority-Sorted Red Flags 4-Column Table
    if sorted_flags:
        rf_tbl = Table(title="4. Priority-Sorted Red Flags", border_style="#e11d48")
        rf_tbl.add_column("Severity", justify="center")
        rf_tbl.add_column("Target (file:line)")
        rf_tbl.add_column("Business Impact")
        rf_tbl.add_column("1-Line Fix Plan")
        for flag in sorted_flags:
            sev = getattr(flag.severity, "value", str(flag.severity)).lower()
            sev_badge = (
                "[bold #e11d48]CRITICAL[/bold #e11d48]"
                if sev == "critical"
                else ("[bold #d97706]⚠️ HIGH[/bold #d97706]" if sev == "high" else sev.upper())
            )
            rf_tbl.add_row(
                sev_badge,
                _extract_file_line(flag),
                f"{flag.title}: {flag.description[:80]}",
                _extract_one_line_fix(flag),
            )
        console.print(rf_tbl)


def _detect_ai_terminal() -> bool:
    """Best-effort detection of whether we're running inside an AI terminal."""
    import os
    # Claude Code sets CLAUDE_CODE or similar env vars
    if os.environ.get("CLAUDE_CODE"):
        return True
    # Codex CLI
    if os.environ.get("CODEX_SANDBOX") or os.environ.get("CODEX_CI"):
        return True
    # Gemini CLI / Antigravity
    if (
        os.environ.get("GEMINI_CLI")
        or os.environ.get("ANTIGRAVITY_CLI_ALIAS")
        or os.environ.get("ANTIGRAVITY_AGENT")
    ):
        return True
    # Cursor sets CURSOR_SESSION or TERM_PROGRAM contains "cursor"
    if os.environ.get("CURSOR_SESSION"):
        return True
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    if any(agent in term_program for agent in ("cursor", "claude", "codex", "gemini", "antigravity")):
        return True
    # Check if parent process name hints at AI terminal
    # (heuristic — not always reliable)
    if os.environ.get("VSCODE_GIT_ASKPASS_NODE"):
        # Running inside VS Code / Cursor terminal
        return True
    return False


def _is_github_url(target: str) -> bool:
    """Determine if the target looks like a GitHub URL or owner/repo shorthand."""
    target = target.strip()
    try:
        if Path(target).exists():
            return False
    except OSError:
        pass
    # Explicit URLs
    if target.startswith(("https://", "http://", "git@", "github.com/")):
        return True
    # Short form: owner/repo (no dots, no path separators beyond one slash)
    if re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", target):
        # Exclude local paths like ./foo or ../bar
        if not target.startswith((".", "/")):
            return True
    return False


def _extract_project_name(target: str) -> str:
    """Extract a human-readable project name from URL or path."""
    target = target.strip().rstrip("/")
    # Remove .git suffix
    target = re.sub(r"\.git$", "", target)
    # Remove /tree/branch suffix
    target = re.sub(r"/tree/.*$", "", target)
    # Get last path component
    name = target.rstrip("/").split("/")[-1]
    # Remove .git or .zip suffix again if present
    name = re.sub(r"\.git$", "", name)
    name = re.sub(r"\.zip$", "", name)
    return name or "unknown"


if __name__ == "__main__":
    cli()
