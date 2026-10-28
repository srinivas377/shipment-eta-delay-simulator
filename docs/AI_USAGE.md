# AI Usage & Governance Disclosure

In compliance with the YottaFlex AI project submission requirements, this document outlines the extent, methodologies, and human engineering oversight applied in utilizing AI coding tools (Claude Code / Google Antigravity).

---

### 1. Where AI Accelerated the Work
- **Boilerplate Scaffolding**: Rapid construction of relational schema mappings, dataclass definitions, and zero-padded ID regex patterns across 19 relational entities.
- **Test Generation**: Automated drafting of parameterized test suites covering edge cases, regex validators, and foreign key traversals.
- **SQL DDL & SQLite Loader Construction**: Generation of strict foreign-key enforced DDL statements matching the JSON schema definitions.
- **Streamlit Layout**: Prototyping multi-tab dashboard component wrappers and glassmorphism CSS stylings.

### 2. Critical Areas Requiring Heavy Personal Oversight & Refinement
- **RNG Decoupling & SeedSequence Hierarchy**: Ensuring that NumPy's `np.random.SeedSequence.spawn` created truly independent generators for each domain, preventing random trajectory shifts across entities when modifying parameters.
- **Event Calibration Infinite-Loop Fix**: Personally diagnosing and fixing a subtle edge-case in event pruning where `while excess > 0` looped endlessly when only non-prunable scans remained. Refactored into a single-pass $O(N)$ candidate filter.
- **NumPy 2.x `rng.choice` List-of-Dicts Coercion**: Fixing a performance hang caused by `np.random.default_rng().choice` coercing lists of dictionaries into structured ndarrays. Refactored into direct integer indexing.
- **Compact Minute UTC ID Collision Prevention**: Discovering that formatting timestamps to minute resolution (`YYYYMMDDTHHMM`) caused duplicate primary keys when multiple scans occurred in the same minute. Added minute-level deduplication to guarantee 100% primary key uniqueness.
- **Strict Leakage Boundary**: Ensuring that `features_cutoff_time` and all candidate feature events were strictly gated by `ingestion_time <= prediction_time` rather than `event_time`.

### 3. Verification & Governance Evidence
- Every single line of code was executed, tested with `pytest`, and verified against real command outputs.
- 100% bit-for-bit reproducibility verified across independent generation runs (`scripts/repro_check.py`).
- Complete prompt history preserved in `prompt_history/`.
