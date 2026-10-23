"""
Foundry Handler Contract Generator for InvariantForge.
Generates bounded, stateful handler contracts targeting the contract under test.
"""

from typing import List
from invariant_forge.parser import ParsedContract
from invariant_forge.invariant_rules import InvariantRule


class HandlerGenerator:
    """Generates Handler.sol to bound fuzz inputs and maintain ghost variables."""

    @classmethod
    def generate(cls, parsed: ParsedContract, rules: List[InvariantRule]) -> str:
        contract_name = parsed.contract_name
        
        # Collect ghost variables
        ghost_vars = []
        for r in rules:
            ghost_vars.extend(r.ghost_variables)
        ghost_vars_str = "\n    ".join(set(ghost_vars))

        # Check which functions exist
        has_deposit = any(f.name == "deposit" for f in parsed.functions)
        has_withdraw = any(f.name == "withdraw" for f in parsed.functions)
        has_donate = any(f.name == "donate" for f in parsed.functions)

        handler_code = f"""// SPDX-License-Identifier: MIT
pragma solidity {parsed.pragma};

import {{Test}} from "forge-std/Test.sol";
import {{CommonBase}} from "forge-std/Base.sol";
import {{StdCheats}} from "forge-std/StdCheats.sol";
import {{StdUtils}} from "forge-std/StdUtils.sol";
import "../src/{contract_name}.sol";

contract {contract_name}Handler is CommonBase, StdCheats, StdUtils, Test {{
    {contract_name} public target;

    // Ghost Variables for Invariant Assertions
    {ghost_vars_str}

    // Actors Array for Multi-User Fuzzing
    address[] public actors;
    address internal currentActor;

    constructor({contract_name} _target) {{
        target = _target;
        actors.push(address(0xAAAA));
        actors.push(address(0xBBBB));
        actors.push(address(0xCCCC));
        actors.push(address(0xDDDD));
    }}

    modifier useActor(uint256 actorIndexSeed) {{
        currentActor = actors[bound(actorIndexSeed, 0, actors.length - 1)];
        vm.startPrank(currentActor);
        _;
        vm.stopPrank();
    }}
"""

        if has_deposit:
            handler_code += """
    function deposit(uint256 assetsSeed, uint256 actorSeed) public useActor(actorSeed) {
        // Bound deposit amount realistically (from 1 wei to 1,000,000 ether)
        uint256 assets = bound(assetsSeed, 1, 1_000_000 ether);

        try target.deposit(assets) returns (uint256 shares) {
            ghost_totalDepositedAssets += assets;
            
            // Check for zero-shares dilution violation
            if (shares == 0 && assets > 0) {
                ghost_zeroSharesOnNonZeroDepositCount++;
            }
        } catch {
            // Expected reverts (e.g. invalid conditions) are safely absorbed
        }
    }
"""

        if has_withdraw:
            handler_code += """
    function withdraw(uint256 sharesSeed, uint256 actorSeed) public useActor(actorSeed) {
        uint256 userShares = target.balanceOf(currentActor);
        if (userShares == 0) return;

        uint256 shares = bound(sharesSeed, 1, userShares);

        try target.withdraw(shares) returns (uint256 assets) {
            ghost_totalWithdrawnAssets += assets;
        } catch {
            // Absorb revert
        }
    }
"""

        if has_donate:
            handler_code += """
    function donate(uint256 assetsSeed, uint256 actorSeed) public useActor(actorSeed) {
        // Direct donation without minting shares
        uint256 assets = bound(assetsSeed, 1, 100_000 ether);

        try target.donate(assets) {
            // Donation succeeds
        } catch {
            // Absorb
        }
    }
"""

        handler_code += "\n}\n"
        return handler_code
