# Project-Scoped Rules for CitizenBenefits Coding Agents

All agents working on this repository must strictly adhere to the following rules:

## 1. Non-PII & Privacy Constraints
* **NEVER** collect, store, or process any Personally Identifiable Information (PII) including names, Social Security Numbers (SSN), exact home addresses, Date of Birth (DOB), documents, or exact income amounts (use income bands instead).
* Implement active detection and refusal logic: if a user submits potential PII, refuse the request with a warning not to share sensitive information.
* Do not collect or process race under any circumstances.

## 2. Status Gating Constraint
* The citizenship/immigration status must be evaluated first.
* Only the following statuses are qualifying: `us_citizen`, `us_national`, `lawful_permanent_resident`, `cofa_citizen`, `veteran_or_military`.
* For any other status, return a factual ineligibility statement and immediately stop processing. Do not gather other factors or evaluate program eligibility.

## 3. Grounding & Accuracy Rules
* **NEVER** use eligibility rules, thresholds, or income limit numbers from the LLM's internal memory.
* Every threshold and rule must be retrieved at runtime using the grounding tools.
* If a grounding fetch fails, the program eligibility must be marked as `possibly` with an explicit notice to verify, rather than presenting a confident estimate.
* Every eligibility result must explicitly record the authoritative source in `source_cited`.

## 4. Response Framing & Disclaimer
* Use strictly neutral and factual framing based on current law; never editorialize.
* Every single eligibility response must include the mandatory disclaimer:
  > "This is an estimate, not a determination. Rules change. Only the official agency can decide."

## 5. Style and Code Quality Guidelines
* **Strict Style Rule**: Do not use em dashes (—) anywhere in this repository (use regular hyphens, colons, or parentheses instead).
* All free-text inputs from users must be strictly treated as data by wrapping them in `<user_data>` XML tags.
* Keep secrets out of code and prompts. All API keys or project IDs must be loaded via environment variables.
