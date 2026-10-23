"""
Solidity Contract Parser & Interface Extractor for InvariantForge.
Extracts state variables, functions, types, and identifies protocol patterns.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class FunctionParam:
    type_name: str
    name: str


@dataclass
class ContractFunction:
    name: str
    params: List[FunctionParam]
    visibility: str  # public, external, internal, private
    is_view: bool
    is_pure: bool
    is_payable: bool
    return_types: List[str] = field(default_factory=list)


@dataclass
class StateVariable:
    type_name: str
    name: str
    visibility: str  # public, internal, private


@dataclass
class ParsedContract:
    contract_name: str
    pragma: str
    state_variables: List[StateVariable]
    functions: List[ContractFunction]
    detected_patterns: List[str]  # "VAULT_ERC4626", "LENDING", "STAKING", "REWARD"
    raw_source: str


class SolidityParser:
    """Parses Solidity source files to extract semantic structure for invariant synthesis."""

    VAULT_KEYWORDS = {"deposit", "withdraw", "totalassets", "totalsupply", "converttoshares", "converttoassets"}
    LENDING_KEYWORDS = {"borrow", "repay", "liquidate", "collateral", "debt", "ltv"}
    DONATION_KEYWORDS = {"donate", "skim", "sync"}

    @classmethod
    def parse_file(cls, file_path: str) -> ParsedContract:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        return cls.parse_source(source)

    @classmethod
    def parse_source(cls, source: str) -> ParsedContract:
        # Strip comments
        clean_source = re.sub(r"//.*", "", source)
        clean_source = re.sub(r"/\*[\s\S]*?\*/", "", clean_source)

        # Extract pragma
        pragma_match = re.search(r"pragma\s+solidity\s+([^;]+);", source)
        pragma = pragma_match.group(1).strip() if pragma_match else "^0.8.20"

        # Extract contract name
        contract_match = re.search(r"contract\s+(\w+)", clean_source)
        contract_name = contract_match.group(1).strip() if contract_match else "TargetContract"

        # Extract state variables
        state_vars = cls._extract_state_variables(clean_source)

        # Extract functions
        functions = cls._extract_functions(clean_source)

        # Detect protocol patterns
        patterns = cls._detect_patterns(functions, state_vars)

        return ParsedContract(
            contract_name=contract_name,
            pragma=pragma,
            state_variables=state_vars,
            functions=functions,
            detected_patterns=patterns,
            raw_source=source,
        )

    @classmethod
    def _extract_state_variables(cls, source: str) -> List[StateVariable]:
        vars_list = []
        # Pattern for basic state vars: type (public|private|internal)? name (= value)?;
        var_pattern = re.compile(
            r"^\s*(uint256|uint128|uint64|uint8|int256|address|bool|string|bytes32|mapping\([^\)]+\))\s+"
            r"(public|internal|private)?\s*([a-zA-Z0-9_]+)\s*(?:=.*?)?;",
            re.MULTILINE,
        )
        for match in var_pattern.finditer(source):
            type_name = match.group(1).strip()
            visibility = match.group(2).strip() if match.group(2) else "internal"
            name = match.group(3).strip()
            vars_list.append(StateVariable(type_name=type_name, name=name, visibility=visibility))
        return vars_list

    @classmethod
    def _extract_functions(cls, source: str) -> List[ContractFunction]:
        functions = []
        func_pattern = re.compile(
            r"function\s+([a-zA-Z0-9_]+)\s*\((.*?)\)\s*"
            r"(external|public|internal|private)?\s*"
            r"(view|pure)?\s*"
            r"(payable)?\s*"
            r"(?:returns\s*\((.*?)\))?\s*\{",
            re.DOTALL,
        )

        for match in func_pattern.finditer(source):
            name = match.group(1).strip()
            params_raw = match.group(2).strip()
            visibility = match.group(3).strip() if match.group(3) else "public"
            view_or_pure = match.group(4).strip() if match.group(4) else ""
            payable = bool(match.group(5))
            returns_raw = match.group(6).strip() if match.group(6) else ""

            # Skip constructor, fallback, receive
            if name in {"constructor", "fallback", "receive"}:
                continue

            # Parse parameters
            params = []
            if params_raw:
                for p in params_raw.split(","):
                    p = p.strip()
                    if not p:
                        continue
                    tokens = p.split()
                    if len(tokens) >= 2:
                        type_name = tokens[0]
                        # Handle memory, calldata, storage modifiers
                        param_name = tokens[-1]
                        params.append(FunctionParam(type_name=type_name, name=param_name))

            returns = [r.strip().split()[0] for r in returns_raw.split(",") if r.strip()]

            functions.append(
                ContractFunction(
                    name=name,
                    params=params,
                    visibility=visibility,
                    is_view=(view_or_pure == "view"),
                    is_pure=(view_or_pure == "pure"),
                    is_payable=payable,
                    return_types=returns,
                )
            )

        return functions

    @classmethod
    def _detect_patterns(cls, functions: List[ContractFunction], state_vars: List[StateVariable]) -> List[str]:
        func_names = {f.name.lower() for f in functions}
        var_names = {v.name.lower() for v in state_vars}
        all_identifiers = func_names.union(var_names)

        patterns = []
        if len(all_identifiers.intersection(cls.VAULT_KEYWORDS)) >= 2:
            patterns.append("VAULT_ERC4626")
        if len(all_identifiers.intersection(cls.LENDING_KEYWORDS)) >= 2:
            patterns.append("LENDING_MARKET")
        if any(kw in all_identifiers for kw in cls.DONATION_KEYWORDS):
            patterns.append("DONATION_SUSCEPTIBLE")

        return patterns
