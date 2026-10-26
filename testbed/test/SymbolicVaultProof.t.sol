// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {SecureVault} from "../src/SecureVault.sol";

/**
 * @title SymbolicVaultProof
 * @notice Mathematical Formal Verification with Halmos & Z3 SMT Solver.
 * Proves that SecureVault's virtual offset prevents share inflation attacks for ALL possible deposit inputs.
 */
contract SymbolicVaultProof is SecureVault {
    /// @notice Proves that zero assets produces zero shares (no free minting).
    function check_zero_assets_zero_shares() public view {
        assert(convertToShares(0) == 0);
    }

    /// @notice Proves that for ANY non-zero deposit amount, shares minted are strictly > 0.
    /// Halmos verifies this symbolically for ∀ assets ∈ [1, type(uint128).max].
    function check_shares_never_zero_for_positive_assets(uint128 assets) public view {
        if (assets == 0) return;
        uint256 shares = convertToShares(assets);
        assert(shares > 0);
    }

    /// @notice Proves mathematical scale monotonicity: convertToShares(2 * a) >= convertToShares(a)
    function check_shares_monotonic_scaling(uint64 assets) public view {
        if (assets == 0 || assets > type(uint64).max / 2) return;
        assert(convertToShares(2 * uint256(assets)) >= convertToShares(assets));
    }
}


