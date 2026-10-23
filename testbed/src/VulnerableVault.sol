// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title VulnerableVault
 * @notice Simplified ERC4626 Vault vulnerable to the classic First-Depositor Share Inflation Attack
 * and Rounding Truncation Exploitation.
 */
contract VulnerableVault {
    string public name = "Vulnerable Yield Vault";
    string public symbol = "vVAULT";
    
    uint256 public totalAssets;
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => uint256) public assetBalanceOf;

    event Deposit(address indexed sender, uint256 assets, uint256 shares);
    event Withdraw(address indexed sender, uint256 assets, uint256 shares);
    event Donation(address indexed sender, uint256 assets);

    function convertToShares(uint256 assets) public view returns (uint256) {
        if (totalSupply == 0) {
            return assets;
        }
        return (assets * totalSupply) / totalAssets;
    }

    function convertToAssets(uint256 shares) public view returns (uint256) {
        if (totalSupply == 0) {
            return shares;
        }
        return (shares * totalAssets) / totalSupply;
    }

    function deposit(uint256 assets) external returns (uint256 shares) {
        require(assets > 0, "INVALID_ZERO_ASSETS");
        
        shares = convertToShares(assets);
        // CRITICAL BUG: No check that shares > 0!
        // When share price is inflated, victim deposits assets but receives 0 shares!
        
        totalAssets += assets;
        totalSupply += shares;
        balanceOf[msg.sender] += shares;
        assetBalanceOf[msg.sender] += assets;

        emit Deposit(msg.sender, assets, shares);
    }

    function withdraw(uint256 shares) external returns (uint256 assets) {
        require(shares > 0, "INVALID_ZERO_SHARES");
        require(balanceOf[msg.sender] >= shares, "INSUFFICIENT_SHARES");

        assets = convertToAssets(shares);
        
        balanceOf[msg.sender] -= shares;
        totalSupply -= shares;
        totalAssets -= assets;

        emit Withdraw(msg.sender, assets, shares);
    }

    // Direct donation to vault to inflate exchange rate
    function donate(uint256 assets) external {
        require(assets > 0, "INVALID_ZERO_DONATION");
        totalAssets += assets;
        emit Donation(msg.sender, assets);
    }
}
