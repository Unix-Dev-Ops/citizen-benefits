---
name: program-liheap
description: Low Income Home Energy Assistance Program (LIHEAP) eligibility navigation skill.
triggers:
  - query mentions LIHEAP, heating bill, utility assistance, energy help, cooling bill
  - factor evaluation is requested for energy assistance benefits
---

# LIHEAP (Low Income Home Energy Assistance Program) Eligibility Skill

## 1. Anonymous Factors Used
- `status`: Immigration/Citizenship status
- `household_size`: Number of members in household
- `total_income_band`: Household total income band (FPL-relative, used for SMI/FPL limit tests)
- `earned_income_share`: Earned income share (none, some, most, all)
- `age_band`: Age of members (under_18, 18_59, 60_64, 65_plus)
- `has_disability`: Any disabled members (yes/no)
- `num_children`: Number of children in household
- `state`: 2-letter state abbreviation

## 2. Authoritative Source URLs
- Primary: https://www.acf.hhs.gov/ocs/programs/liheap (HHS Administration for Children and Families)

## 3. Eligibility Logic & Placeholders
- **Citizenship/Immigration Status Gate**:
  - Qualifying: `us_citizen`, `us_national`, `cofa_citizen`, `veteran_or_military`, or `lawful_permanent_resident` (LPR).
  - Note: LPR status must meet standard qualification rules, though states have discretion on waiting period implementation for emergency utility assistance under `{liheap_state_lpr_discretion}`.
- **Income Limits**:
  - Household monthly income (estimated from `total_income_band`) must be <= `{liheap_income_limit_fpl_percentage}`% of the FPL for `household_size` in the given `state`, OR <= `{liheap_income_limit_smi_percentage}`% of the State Median Income (SMI) for `household_size` (whichever is greater, subject to state policy).
  - Federal maximum guideline is the greater of `{liheap_max_fpl_percentage}`% FPL or `{liheap_max_smi_percentage}`% SMI.

## 4. Legislative Update Note (OBBBA)
- The One Big Beautiful Bill Act (OBBBA, P.L. 119-21) increased emergency contingency funding and adjusted eligibility maximums through fiscal year 2028.
- Every threshold retrieved by the Grounding Tool must specify its `as_of_date` and check state-specific implementation parameters.

## 5. Mandatory Disclaimer
> "This is an estimate, not a determination. Rules change. Only the official agency can decide."
