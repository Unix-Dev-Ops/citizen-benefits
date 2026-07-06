---
name: program-snap
description: Supplemental Nutrition Assistance Program (SNAP) eligibility navigation skill.
triggers:
  - query mentions SNAP, food stamps, food assistance, or grocery help
  - factor evaluation is requested for food assistance benefits
---

# SNAP (Supplemental Nutrition Assistance Program) Eligibility Skill

## 1. Anonymous Factors Used
- `status`: Immigration/Citizenship status
- `household_size`: Number of members in household
- `total_income_band`: Household total income band (FPL-relative, used for gross/net tests)
- `earned_income_share`: Earned income share (none, some, most, all) to apply 20% deduction
- `age_band`: Age of members (under_18, 18_59, 60_64, 65_plus)
- `has_disability`: Any disabled members (yes/no)
- `is_pregnant`: Any pregnant members
- `num_children`: Number of children in household
- `state`: 2-letter state abbreviation
- `is_veteran_or_military`: Special exemptions for LPR wait periods

## 2. Authoritative Source URLs
- Primary: https://www.fns.usda.gov/snap/eligibility (USDA Food and Nutrition Service)
- Secondary: The applicant's state agency portal (Ohio Department of Job and Family Services, etc.)

## 3. Eligibility Logic & Placeholders
- **Citizenship/Immigration Status Gate**:
  - Qualifying: `us_citizen`, `us_national`, `cofa_citizen`, `veteran_or_military`, or `lawful_permanent_resident` (LPR).
  - Note: LPR status must meet one of the following:
    - Held LPR status for >= `{snap_lpr_waiting_period_years}`.
    - Exemption: LPR under age 18, receiving disability benefits, or `is_veteran_or_military` is true (no waiting period).
- **Gross Income Limit**:
  - Household monthly gross income (estimated from `total_income_band`) must be <= `{snap_gross_income_limit_fpl_percentage}`% of the FPL for `household_size` in the given `state`.
  - Special Rule: Households with elderly (`age_band` is `60_64` or `65_plus`) or disabled (`has_disability` is true) members are exempt from the gross income limit (use the Net income test only).
- **Net Income Limit**:
  - Household monthly net income must be <= `{snap_net_income_limit_fpl_percentage}`% of the FPL for `household_size` in the given `state`.
  - Deductions: Apply a 20% deduction to earned income using the `earned_income_share` factor.
- **Asset/Resource Limit** (if applicable in state):
  - Assets must be <= `{snap_asset_limit_standard}`.
  - If household contains an elderly (`age_band` is `60_64` or `65_plus`) or disabled (`has_disability` is true) member, assets must be <= `{snap_asset_limit_elderly_disabled}` (a higher asset limit, grounded at runtime).

## 4. Legislative Update Note (OBBBA & Work Requirements)
- The One Big Beautiful Bill Act (OBBBA, P.L. 119-21) has modified SNAP work requirements, asset limits, and transitional benefits. These changes are phased in with effective dates through 2028.
- Every threshold retrieved by the Grounding Tool must specify its `as_of_date` and check for OBBBA implementation phase in the target state.
- Work Requirement Updates: Under OBBBA, individuals in the `60_64` age band are subject to the 80-hour work requirement (ABAWD ceiling raised from 55 to 65), whereas those in the `65_plus` age band are codified exempt.
- Work Requirement Exemption Update: As of Feb 1 2026, veterans are no longer automatically exempt from SNAP work requirements. Work requirements and exemptions must be grounded at runtime based on active dates.

## 5. Mandatory Disclaimer
> "This is an estimate, not a determination. Rules change. Only the official agency can decide."
