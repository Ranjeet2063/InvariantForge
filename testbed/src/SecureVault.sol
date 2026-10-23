// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title SecureVault
 * @notice Fixed ERC4626 Vault with virtual offset to prevent share inflation / zero-shares attacks.
 */
contract SecureVault {
    string public name = "Secure Yield Vault";
    string public symbol = "sVAULT";

    uint256 public totalAssets;
    uint256 public totalSupply;

    uint256 internal constant VIRTUAL_OFFSET = 1e3;

    mapping(address => uint256) public balanceOf;

    event Deposit(address indexed sender, uint256 assets, uint256 shares);
    event Withdraw(address indexed sender, uint256 assets, uint256 shares);

    function convertToShares(uint256 assets) public view returns (uint256) {
        return (assets * (totalSupply + VIRTUAL_OFFSET)) / (totalAssets + 1);
    }

    function convertToAssets(uint256 shares) public view returns (uint256) {
        return (shares * (totalAssets + 1)) / (totalSupply + VIRTUAL_OFFSET);
    }

    function deposit(uint256 assets) external returns (uint256 shares) {
        require(assets > 0, "INVALID_ZERO_ASSETS");
        
        shares = convertToShares(assets);
        require(shares > 0, "ZERO_SHARES_MINTED");

        totalAssets += assets;
        totalSupply += shares;
        balanceOf[msg.sender] += shares;

        emit Deposit(msg.sender, assets, shares);
    }

    function withdraw(uint256 shares) external returns (uint256 assets) {
        require(shares > 0, "INVALID_ZERO_SHARES");
        require(balanceOf[msg.sender] >= shares, "INSUFFICIENT_SHARES");

        assets = convertToAssets(shares);
        require(assets > 0, "ZERO_ASSETS_WITHDRAWN");

        balanceOf[msg.sender] -= shares;
        totalSupply -= shares;
        totalAssets -= assets;

        emit Withdraw(msg.sender, assets, shares);
    }
}
