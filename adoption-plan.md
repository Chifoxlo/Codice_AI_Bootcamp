# Agent Adoption Plan: SAP Customer Master Data Migration Team

## 1. Routing Card
*   **Complex Tasks (e.g., Complex data deduplication logic, ABAP/Data Services script architecture review, IDoc structural validation):** Pinned to a frontier model (Anthropic Claude Opus 4.8 or OpenAI GPT-5.6 Sol) to ensure maximum reasoning on critical data mapping rules.
*   **Routine/Repetitive Tasks (e.g., Basic field mapping format validation, translating legacy field names, doc-syncing):** Pinned to Microsoft MAI-Code-1-Flash to save AI Credits and minimize latency.
*   **Auto-select:** Used for standard mapping script triaging and PR summarization. Allowing the Copilot orchestrator to auto-select provides a 10% discount on credit billing while handling standard tasks efficiently.

## 2. Deny Rules
*   `agent execute sql --command "DELETE FROM..."` or `DROP`: **Blocked.** A `PreToolUse` hook matching "DELETE/DROP" triggers `block_destructive.py` (exit 2) to prevent the agent from destroying data in the staging databases.
*   `agent execute api --endpoint "SAP_PRD_*"`: **Blocked.** The agent is forbidden from executing direct writes or API calls to the SAP Production (PRD) environment. Production loads must remain human-gated.

## 3. Reviewer Spec
*   **Objective:** Review SAP Customer Master Data mapping pull requests (CSV/JSON/SQL) to ensure all mandatory S/4HANA fields (e.g., `NAME1`, `SORTL`, `LAND1`) are correctly mapped and follow Bosch data governance standards.
*   **Output Contract:** The agent must output a strict JSON array of objects containing `severity`, `rule`, `row_or_line`, and `msg`. 
*   **Escape Hatch:** If the PR diff is empty or does not contain mapping files, return `[]`.

## 4. Output Contract
To ensure the output is CI-consumable (so downstream GitHub Actions can deterministically block or pass the PR before we attempt a mock load into SAP), the reviewer agent must emit its findings strictly in this JSON schema:

```json
[
  {
    "severity": "high", 
    "rule": "SAP-CMD-01-MissingMandatory",
    "row_or_line": 154,
    "msg": "Mandatory field 'LAND1' (Country Key) is unmapped for customer record."
  }
]
