"""
Tests for InvariantForge Symbolic SMT Verification Runner.
"""

import os
from invariant_forge.symbolic_runner import SymbolicRunner


def test_symbolic_solver_detection():
    solver = SymbolicRunner.get_available_solver()
    assert solver in ["yices", "z3"]


def test_symbolic_runner_parse_pass_output():
    sample_output = """
Running 3 tests for test/SymbolicVaultProof.t.sol:SymbolicVaultProof
[PASS] check_shares_monotonic_scaling(uint64) (paths: 7, time: 0.12s, bounds: [])
[PASS] check_shares_never_zero_for_positive_assets(uint128) (paths: 4, time: 0.05s, bounds: [])
[PASS] check_zero_assets_zero_shares() (paths: 1, time: 0.01s, bounds: [])
Symbolic test result: 3 passed; 0 failed; time: 0.20s
"""
    result = SymbolicRunner._parse_output(sample_output, "Vault", "yices")
    assert result.success is True
    assert result.total_passed == 3
    assert result.total_failed == 0
    assert len(result.checks) == 3
    assert result.checks[0].function_name == "check_shares_monotonic_scaling"
    assert result.checks[0].status == "PASS"
    assert result.checks[1].function_name == "check_shares_never_zero_for_positive_assets"
    assert result.checks[2].function_name == "check_zero_assets_zero_shares"


def test_symbolic_runner_parse_fail_output():
    sample_output = """
Running 1 tests for test/SymbolicVulnerableVaultProof.t.sol:SymbolicVulnerableVaultProof
Counterexample: 
    p_assets_uint64_5f7e3a7_00 = 0x4000000000000000
    p_donation_uint64_d0ad986_00 = 0x8000000000000000
[FAIL] check_positive_deposit_always_mints_shares(uint64,uint64) (paths: 7, time: 0.75s, bounds: [])
Symbolic test result: 0 passed; 1 failed; time: 0.77s
"""
    result = SymbolicRunner._parse_output(sample_output, "VulnerableVault", "yices")
    assert result.success is False
    assert result.total_passed == 0
    assert result.total_failed == 1
    assert len(result.checks) == 1
    assert result.checks[0].status == "FAIL"
    assert "p_assets_uint64_5f7e3a7_00" in result.checks[0].counterexample_model
    assert result.checks[0].counterexample_model["p_assets_uint64_5f7e3a7_00"] == "0x4000000000000000"


def test_live_symbolic_proof_execution():
    workspace_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "testbed")
    result = SymbolicRunner.run_symbolic_proof(workspace_dir, "Vault", solver="yices", timeout=30)
    assert result.success is True
    assert result.total_passed >= 3
    assert result.total_failed == 0
