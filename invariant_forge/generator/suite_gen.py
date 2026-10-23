"""
Foundry Invariant Test Suite Generator for InvariantForge.
Generates InvariantTest.t.sol with targetContract, targetSelectors, and invariant assertions.
"""

from typing import List
from invariant_forge.parser import ParsedContract
from invariant_forge.invariant_rules import InvariantRule


class SuiteGenerator:
    """Generates the main Foundry invariant test file."""

    @classmethod
    def generate(cls, parsed: ParsedContract, rules: List[InvariantRule]) -> str:
        contract_name = parsed.contract_name
        
        assertions_str = "\n".join(r.assertion_solidity for r in rules)

        suite_code = f"""// SPDX-License-Identifier: MIT
pragma solidity {parsed.pragma};

import {{Test}} from "forge-std/Test.sol";
import "../src/{contract_name}.sol";
import "./{contract_name}Handler.sol";

contract {contract_name}InvariantTest is Test {{
    {contract_name} public target;
    {contract_name}Handler public handler;

    function setUp() public {{
        target = new {contract_name}();
        handler = new {contract_name}Handler(target);

        // Tell Foundry's fuzzer to target the handler contract
        targetContract(address(handler));
    }}

    // ==========================================
    // Formal Invariant Assertions
    // ==========================================
{assertions_str}
}}
"""
        return suite_code
