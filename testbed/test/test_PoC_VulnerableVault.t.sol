// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/* Authorized Protocol Quality Assurance & Formal Verification Test Suite */
import {Test} from "forge-std/Test.sol";
import "../src/VulnerableVault.sol";
import "./VulnerableVaultHandler.sol";

/**
 * @title PoC_VulnerableVault_InvariantViolation
 * @notice Standalone Proof of Concept reproducing invariant violation: InvariantViolation
 * Generated autonomously by InvariantForge.
 */
contract PoC_VulnerableVault_InvariantViolation is Test {
    VulnerableVault public target;
    VulnerableVaultHandler public handler;

    function setUp() public {
        target = new VulnerableVault();
        handler = new VulnerableVaultHandler(target);
    }

    function test_PoC_reproduce_invariant_violation() public {
        // ----------------------------------------------------
        // Counterexample Action Sequence Extracted from Fuzzer
        // ----------------------------------------------------
        // Step 1: handler.deposit(48059, 0);
        handler.deposit(48059, 0);
        // Step 2: handler.donate(20395106071830844192481026447245219490697258481504146069601850614441964881, 523820077384027719611196185493199);
        handler.donate(20395106071830844192481026447245219490697258481504146069601850614441964881, 523820077384027719611196185493199);
        // Step 3: handler.deposit(1899, 9256);
        handler.deposit(1899, 9256);
        
        // Invariant assertion proving the vulnerability was triggered
        assertGt(
            handler.ghost_zeroSharesOnNonZeroDepositCount(),
            0,
            "CONFIRMED_VULNERABILITY: Non-zero assets deposited resulted in zero shares minted!"
        );
    }
}
