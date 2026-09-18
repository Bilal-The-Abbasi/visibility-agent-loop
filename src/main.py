"""
Main CLI Entrypoint: Website Visibility & AI Search Agent Loop
"""
import argparse
import os
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from src.orchestrator.pipeline import VisibilityPipeline


console = Console()


def print_banner():
    console.print(
        Panel.fit(
            "[bold cyan]🤖 Multi-Agent Website Visibility & Operations Loop[/bold cyan]\n"
            "[dim]Autonomous Pipeline: Auditor (SEO/AEO/GEO/AIO) ➔ Strategist ➔ Operator ➔ Loopback[/dim]",
            border_style="cyan"
        )
    )


def print_scores_table(title: str, scores, subtitle: str = ""):
    table = Table(title=title, title_style="bold magenta", border_style="dim")
    table.add_column("Optimization Dimension", style="cyan", justify="left")
    table.add_column("Score (0-100)", justify="center", style="bold")
    table.add_column("Status / Focus Area", style="italic")

    def score_badge(s: float):
        if s >= 80:
            return f"[green]{s}[/green]"
        elif s >= 50:
            return f"[yellow]{s}[/yellow]"
        return f"[red]{s}[/red]"

    table.add_row("Overall Visibility", score_badge(scores.overall), "Aggregated Weighted Index")
    table.add_row("Traditional SEO", score_badge(scores.seo), "Meta tags, Headings, Crawlability")
    table.add_row("AEO (Answer Engine)", score_badge(scores.aeo), "Direct Answers, Q&A, Voice Snippets")
    table.add_row("GEO (Generative Engine)", score_badge(scores.geo), "E-E-A-T, Source Authority, Stats")
    table.add_row("AIO (AI Overview)", score_badge(scores.aio), "JSON-LD Schemas, llms.txt, Summaries")

    console.print(table)


def print_comparison_table(before, after, delta):
    table = Table(title="🔄 Closed-Loop Re-Audit Verification", title_style="bold green", border_style="green")
    table.add_column("Dimension", style="cyan")
    table.add_column("Initial Score", justify="center")
    table.add_column("Optimized Score", justify="center")
    table.add_column("Score Delta", justify="center", style="bold")

    for key, name in [
        ("overall", "Overall Visibility"),
        ("seo", "Traditional SEO"),
        ("aeo", "AEO (Answer Engine)"),
        ("geo", "GEO (Generative Engine)"),
        ("aio", "AIO (AI Overview)"),
    ]:
        b = getattr(before, key)
        a = getattr(after, key)
        d = delta.get(key, 0.0)
        d_str = f"[green]+{d}[/green]" if d > 0 else (f"[red]{d}[/red]" if d < 0 else f"[dim]{d}[/dim]")
        table.add_row(name, f"{b}", f"{a}", d_str)

    console.print(table)


def main():
    parser = argparse.ArgumentParser(
        description="Autonomous Multi-Agent Loop for Website Visibility (SEO, AEO, GEO, AIO) & Operations."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", type=str, help="Target website URL to audit and optimize.")
    group.add_argument("--file", type=str, help="Path to local HTML file to audit and optimize.")
    group.add_argument("--demo", action="store_true", help="Run the pipeline on the included demo site.")

    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Directory to save generated reports and technical artifacts (default: ./output)"
    )
    parser.add_argument(
        "--no-loopback",
        action="store_true",
        help="Skip loopback verification re-audit."
    )

    args = parser.parse_args()
    print_banner()

    target = None
    raw_html = None

    if args.demo:
        demo_path = os.path.join(os.path.dirname(__file__), "..", "samples", "sample_site.html")
        target = os.path.abspath(demo_path)
        console.print(f"[bold yellow]▶ Mode:[/bold yellow] Demo Sample Website ([dim]{target}[/dim])")
    elif args.file:
        target = os.path.abspath(args.file)
        console.print(f"[bold yellow]▶ Mode:[/bold yellow] Local File ([dim]{target}[/dim])")
    elif args.url:
        target = args.url
        console.print(f"[bold yellow]▶ Mode:[/bold yellow] Live URL ([dim]{target}[/dim])")

    pipeline = VisibilityPipeline()

    console.print("\n[bold cyan]Step 1: Agent 1 (AuditorAgent)[/bold cyan] is analyzing target...")
    result = pipeline.run_loop(
        target=target,
        output_dir=args.output_dir,
        perform_loopback=not args.no_loopback,
    )

    # Display Initial Audit Scores
    console.print("\n[bold]Initial Audit Results:[/bold]")
    print_scores_table("📊 Initial Visibility Baseline", result.initial_audit.scores)

    # Critical Findings
    criticals = result.initial_audit.get_findings_by_severity("critical")
    if criticals:
        console.print(f"\n[bold red]🚨 Critical Visibility Deficiencies Found ({len(criticals)}):[/bold red]")
        for c in criticals:
            console.print(f"  • [bold][{c.category.upper()}][/bold] {c.name}: [dim]{c.description}[/dim]")

    # Display Strategic Plan
    console.print(f"\n[bold cyan]Step 2: Agent 2 (StrategistAgent)[/bold cyan] formulated [bold]{len(result.action_plan.recommendations)}[/bold] strategic initiatives:")
    for rec in result.action_plan.recommendations:
        console.print(f"  • [bold magenta][{rec.id}][/bold magenta] [bold]{rec.title}[/bold] ([dim]{rec.priority.upper()} priority[/dim])")
        console.print(f"    [dim]Impact:[/dim] {rec.expected_impact}")

    # Display Operations
    console.print(f"\n[bold cyan]Step 3: Agent 3 (OperatorAgent)[/bold cyan] manufactured [bold]{len(result.operation_result.artifacts)}[/bold] deliverables:")
    for art in result.operation_result.artifacts:
        console.print(f"  • [bold green]✓[/bold green] [bold]{art.name}[/bold] ➔ [cyan]`{os.path.join(args.output_dir, art.file_path)}`[/cyan]")

    # Loopback Verification
    if result.re_audit and result.score_delta:
        console.print("\n[bold cyan]Step 4: Loopback Verification Agent[/bold cyan] re-audited the patched asset:")
        print_comparison_table(result.initial_audit.scores, result.re_audit.scores, result.score_delta)

    console.print(f"\n[bold green]✔ Pipeline Run Complete![/bold green] All artifacts and reports exported to [bold cyan]{args.output_dir}/[/bold cyan]\n")


if __name__ == "__main__":
    main()
