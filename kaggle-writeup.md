# Citizen Benefits
### Kaggle Writeup - Google/Kaggle 5-Day AI Agents Intensive Capstone
### Track: Agents for Good

---

## Agent Name

**Citizen Benefits** - Find the benefits you qualify for.

- [Live Demo](https://citizenbenefits-api-fzxvf6yczq-uc.a.run.app)
- [Code](https://github.com/Unix-Dev-Ops/citizen-benefits)
- [Video](https://www.youtube.com/watch?v=Lg9Bb8VGDcU)

---

## Problem It Solves

Unclaimed benefits are a worldwide problem: people everywhere miss support
they are entitled to because eligibility systems are opaque. Citizen Benefits
starts with the United States, where millions of eligible people never claim
benefits they qualify for. The rules are confusing, they changed substantially
under recent federal legislation (2025), they vary by state, and asking for
help usually means handing over personal information. Citizen Benefits is an
autonomous agent that takes ONLY anonymous situational factors (state,
household size, income band, age band, disability, pregnancy, children,
veteran status) and estimates which of five federal programs a person likely
qualifies for: SNAP, Medicaid/CHIP, EITC, LIHEAP, and WIC. It explains why in
plain language, in four languages, and routes the person to the official
application portal for their state.

It is a navigator, not a determiner. Every single response carries the
disclaimer: "This is an estimate, not a determination. Rules change. Only the
official agency can decide."

---

## How It Works

A Google ADK 2.0 graph Workflow orchestrates single-responsibility nodes:
PiiGuard (regex + a gemini-3.5-flash structured check that FAILS CLOSED on any
error) rejects any input containing personal information before processing.
StatusGate evaluates citizenship/immigration status first and stops early with
a factual scope statement when programs do not cover the selected status.
EligibilityEngine evaluates each program using interval logic over income
bands: if a band straddles a threshold, the agent answers POSSIBLY rather than
guessing. GroundingTool fetches current thresholds at runtime with live HTML
parsers for SNAP (USDA/FNA), EITC (IRS), and WIC (USDA/FNA), each gated by
sanity-range validation; Medicaid and LIHEAP fall back to fixtures verified
against official sources, and any ungrounded result is capped at POSSIBLY,
never a confident answer. Explainer and Router assemble neutral plain-language
reasons, the mandatory disclaimer, and the state application link. A FastAPI
app on Cloud Run serves the agent and a fully redesigned multilingual
(EN/ES/FR/DE) frontend with localized results, complete Open Graph/Twitter
metadata, and an A+ grade on securityheaders.com.

---

## Tools & APIs Used

- Google ADK 2.0 (graph Workflow API) - agent orchestration
- Gemini 3.5 Flash - PII detection guardrail + LLM-as-judge evaluation
- Google AI Studio API (free tier) + Secret Manager for key handling
- FastAPI + Uvicorn - web layer; aiosqlite session records (anonymous only)
- httpx + BeautifulSoup - live grounding parsers for USDA/FNA, IRS
- pytest + Gherkin scenarios - 19 unit tests
- agents-cli with custom CodeExecutionMetrics + a local LLM-as-judge metric
- Google Cloud Run + Cloud Build + Artifact Registry - deployment
- Antigravity Editor (sandboxed mode) - the entire build was vibe-coded

---

## Course Concepts Demonstrated (5 of 3 required)

1. **Multi-agent orchestration with ADK graph workflows (Day 1/2)** - a
   dictionary-routed Workflow graph: pii_guard -> status_gate ->
   eligibility_engine -> router -> explainer, with dedicated terminal nodes
   for refusals, ineligibility, and invalid input.

2. **Agent Skills with progressive disclosure (Day 3)** - one SKILL.md per
   program (program-snap, program-medicaid-chip, program-eitc, program-liheap,
   program-wic), each defining trigger conditions, the anonymous factors it
   uses, authoritative sources, and eligibility logic with PLACEHOLDER numbers
   that only the grounding tool may fill.

3. **Sessions & memory (Day 3)** - anonymous SessionRecords (UUID, request,
   results) persisted per session via aiosqlite; no PII can enter memory
   because PiiGuard sits upstream of everything.

4. **Security & evaluation (Day 4)** - the core story. NO-PII by design with
   an actively refusing, fail-closed guard; prompt-injection defense by
   wrapping all user input in <user_data> delimiters; a status gate that
   prevents needless data collection; trajectory evaluation over 20 canned
   scenarios with six metrics all at 1.0000: pii_never_leaked,
   disclaimer_present, zero_prompt_leakage, correct_status_gating,
   eligibility_grounded, and neutral_framing (a true LLM-as-judge run locally
   through the AI Studio API); A+ on securityheaders.com with a hardened CSP
   (verify: https://securityheaders.com/?q=citizenbenefits-api-fzxvf6yczq-uc.a.run.app).

5. **Spec-driven, production-grade development (Day 5)** - a
   Markdown+YAML+Gherkin spec as the single source of truth; every Gherkin
   scenario maps to a pytest test; Dockerized non-root deployment to Cloud Run
   with the API key mounted from Secret Manager and a human-in-the-loop
   checkpoint before every deploy.

---

## Challenges & How I Solved Them

**1. Benefit rules recently changed, and model memory is wrong.** 2025
federal legislation changed SNAP work requirements (ABAWD ceiling raised to 65, veterans no
longer auto-exempt as of Feb 2026), Medicaid work requirements, and more. The
solution was architectural: no threshold may originate from model memory.
SKILL.md files carry placeholders; the grounding tool fills them at runtime;
missing data forces POSSIBLY. The live parsers proved the point immediately:
on first run, the SNAP parser caught that my own fixture values were stale
(standard deduction $200 vs the real FY2026 $209; asset limits $2,750/$4,250
vs the real $3,000/$4,500), and the EITC parser caught stale tax-year limits.
The agent corrected me.

**2. Income bands vs precise thresholds.** Privacy-first means collecting
income as a BAND, but thresholds are exact numbers. Early engine code
estimated a midpoint income, which silently misclassified people near limits.
I replaced it with interval logic: a band entirely under a limit passes,
entirely over fails, and a band that straddles the limit returns POSSIBLY
with an explanation. The agent refuses to guess inside a band.

**3. The eval framework could not reach Vertex AI.** The built-in LLM-as-judge
routes through the Vertex AI Evaluation Service, which my free-tier AI Studio
setup cannot use (403). I reimplemented the judge as a local custom metric
calling gemini-3.5-flash directly through the same AI Studio auth the app
uses, temperature 0, structured JSON verdicts, with API errors recorded as
errors rather than fake passes.

**4. Trust but verify the coding agent.** Twice, the coding agent reported
completed work (result sorting, wording changes, a minified JS file) that did
not exist on disk. I adopted proof-by-grep: every prompt now requires the
agent to print the grep or ls output that proves each change landed. This
single practice caught every subsequent hallucinated claim.

**5. Government pages fight scrapers.** LIHEAP's site returns an empty 202
(bot shield) and Medicaid publishes state-by-state tables with no single
national threshold. Rather than forcing bad parses, those programs stay on
fixtures verified against official sources, return grounded=false, and cap at
POSSIBLY, with the reason telling the user to confirm with the agency. Honest
fallback beats fake confidence.

---

## What I'd Build Next

- Live parsers for Medicaid (per-state tables) and a LIHEAP data source that
  permits programmatic access
- State-level rule variations (BBCE gross-income limits vary by state)
- Backend-native localization of results (currently a frontend template
  matcher translates the finite set of reason templates)
- Country modules for the seven coming-soon countries (Canada, UK,
  Australia, Germany, France, Spain, Mexico), each with its own grounded
  program skills
- A verified notify list for those countries, with a real
  consent flow (the current UI honestly says the feature is coming soon and
  collects nothing)
- Mechanical link-freshness checks in CI for every state application portal
- OpenTelemetry trace export for the trajectory eval

---

## Rationale

Benefits complexity is a solved-problem-in-theory that remains unsolved in
practice because the information layer is hostile: rules change, sites vary,
and every helper wants your data. An agent that is aggressively private,
aggressively grounded, and honest about uncertainty is the version of this
tool that deserves to exist. Every design decision above serves one of those
three properties.
