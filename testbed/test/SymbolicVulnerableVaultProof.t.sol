// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {VulnerableVault} from "../src/VulnerableVault.sol";

/**
 * @title SymbolicVulnerableVaultProof
 * @notice Formal verification of VulnerableVault with Halmos & Z3/Yices SMT solvers.
 * Demonstrates mathematical counterexample generation when the vault lacks virtual share offsets.
 */
contract SymbolicVulnerableVaultProof is VulnerableVault {
    /// @notice Security invariant: For any positive deposit, the depositor must receive > 0 shares.
    /// In VulnerableVault, when totalAssets is inflated relative to totalSupply,
    /// integer division truncates to zero: shares = (assets * totalSupply) / totalAssets = 0.
    /// Halmos will find a SAT counterexample violating this assertion!
    function check_positive_deposit_always_mints_shares(uint64 assets, uint64 donation) public {
        if (assets == 0 || donation < 1000) return;

        // Simulate post-donation inflated state
        totalAssets = uint256(donation);
        totalSupply = 1;

        uint256 shares = convertToShares(assets);
        assert(shares > 0);
    }
}
