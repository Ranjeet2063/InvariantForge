# 🛡️ InvariantForge
**Autonomous Smart Contract Invariant Fuzzing & SMT Symbolic Prover**  
*Built with Ramanujan Mathematical Rigor, Halmos, Z3/Yices SMT Solvers, and Foundry*

[![CI](https://github.com/Ranjeet2063/InvariantForge/actions/workflows/ci.yml/badge.svg)](https://github.com/Ranjeet2063/InvariantForge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Foundry](https://img.shields.io/badge/Built%20with-Foundry-red.svg)](https://getfoundry.sh/)
[![Formal Verification](https://img.shields.io/badge/Prover-Halmos%20%2B%20Z3%2FYices-purple.svg)](https://github.com/a16z/halmos)

---

## ⚡ Overview
`InvariantForge` is an elite formal verification and autonomous fuzzing engine for Web3 smart contracts. Unlike generic LLM auditors that produce noisy, unverified markdown reports, `InvariantForge` provides **mathematical proof guarantees**:

1. **Dual Verification Architecture**:
   - **Stateful Invariant Fuzzing (`forge test`)**: Simulates millions of randomized multi-actor state transitions across bounded sequences to uncover race conditions, reentrancy, and insolvency.
   - **Symbolic SMT Formal Prover (`halmos` + `Z3`/`Yices`)**: Mathematically evaluates EVM bytecodes over the universal input domain ($\forall x \in [0, 2^{256}-1]$) to formally prove theorem invariants (UNSAT) or extract counterexample exploit models (SAT).
2. **Autonomous PoC Generation**:
   - When an invariant fails in fuzzing or symbolic execution, `InvariantForge` automatically synthesizes a standalone, deterministic `test_PoC_*.t.sol` reproducer that runs in $< 5\text{ms}$ with 100% green exit status for direct bounty submission to **Cantina / Immunefi**.
3. **Ramanujan Invariant Catalog**:
   - Out-of-the-box formal properties covering ERC-4626 Vault Dilution, Lending Solvency, AMM Constant Invariants, and Precision Loss.

---

## 🚀 Installation

### Prerequisites
- [Foundry](https://getfoundry.sh/) (`forge`, `cast`)
- Python 3.10+
- SMT Solvers: [Z3](https://github.com/Z3Prover/z3) and/or [Yices](https://yices.csl.sri.com/)

```bash
# Clone repository
git clone https://github.com/Ranjeet2063/InvariantForge.git
cd InvariantForge

# Install Python package and dependencies
pip install -e .

# Install Halmos Symbolic Prover
pip install halmos
```

---

## 💻 CLI Usage

### 1. View Ramanujan Mathematical Invariants
```bash
invariant-forge rules
```

### 2. Formally Prove Invariants via SMT Symbolic Execution
Formally proves properties for **all possible inputs** using Halmos with Z3 or Yices:
```bash
# Prove SecureVault with Yices/Z3
invariant-forge prove Vault --solver yices

# Run symbolic proof against VulnerableVault (extracts concrete exploit model)
invariant-forge prove VulnerableVault --solver yices
```

**Output Preview:**
```
╭──────────────────────────────────────────────────────────────────╮
│ 🔬 InvariantForge Formal Verifier — Halmos & SMT Symbolic Engine │
│ Ramanujan Mathematical Rigor & Universal Input Domain Guarantees │
╰──────────────────────────────────────────────────────────────────╯
✔ Target Contract: Vault
✔ SMT Solver Selected: YICES
⚡ Launching Halmos Symbolic Execution (∀ inputs in 2^256)...

                        Symbolic Proof Telemetry — Vault                        
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Symbolic Theorem / Invariant          ┃ Result ┃ Paths Explored ┃ Proof Time ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ check_shares_monotonic_scaling        │ PASS   │              7 │      0.06s │
│ check_shares_never_zero_for_positive… │ PASS   │              4 │      0.02s │
│ check_zero_assets_zero_shares         │ PASS   │              1 │      0.00s │
└───────────────────────────────────────┴────────┴────────────────┴────────────┘
╭───────────────────────── Formal Verification Passed ─────────────────────────╮
│ ✔ ALL THEOREMS MATHEMATICALLY PROVEN! (UNSAT)                                │
│ • Verified by SMT Solver: YICES                                              │
│ • Total Theorems Proven: 3                                                   │
│ • Proof Execution Time: 0.10s                                                │
│ • Mathematical Invariant: No state input exists in ∀ x ∈ [0, 2^256-1]        │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 3. Stateful Invariant Fuzzing Campaign
```bash
# Run 1,000 multi-actor fuzz sequences and auto-synthesize PoC on failure
invariant-forge scan testbed/src/VulnerableVault.sol --runs 1000
```

---

## 📊 Benchmark Suite

| Contract | Pattern Analyzed | Invariant Result | Formal SMT Result | Generated Proof Artifact |
| :--- | :--- | :---: | :---: | :--- |
| `VulnerableVault.sol` | First-Depositor Share Inflation | 🚨 **BREACHED** | 🚨 **SAT Counterexample** | `test_PoC_VulnerableVault.t.sol` (100% Green in 2ms) |
| `SecureVault.sol` | Solady Virtual Decimal Offset | ✔ **PASSED** | ✔ **PROVEN (UNSAT)** | Formal Certificate of Solvency |

---

## 🏗️ Repository Architecture

```
invariant-forge/
├── invariant_forge/             # Core Engine
│   ├── parser.py                # Solidity AST & Pattern Extractor
│   ├── invariant_rules.py       # Ramanujan Formal Invariant Catalog
│   ├── runner.py                # Foundry Stateful Test Runner
│   ├── symbolic_runner.py       # Halmos + Z3/Yices SMT Formal Prover
│   ├── generator/               # Code Synthesis Engines
│   │   ├── handler_gen.py       # Multi-Actor Bounded Handler Synthesizer
│   │   ├── suite_gen.py         # Foundry Invariant Suite Synthesizer
│   │   └── poc_gen.py           # Standalone PoC Reproducer Synthesizer
│   └── cli.py                   # Unified CLI Interface
├── testbed/                     # Foundry Testbed Environment
│   ├── src/                     # Verified Protocols (SecureVault, VulnerableVault)
│   ├── test/                    # Invariant & Symbolic Test Contracts
│   └── foundry.toml             # Foundry & Halmos AST Configurations
├── tests/                       # Python Unit & Verification Test Suite
└── .github/workflows/ci.yml     # Continuous Integration Pipeline
```

---

## 🔒 Security & Defensive Scope
`InvariantForge` is built strictly for **authorized white-hat security auditing, protocol defense, and formal verification**. All synthesized proofs and test cases verify invariant boundaries to harden smart contracts prior to mainnet deployment.

---

## 📜 License
MIT License. Built with mathematical precision by [Ranjeet2063](https://github.com/Ranjeet2063).
