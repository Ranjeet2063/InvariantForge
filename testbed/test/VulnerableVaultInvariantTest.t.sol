// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import "../src/VulnerableVault.sol";
import "./VulnerableVaultHandler.sol";

contract VulnerableVaultInvariantTest is Test {
    VulnerableVault public target;
    VulnerableVaultHandler public handler;

    function setUp() public {
        target = new VulnerableVault();
        handler = new VulnerableVaultHandler(target);

        // Tell Foundry's fuzzer to target the handler contract
        targetContract(address(handler));
    }

    // ==========================================
    // Formal Invariant Assertions
    // ==========================================

    function invariant_no_zero_shares_minted_for_deposit() public view {
        assertEq(
            handler.ghost_zeroSharesOnNonZeroDepositCount(),
            0,
            "CRITICAL_VULNERABILITY: Non-zero assets deposited resulted in zero shares minted! Inflation/Dilution bug confirmed."
        );
    }


    function invariant_vault_asset_conservation() public view {
        if (handler.ghost_totalDepositedAssets() >= handler.ghost_totalWithdrawnAssets()) {
            uint256 expectedMinAssets = handler.ghost_totalDepositedAssets() - handler.ghost_totalWithdrawnAssets();
            assertGe(
                target.totalAssets(),
                expectedMinAssets,
                "HIGH_VULNERABILITY: Vault totalAssets is less than net deposited assets! Protocol insolvency."
            );
        }
    }


    function invariant_total_supply_backed_by_assets() public view {
        if (target.totalSupply() > 0) {
            assertGt(
                target.totalAssets(),
                0,
                "CRITICAL_VULNERABILITY: Shares exist with 0 total assets! Vault completely drained while liabilities remain."
            );
        }
    }

}
