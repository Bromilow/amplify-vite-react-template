# 📘 PROJECT_RULES.md

_Last updated: 5 August 2025_

These are the global implementation rules for Replit AI to follow when modifying or extending the South African Payroll Management System codebase.

---

## 🔁 Auto-Update Workflow

When responding to a prompt, Replit AI must:

1. **Evaluate the current codebase** to determine feature state:
   - ✅ Fully Implemented
   - ⚠️ Partially Implemented
   - ❌ Not Implemented

2. **Cross-reference the following files (in `/reports/`)**:
   - `PROJECT_ISSUES.md`
   - `FEATURES_AND_GAPS_MASTER.md`
   - Any relevant `TODO_*.md` files

3. **Update reports accordingly**:
   - Modify `FEATURES_AND_GAPS_MASTER.md` with updated status tags and brief notes
   - Add any newly discovered bugs to `PROJECT_ISSUES.md`
   - Append specific issues to relevant TODO files (e.g. `TODO_EMPLOYEE_FORM.md`)

---

## 🔄 Knock-On Effect Awareness

Replit AI must identify and handle **knock-on effects** of any change. For example:

If modifying the `Add Employee` form:
- Re-evaluate the `Edit Employee` modal
- Check:
  - Validation logic
  - Payroll and tax calculation interactions
  - CSV import/export
  - Template rendering
  - Any APIs or routes using this data

Apply this principle to all:
- Shared forms
- Calculated fields
- Templates
- Multi-step modals
- Configuration-based components

---

## 🧪 Consistency & Compliance Rules

- No hardcoded tax rates or thresholds
  - Use dynamic config: `get_sars_config(company_id)`
  - In templates: use `{{ sars.uif_percent }}`, `{{ sars.tax_year_start_display }}`, etc.
  - Format correctly: `R {{ sars.value }}` or `{{ (rate * 100)|round(2) }}%`
- All new values or calculations must pass through the SARS config system

---

## 📝 Documentation & Traceability

All code updates must:
- Maintain consistency with logic in the `/services` layer
- Use shared helpers/utilities where applicable
- Reflect changes in:
  - `FEATURES_AND_GAPS_MASTER.md`
  - `PROJECT_ISSUES.md`
  - Relevant `TODO_*.md`

---

## 🔄 Auto-Documentation Rule

After every change or fix, Replit AI must:
- Identify and update affected project documentation files
- Add an ISO-formatted timestamp next to each update
- Ensure all documentation reflects the true state of the codebase

**Affected Files:**
- `FEATURES_AND_GAPS.md` → Feature status, gaps, enhancements
- `PROJECT_ISSUES.md` → Bugs, edge cases, system limitations
- `PRODUCTION_ROADMAP.md` → Deployment sequencing, milestones

**Update Behavior:**
After completing any implementation task, Replit AI must:
1. Add or update the relevant section in one or more of the above files
2. Use this timestamp format: `2025-08-06T15:52:00+02:00`
3. Example: `✅ Cell number format now accepts both 07x and +27 formats – 2025-08-06T15:52:00+02:00`

**Self-Enforcement:**
Replit AI must now assume this rule is permanently in effect and no longer require explicit reminders to update documentation after future changes.

---

By following these rules, Replit AI will ensure consistent, traceable, and compliant updates to the payroll system.
