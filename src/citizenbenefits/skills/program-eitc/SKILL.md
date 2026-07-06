---
name: program-eitc
description: Earned Income Tax Credit (EITC) eligibility navigation skill.
triggers:
  - query mentions EITC, earned income tax credit, tax refund, child tax credit
  - factor evaluation is requested for tax credit benefits
---

# EITC (Earned Income Tax Credit) Eligibility Skill

## 1. Anonymous Factors Used
- `status`: Immigration/Citizenship status
- `household_size`: Number of members in household
- `total_income_band`: Household total income band (FPL-relative)
- `earned_income_share`: Earned income share (none, some, most, all)
- `age_band`: Age of members (under_18, 18_59, 60_64, 65_plus)
- `has_disability`: Any disabled members (yes/no)
- `num_children`: Number of children in household
- `is_married`: Marriage status (filing status)

## 2. Authoritative Source URLs
- Primary: https://www.irs.gov/eitc (Internal Revenue Service)

## 3. Eligibility Logic & Placeholders
- **Citizenship/Immigration Status Gate**:
  - Qualifying: `us_citizen`, `us_national`, `lawful_permanent_resident`, or `veteran_or_military`.
  - Note: COFA citizens may qualify depending on tax residency rules under `{eitc_cofa_tax_residency_rule}`.
- **Earned Income and Adjusted Gross Income (AGI) Limits**:
  - Household monthly income (extrapolated annually from `total_income_band` and `earned_income_share`) must be <= `{eitc_income_limit}` for the number of children (`num_children`) and filing status (single or married, `is_married`).
  - Investment income must be <= `{eitc_investment_income_limit}`.
- **Age Rules (for those with no qualifying children)**:
  - If `num_children` is 0: The applicant (or spouse if `is_married` is true) must be >= `{eitc_childless_min_age}` and <= `{eitc_childless_max_age}`.

## 4. Legislative Update Note (OBBBA)
- The One Big Beautiful Bill Act (OBBBA, P.L. 119-21) updated the childless EITC age bands and basic credit calculations, with phases running through tax year 2028.
- Every threshold retrieved by the Grounding Tool must specify its `as_of_date` and tax year context.

## 5. Mandatory Disclaimer
> "This is an estimate, not a determination. Rules change. Only the official agency can decide."
