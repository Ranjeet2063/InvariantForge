"""
Foundry Test Runner & Trace Parser for InvariantForge.
Executes forge test with deep verbosity and parses counterexample call traces.
"""

import subprocess
import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class CallTraceStep:
    contract_or_handler: str
    function_name: str
    args: str
    calldata: Optional[str] = None


@dataclass
class FuzzResult:
    success: bool
    runs: int
    failed_invariant: Optional[str] = None
    revert_reason: Optional[str] = None
    counterexample_calls: List[CallTraceStep] = field(default_factory=list)
    raw_output: str = ""


class FoundryRunner:
    """Runs forge test and extracts structured failure telemetry."""

    @classmethod
    def run_invariant_test(cls, workspace_dir: str, contract_name: str, fuzz_runs: int = 1000) -> FuzzResult:
        cmd = [
            "forge", "test",
            "--match-contract", f"{contract_name}InvariantTest",
            "-vvv"
        ]

        env = os.environ.copy()
        env["FOUNDRY_FUZZ_RUNS"] = str(fuzz_runs)

        try:
            process = subprocess.run(
                cmd,
                cwd=workspace_dir,
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )
            raw_output = process.stdout + "\n" + process.stderr
            return cls._parse_output(raw_output, process.returncode)
        except subprocess.TimeoutExpired:
            return FuzzResult(success=False, runs=0, revert_reason="FUZZ_TIMEOUT", raw_output="Fuzzing timed out after 120s")
        except Exception as e:
            return FuzzResult(success=False, runs=0, revert_reason=str(e), raw_output=str(e))

    @classmethod
    def _parse_output(cls, output: str, returncode: int) -> FuzzResult:
        # Check if passed
        passed = (returncode == 0) and ("FAILED" not in output) and ("[PASS]" in output)

        # Extract number of runs
        runs = 0
        runs_match = re.search(r"runs:\s*(\d+)", output)
        if runs_match:
            runs = int(runs_match.group(1))

        if passed:
            return FuzzResult(success=True, runs=runs, raw_output=output)

        # Failure parsing
        failed_invariant = None
        inv_match = re.search(r"\[FAIL(?:\. Reason: (.*?))?\]\s*(invariant_\w+)\(\)", output)
        if inv_match:
            failed_invariant = inv_match.group(2)
        else:
            # Fallback
            inv_match2 = re.search(r"(invariant_\w+)\(\)\s*\(runs:\s*\d+,\s*calls:\s*\d+,\s*reverts:\s*\d+\)", output)
            if inv_match2:
                failed_invariant = inv_match2.group(1)

        # Extract revert reason
        revert_reason = None
        reason_match = re.search(r"Reason:\s*(.*)", output)
        if reason_match:
            revert_reason = reason_match.group(1).strip()

        # Extract counterexample calls from trace
        calls = cls._extract_counterexample_calls(output)

        return FuzzResult(
            success=False,
            runs=runs,
            failed_invariant=failed_invariant,
            revert_reason=revert_reason,
            counterexample_calls=calls,
            raw_output=output,
        )

    @classmethod
    def _extract_counterexample_calls(cls, output: str) -> List[CallTraceStep]:
        calls = []
        # Look for the Counterexample block
        # Example Foundry format:
        #   [Handler]::deposit(48059 [4.805e4], 0)
        #   [Handler]::donate(10000000000000000000000 [1.0e22], 1)
        #   [Handler]::deposit(19999000000000000000000, 2)
        call_pattern = re.compile(r"(\w+Handler)::(\w+)\((.*?)\)")
        for line in output.splitlines():
            match = call_pattern.search(line)
            if match:
                contract_name = match.group(1)
                func_name = match.group(2)
                raw_args = match.group(3)

                # Skip view/getter calls to ghost variables
                if func_name.startswith("ghost_"):
                    continue

                # Strip bracketed scientific notations e.g. "48059 [4.805e4]" -> "48059"
                clean_args = re.sub(r"\[.*?\]", "", raw_args).strip()
                # Clean up any trailing/double commas or spaces
                clean_args = re.sub(r"\s*,\s*", ", ", clean_args).strip()

                calls.append(CallTraceStep(contract_or_handler=contract_name, function_name=func_name, args=clean_args))

        return calls
