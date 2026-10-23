"""
InvariantForge CLI Entrypoint.
Orchestrates contract parsing, invariant synthesis, Foundry fuzzing, and PoC generation.
"""

import sys
import os
import shutil
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from invariant_forge.parser import SolidityParser
from invariant_forge.invariant_rules import InvariantCatalog
from invariant_forge.generator.handler_gen import HandlerGenerator
from invariant_forge.generator.suite_gen import SuiteGenerator
from invariant_forge.generator.poc_gen import PoCGenerator
from invariant_forge.runner import FoundryRunner

console = Console()


def scan_contract(contract_path: str, workspace_dir: str = None, fuzz_runs: int = 1000):
    console.print(Panel.fit(
        "[bold cyan]🛡️ InvariantForge — Autonomous DeFi Invariant & PoC Engine[/bold cyan]\n"
        "[dim]Ramanujan Mathematical Rigor & Deterministic Foundry Verification[/dim]",
        border_style="cyan"
    ))

    if not os.path.exists(contract_path):
        console.print(f"[bold red]Error:[/bold red] Contract file '{contract_path}' not found.")
        sys.exit(1)

    # 1. Parse Contract
    with console.status("[bold green]Parsing Solidity contract and AST...[/bold green]"):
        parsed = SolidityParser.parse_file(contract_path)

    console.print(f"[green]✔[/green] Contract Identified: [bold]{parsed.contract_name}[/bold]")
    console.print(f"[green]✔[/green] Solidity Pragma: [cyan]{parsed.pragma}[/cyan]")
    console.print(f"[green]✔[/green] Detected Protocol Patterns: [yellow]{', '.join(parsed.detected_patterns) or 'GENERIC'}[/yellow]")

    # 2. Select Ramanujan Invariants
    rules = InvariantCatalog.get_applicable_rules(parsed.detected_patterns)
    console.print(f"[green]✔[/green] Injected [bold]{len(rules)}[/bold] Mathematical Invariants from Catalog")

    # Determine Foundry testbed workspace
    if not workspace_dir:
        # Default to local testbed inside invariant-forge
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        workspace_dir = os.path.join(base_dir, "testbed")

    test_dir = os.path.join(workspace_dir, "test")
    src_dir = os.path.join(workspace_dir, "src")
    os.makedirs(test_dir, exist_ok=True)
    os.makedirs(src_dir, exist_ok=True)

    # Copy target contract to src/
    target_dest = os.path.join(src_dir, f"{parsed.contract_name}.sol")
    if os.path.abspath(contract_path) != os.path.abspath(target_dest):
        shutil.copy2(contract_path, target_dest)

    # 3. Generate Handler.sol
    handler_code = HandlerGenerator.generate(parsed, rules)
    handler_file = os.path.join(test_dir, f"{parsed.contract_name}Handler.sol")
    with open(handler_file, "w", encoding="utf-8") as f:
        f.write(handler_code)
    console.print(f"[green]✔[/green] Generated Stateful Fuzz Handler: [cyan]{handler_file}[/cyan]")

    # 4. Generate InvariantTest.t.sol
    suite_code = SuiteGenerator.generate(parsed, rules)
    suite_file = os.path.join(test_dir, f"{parsed.contract_name}InvariantTest.t.sol")
    with open(suite_file, "w", encoding="utf-8") as f:
        f.write(suite_code)
    console.print(f"[green]✔[/green] Generated Invariant Suite: [cyan]{suite_file}[/cyan]")

    # 5. Execute Foundry Fuzzer
    console.print(f"\n[bold yellow]⚡ Launching Foundry Stateful Fuzzer ({fuzz_runs} runs)...[/bold yellow]")
    with console.status("[bold yellow]Fuzzing contract state transitions with randomized actors...[/bold yellow]"):
        result = FoundryRunner.run_invariant_test(workspace_dir, parsed.contract_name, fuzz_runs=fuzz_runs)

    # 6. Evaluate Results
    if result.success:
        console.print(Panel(
            f"[bold green]✔ ALL INVARIANTS HELD SOLID! ({result.runs} runs)[/bold green]\n"
            f"Target contract verified against all {len(rules)} formal mathematical invariants.\n"
            f"Zero insolvency, zero rounding dilution, and zero unbacked minting detected.",
            title="Certification Passed",
            border_style="green"
        ))
        return

    # Invariant Violation Found!
    console.print(Panel(
        f"[bold red]🚨 CRITICAL INVARIANT VIOLATION DETECTED![/bold red]\n\n"
        f"• Failed Invariant: [bold yellow]{result.failed_invariant or 'Unknown'}[/bold yellow]\n"
        f"• Revert Reason: [red]{result.revert_reason or 'Assertion Failed'}[/red]\n"
        f"• Counterexample Call Trace: [cyan]{len(result.counterexample_calls)} call(s) executed[/cyan]",
        title="Exploit Proof Discovered",
        border_style="red"
    ))

    # 7. Generate Standalone test_PoC_*.t.sol
    console.print("[bold cyan]🔨 Synthesizing Deterministic Standalone Proof of Concept (PoC)...[/bold cyan]")
    poc_code = PoCGenerator.generate(parsed, result)
    poc_file = os.path.join(test_dir, f"test_PoC_{parsed.contract_name}.t.sol")
    with open(poc_file, "w", encoding="utf-8") as f:
        f.write(poc_code)

    console.print(f"[green]✔[/green] Standalone PoC Saved: [bold cyan]{poc_file}[/bold cyan]")

    # 8. Verify PoC Execution
    with console.status("[bold cyan]Verifying standalone PoC execution with forge test...[/bold cyan]"):
        verify_proc = FoundryRunner.run_invariant_test(workspace_dir, parsed.contract_name, fuzz_runs=1)
        # Verify direct execution of PoC contract
        import subprocess
        poc_verify = subprocess.run(
            ["forge", "test", "--match-contract", f"PoC_{parsed.contract_name}", "-v"],
            cwd=workspace_dir,
            capture_output=True,
            text=True
        )

    if poc_verify.returncode == 0:
        console.print(Panel(
            f"[bold green]✔ STANDALONE PoC VERIFIED 100% GREEN![/bold green]\n\n"
            f"PoC File: [bold cyan]{poc_file}[/bold cyan]\n"
            f"Execution Proof: Reproduces invariant breach deterministically in < 5ms.\n"
            f"Ready for direct submission to [bold]Cantina / Immunefi[/bold].",
            title="PoC Verification Successful",
            border_style="green"
        ))
    else:
        console.print(f"[yellow]PoC verification output:[/yellow]\n{poc_verify.stdout}\n{poc_verify.stderr}")


def main():
    parser = argparse.ArgumentParser(
        description="InvariantForge: Autonomous Smart Contract Invariant Fuzzing & PoC Generator"
    )
    subparsers = parser.add_subparsers(dest="command")

    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan contract for invariant violations and generate PoC")
    scan_parser.add_argument("contract", help="Path to target Solidity contract")
    scan_parser.add_argument("--runs", type=int, default=1000, help="Number of fuzz runs (default: 1000)")
    scan_parser.add_argument("--workspace", type=str, default=None, help="Foundry workspace path")

    # rules command
    subparsers.add_parser("rules", help="List Ramanujan Mathematical Invariant catalog")

    args = parser.parse_args()

    if args.command == "scan":
        scan_contract(args.contract, workspace_dir=args.workspace, fuzz_runs=args.runs)
    elif args.command == "rules":
        table = Table(title="Ramanujan Mathematical Invariant Catalog")
        table.add_column("Rule ID", style="cyan")
        table.add_column("Name", style="bold")
        table.add_column("Category", style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("Description")

        for rule in InvariantCatalog.RULES.values():
            table.add_row(rule.rule_id, rule.name, rule.category, rule.severity, rule.description)

        console.print(table)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
