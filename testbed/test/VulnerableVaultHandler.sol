// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";
import {CommonBase} from "forge-std/Base.sol";
import {StdCheats} from "forge-std/StdCheats.sol";
import {StdUtils} from "forge-std/StdUtils.sol";
import "../src/VulnerableVault.sol";

contract VulnerableVaultHandler is CommonBase, StdCheats, StdUtils, Test {
    VulnerableVault public target;

    // Ghost Variables for Invariant Assertions
    uint256 public ghost_zeroSharesOnNonZeroDepositCount;
    uint256 public ghost_totalWithdrawnAssets;
    uint256 public ghost_totalDepositedAssets;

    // Actors Array for Multi-User Fuzzing
    address[] public actors;
    address internal currentActor;

    constructor(VulnerableVault _target) {
        target = _target;
        actors.push(address(0xAAAA));
        actors.push(address(0xBBBB));
        actors.push(address(0xCCCC));
        actors.push(address(0xDDDD));
    }

    modifier useActor(uint256 actorIndexSeed) {
        currentActor = actors[bound(actorIndexSeed, 0, actors.length - 1)];
        vm.startPrank(currentActor);
        _;
        vm.stopPrank();
    }

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

    function donate(uint256 assetsSeed, uint256 actorSeed) public useActor(actorSeed) {
        // Direct donation without minting shares
        uint256 assets = bound(assetsSeed, 1, 100_000 ether);

        try target.donate(assets) {
            // Donation succeeds
        } catch {
            // Absorb
        }
    }

}
