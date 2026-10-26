"""
Tests for Solidity Parser in InvariantForge.
"""

from invariant_forge.parser import SolidityParser


def test_parse_vault_contract():
    sample_sol = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MockVault {
    mapping(address => uint256) public balanceOf;
    uint256 public totalSupply;
    uint256 public totalAssets;

    function deposit(uint256 assets) external returns (uint256 shares) {}
    function withdraw(uint256 shares) external returns (uint256 assets) {}
    function donate(uint256 amount) external {}
}
"""
    parsed = SolidityParser.parse_source(sample_sol)
    assert parsed.contract_name == "MockVault"
    assert parsed.pragma == "^0.8.20"
    assert "VAULT_ERC4626" in parsed.detected_patterns
    var_names = [v.name for v in parsed.state_variables]
    assert "balanceOf" in var_names
    func_names = [f.name for f in parsed.functions]
    assert "deposit" in func_names
    assert "withdraw" in func_names
