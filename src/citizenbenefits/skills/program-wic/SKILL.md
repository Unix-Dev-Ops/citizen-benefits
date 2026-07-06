---
name: program-wic
description: Special Supplemental Nutrition Program for Women, Infants, and Children (WIC) eligibility navigation skill.
triggers:
  - query mentions WIC, baby formula, breastfeeding assistance, pregnancy nutrition, infant food
  - factor evaluation is requested for maternal and child nutrition benefits
---

# WIC (Women, Infants, and Children) Eligibility Skill

## 1. Anonymous Factors Used
- `status`: Immigration/Citizenship status
- `household_size`: Number of members in household
- `total_income_band`: Household total income band (FPL-relative)
- `earned_income_share`: Earned income share (none, some, most, all)
- `age_band`: Age of members (under_18, 18_59, 60_64, 65_plus)
- `has_disability`: Any disabled members (yes/no)
- `is_pregnant`: Any pregnant members
- `num_children`: Number of children in household
- `state`: 2-letter state abbreviation

## 2. Authoritative Source URLs
- Primary: https://www.fns.usda.gov/wic (USDA Food and Nutrition Service WIC)

## 3. Eligibility Logic & Placeholders
- **Citizenship/Immigration Status Gate**:
  - Qualifying: WIC is exempt from welfare citizenship restrictions. Qualifying status is `{wic_status_exempt}` (all statuses, including undocumented and non-qualifying statuses, are eligible for WIC benefits if they meet other criteria).
- **Categorical Requirement**:
  - The household must include someone who is pregnant (`is_pregnant` is true), breastfeeding/postpartum, an infant (under age 1), or a child under age `{wic_child_max_age}`.
- **Income Limit**:
  - Household monthly income (estimated from `total_income_band`) must be <= `{wic_income_limit_fpl_percentage}`% of the FPL for `household_size` in the given `state`.
  - Adjunct Eligibility: If the applicant participates in SNAP, Medicaid, or TANF, they are automatically income-eligible under `{wic_adjunct_eligibility_rule}`.

## 4. Legislative Update Note (OBBBA)
- The One Big Beautiful Bill Act (OBBBA, P.L. 119-21) expanded age limits for children and increased vegetable and fruit cash-value vouchers through 2028.
- Every threshold retrieved by the Grounding Tool must specify its `as_of_date` and WIC state plan details.

## 5. Mandatory Disclaimer
> "This is an estimate, not a determination. Rules change. Only the official agency can decide."
