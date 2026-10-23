"""
Ramanujan Mathematical Invariant Catalog for InvariantForge.
Defines formal properties, ghost variable tracking requirements, and assertions.
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class InvariantRule:
    rule_id: str
    name: str
    category: str  # "VAULT", "SOLVENCY", "ROUNDING", "CONSERVATION"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM"
    description: str
    ghost_variables: List[str]
    assertion_solidity: str
    failure_explanation: str


class InvariantCatalog:
    """Library of formal state invariants for DeFi protocols."""

    RULES: Dict[str, InvariantRule] = {
        "INV_VAULT_001_NO_ZERO_SHARES": InvariantRule(
            rule_id="INV_VAULT_001",
            name="NonZeroDepositMustYieldShares",
            category="ROUNDING",
            severity="CRITICAL",
            description="A user who deposits non-zero assets must never receive zero shares (Inflation/Truncation Attack).",
            ghost_variables=[
                "uint256 public ghost_zeroSharesOnNonZeroDepositCount;"
            ],
            assertion_solidity="""
    function invariant_no_zero_shares_minted_for_deposit() public view {
        assertEq(
            handler.ghost_zeroSharesOnNonZeroDepositCount(),
            0,
            "CRITICAL_VULNERABILITY: Non-zero assets deposited resulted in zero shares minted! Inflation/Dilution bug confirmed."
        );
    }
""",
            failure_explanation="Attacker artificially inflated share price via donation/direct transfer, causing subsequent victim deposit to round down to 0 shares.",
        ),
        "INV_VAULT_002_ASSET_CONSERVATION": InvariantRule(
            rule_id="INV_VAULT_002",
            name="VaultAssetConservation",
            category="CONSERVATION",
            severity="HIGH",
            description="The vault must retain at least the sum of net user deposits.",
            ghost_variables=[
                "uint256 public ghost_totalDepositedAssets;",
                "uint256 public ghost_totalWithdrawnAssets;"
            ],
            assertion_solidity="""
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
""",
            failure_explanation="Protocol state allows more assets to be extracted than were deposited, leading to under-collateralization or insolvency.",
        ),
        "INV_VAULT_003_SHARE_PRICE_SOLVENCY": InvariantRule(
            rule_id="INV_VAULT_003",
            name="SharePriceBackingSolvency",
            category="SOLVENCY",
            severity="CRITICAL",
            description="If total supply > 0, total assets must be > 0.",
            ghost_variables=[],
            assertion_solidity="""
    function invariant_total_supply_backed_by_assets() public view {
        if (target.totalSupply() > 0) {
            assertGt(
                target.totalAssets(),
                0,
                "CRITICAL_VULNERABILITY: Shares exist with 0 total assets! Vault completely drained while liabilities remain."
            );
        }
    }
""",
            failure_explanation="Shares remain outstanding in circulation but underlying assets were drained to zero.",
        ),
    }

    @classmethod
    def get_applicable_rules(cls, detected_patterns: List[str]) -> List[InvariantRule]:
        applicable = []
        if "VAULT_ERC4626" in detected_patterns or "DONATION_SUSCEPTIBLE" in detected_patterns:
            applicable.extend([
                cls.RULES["INV_VAULT_001_NO_ZERO_SHARES"],
                cls.RULES["INV_VAULT_002_ASSET_CONSERVATION"],
                cls.RULES["INV_VAULT_003_SHARE_PRICE_SOLVENCY"],
            ])
        # Default safety net
        if not applicable:
            applicable.append(cls.RULES["INV_VAULT_001_NO_ZERO_SHARES"])
        return applicable
