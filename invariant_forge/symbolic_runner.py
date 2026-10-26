"""
Symbolic SMT Formal Verification Runner for InvariantForge.
Integrates Halmos with Z3 and Yices SMT Solvers to mathematically prove
invariants for ALL possible state transitions and synthesize counterexample models.
"""

import subprocess
import os
import re
import shutil
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class SymbolicCheckResult:
    function_name: str
    status: str  # "PASS", "FAIL", "TIMEOUT"
    paths_explored: int = 0
    time_seconds: float = 0.0
    counterexample_model: Dict[str, str] = field(default_factory=dict)


@dataclass
class SymbolicProofResult:
    success: bool
    contract_name: str
    solver_used: str
    total_passed: int = 0
    total_failed: int = 0
    total_timeout: int = 0
    total_time_seconds: float = 0.0
    checks: List[SymbolicCheckResult] = field(default_factory=list)
    raw_output: str = ""


class SymbolicRunner:
    """Orchestrates Halmos SMT symbolic execution and parses formal proof results."""

    @classmethod
    def get_available_solver(cls, requested: Optional[str] = None) -> str:
        """Determines best available SMT solver on system."""
        if requested and requested in ["z3", "yices", "cvc5", "bitwuzla"]:
            return requested

        # Prefer yices for fast bitvector inequality solving, fallback to z3
        if shutil.which("yices"):
            return "yices"
        if shutil.which("z3"):
            return "z3"
        return "z3"

    @classmethod
    def run_symbolic_proof(
        cls,
        workspace_dir: str,
        contract_name: str,
        solver: Optional[str] = None,
        timeout: int = 120,
    ) -> SymbolicProofResult:
        """
        Executes Halmos symbolic verification for a target contract.
        Proves assertions for ∀ inputs using Z3 or Yices SMT.
        """
        solver_to_use = cls.get_available_solver(solver)

        halmos_bin = shutil.which("halmos")
        if not halmos_bin:
            return SymbolicProofResult(
                success=False,
                contract_name=contract_name,
                solver_used=solver_to_use,
                raw_output="Error: Halmos not found in PATH. Install via pip install halmos.",
            )

        cmd = [
            halmos_bin,
            "--contract", f"Symbolic{contract_name}Proof",
            "--solver", solver_to_use,
        ]

        try:
            process = subprocess.run(
                cmd,
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            raw_output = process.stdout + "\n" + process.stderr
            return cls._parse_output(raw_output, contract_name, solver_to_use)
        except subprocess.TimeoutExpired:
            return SymbolicProofResult(
                success=False,
                contract_name=contract_name,
                solver_used=solver_to_use,
                total_timeout=1,
                raw_output=f"Symbolic verification timed out after {timeout}s",
            )
        except Exception as e:
            return SymbolicProofResult(
                success=False,
                contract_name=contract_name,
                solver_used=solver_to_use,
                raw_output=f"Execution error: {str(e)}",
            )

    @classmethod
    def _parse_output(cls, output: str, contract_name: str, solver: str) -> SymbolicProofResult:
        # Strip ANSI escape color sequences
        ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        clean_text = ansi_regex.sub("", output)

        checks: List[SymbolicCheckResult] = []
        counterexample_vars: Dict[str, str] = {}

        # 1. Parse Counterexample variables if present
        ce_pattern = re.compile(r"^\s*(p_\w+)\s*=\s*(0x[0-9a-fA-F]+|\d+)", re.MULTILINE)
        for match in ce_pattern.finditer(clean_text):
            var_name = match.group(1)
            var_val = match.group(2)
            counterexample_vars[var_name] = var_val

        # 2. Parse individual check outcomes
        check_pattern = re.compile(
            r"\[(PASS|FAIL|TIMEOUT)\]\s+([\w_]+)\((.*?)\)\s+\(paths:\s*(\d+),\s*time:\s*([\d\.]+)s",
            re.MULTILINE
        )

        for match in check_pattern.finditer(clean_text):
            status = match.group(1)
            func_name = match.group(2)
            paths = int(match.group(4))
            time_sec = float(match.group(5))

            model = counterexample_vars if status == "FAIL" else {}
            checks.append(SymbolicCheckResult(
                function_name=func_name,
                status=status,
                paths_explored=paths,
                time_seconds=time_sec,
                counterexample_model=model,
            ))

        # 3. Parse summary
        passed_count = sum(1 for c in checks if c.status == "PASS")
        failed_count = sum(1 for c in checks if c.status == "FAIL")
        timeout_count = sum(1 for c in checks if c.status == "TIMEOUT")

        total_time = 0.0
        time_match = re.search(r"Symbolic test result:.*?time:\s*([\d\.]+)s", clean_text)
        if time_match:
            total_time = float(time_match.group(1))
        elif checks:
            total_time = sum(c.time_seconds for c in checks)

        success = (failed_count == 0 and timeout_count == 0 and passed_count > 0)


        return SymbolicProofResult(
            success=success,
            contract_name=contract_name,
            solver_used=solver,
            total_passed=passed_count,
            total_failed=failed_count,
            total_timeout=timeout_count,
            total_time_seconds=total_time,
            checks=checks,
            raw_output=output,
        )
