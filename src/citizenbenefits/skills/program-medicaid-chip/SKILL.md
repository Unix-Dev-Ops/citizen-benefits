---
name: program-medicaid-chip
description: Medicaid and Children's Health Insurance Program (CHIP) eligibility navigation skill.
triggers:
  - query mentions Medicaid, CHIP, healthcare for low income, health insurance assistance
  - factor evaluation is requested for healthcare coverage benefits
---

# Medicaid & CHIP Eligibility Skill

## 1. Anonymous Factors Used
- `status`: Immigration/Citizenship status
- `household_size`: Number of members in household
- `total_income_band`: Household total income band (FPL-relative, used for MAGI/non-MAGI limits)
- `earned_income_share`: Earned income share (none, some, most, all)
- `age_band`: Age of members (under_18, 18_59, 60_64, 65_plus)
- `has_disability`: Any disabled members (yes/no)
- `is_pregnant`: Any pregnant members
- `num_children`: Number of children in household
- `state`: 2-letter state abbreviation

## 2. Authoritative Source URLs
- Primary: https://www.medicaid.gov (Medicaid.gov)
- Secondary: https://www.kff.org (Kaiser Family Foundation state-by-state data)

## 3. Eligibility Logic & Placeholders
- **Citizenship/Immigration Status Gate**:
  - Qualifying: `us_citizen`, `us_national`, `cofa_citizen`, `veteran_or_military`, or `lawful_permanent_resident` (LPR).
  - Note: LPR status must meet one of the following:
    - Held LPR status for >= `{medicaid_lpr_waiting_period_years}`.
    - Exemption: LPR under age 18, receiving disability benefits, pregnant (`is_pregnant` is true), or `is_veteran_or_military` is true (varies by state).
- **Income Thresholds (MAGI-based)**:
  - For non-disabled adults: Household monthly income (estimated from `total_income_band`) must be <= `{medicaid_adult_limit_fpl_percentage}`% of the FPL for `household_size` in the given `state` (only applicable if state expanded Medicaid).
  - For pregnant individuals: Household monthly income must be <= `{medicaid_pregnancy_limit_fpl_percentage}`% of the FPL for `household_size` in the given `state`.
  - For children (CHIP/Medicaid): Household monthly income must be <= `{medicaid_child_limit_fpl_percentage}`% of the FPL for `household_size` in the given `state`.
  - For elderly/disabled: Evaluated against non-MAGI rules where assets must be <= `{medicaid_non_magi_asset_limit}` and income <= `{medicaid_elderly_disabled_limit_fpl_percentage}`% of the FPL.

## 4. Legislative Update Note (OBBBA & Work Requirements)
- The One Big Beautiful Bill Act (OBBBA, P.L. 119-21) has expanded post-pregnancy coverage and modified state matching rules for Medicaid expansion through 2028.
- Every threshold retrieved by the Grounding Tool must specify its `as_of_date` and check for OBBBA implementation phase in the target state.
- Work Requirement Updates: Under OBBBA, individuals in the `60_64` age band are inside the Medicaid 19-64 work-requirement band (if applicable by state policy), whereas those in the `65_plus` age band are exempt.

## 5. Mandatory Disclaimer
> "This is an estimate, not a determination. Rules change. Only the official agency can decide."
