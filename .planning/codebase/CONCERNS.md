---
last_mapped_commit: 4c188b479c5772b749da0eba4e25538e41708a25
last_mapped_at: 2026-10-06
---
# Codebase Concerns

**Analysis Date:** 2026-10-06

## Tech Debt

**Monolithic ShiftManager Class:**
- Issue: `models/shift_manager.py` contains ~2000 lines handling rotation logic, exception grouping, backups, JSON parsing, and audit history. Migration to `RotationEngine` and `ConfigRepository` started but legacy implementation remains.
- Files: `models/shift_manager.py`, `models/rotation_engine.py`
- Impact: Difficult to maintain, high regression risk when modifying rotation rules.
- Fix approach: Complete delegation of calculation rules to dedicated domain services and split persistence concerns.

**Large GUI Tab Files:**
- Issue: `views/tabs/tab_plan.py` (1189 lines) and `views/tabs/tab_settings.py` (1151 lines) contain extensive widget assembly, event handlers, and presentation logic.
- Files: `views/tabs/tab_plan.py`, `views/tabs/tab_settings.py`
- Impact: Hard to isolate UI bugs and test visually without launching the entire desktop window.
- Fix approach: Extract sub-components (e.g. `PersonnelTable`, `SmtpSettingsForm`, `ExceptionFilterBar`) into modular widgets under `views/components/`.

## Known Bugs

**Week Duration Transition Inconsistency (Monday-Sunday vs Monday-Monday):**
- Symptoms: `tests/test_shift_manager_hardening.py` fails with `datetime.date(2027, 1, 4) != datetime.date(2027, 1, 3)` because the shift calendar logic transitioned from 7-day Sunday ends to Monday-to-Monday shifts starting October 2026.
- Files: `models/shift_manager.py`, `tests/test_shift_manager_hardening.py`, `tests/test_monday_to_monday_shifts.py`
- Trigger: Boundary weeks between December and January across years.
- Workaround: Ensure tests and logic adhere to the unified transition rule defined in `tests/test_monday_to_monday_shifts.py`.

**Future Month Preview Chaining Discrepancy:**
- Symptoms: `tests/test_future_preview.py::FuturePreviewChainingTests::test_advance_future_month_preserves_preview_parity` fails when previewing and closing months far into the future with exceptions.
- Files: `controllers/main_controller.py`, `models/shift_manager.py`, `tests/test_future_preview.py`
- Trigger: Calling `advance_queue` on a future month with exceptions and re-previewing.
- Workaround: Recalculate using intermediate snapshots sequentially.

**Edge Case in Manual Assignment with Pending Queues:**
- Symptoms: `tests/test_manual_assignments_edge_cases.py::test_manual_assignment_of_other_person_keeps_pendientes_intact` fails when assigning a third party manually while another member is in `pendientes`.
- Files: `models/shift_manager.py`, `tests/test_manual_assignments_edge_cases.py`
- Trigger: Manual assignment on week 1 followed by normal rotation on week 2.
- Workaround: Explicitly preserve pending queue pointers during manual assignments.

**Recalculation Key Miss in Far-Future History:**
- Symptoms: `tests/test_shift_manager_invariants.py::ClosureBehaviourTests::test_recalculating_closed_month_does_not_move_global_pointer_backwards` throws `KeyError: '2030-01-14_2030-01-20'`.
- Files: `models/shift_manager.py`, `tests/test_shift_manager_invariants.py`
- Trigger: Recalculating closure invariants in year 2030 where week boundary dates differ under current calculation.
- Workaround: Standardize date range generation keys for far-future years.

## Security Considerations

**Unencrypted Credential Storage in Local Files:**
- Risk: SMTP passwords and webhook URLs are stored in plain text in `.env` or `config.json`.
- Files: `.env`, `config.json`, `utils/env_helper.py`, `utils/email_notifier.py`
- Current mitigation: `.env` and `config.json` are listed in `.gitignore` and access is restricted to the local user account.
- Recommendations: Recommend Windows Credential Manager (`keyring` package) for storing sensitive SMTP passwords on Windows.

## Performance Bottlenecks

**Full Suite Execution Time:**
- Problem: Running `pytest` takes ~3.5 minutes (~213 seconds) due to extensive cross-month calculations and UI initialization cycles in tests.
- Files: `tests/`
- Cause: Many tests spin up full `TurnosApp` or run multi-year shift simulations without mocking sleep/render cycles.
- Improvement path: Separate fast unit tests from slow integration/GUI tests using pytest markers (`@pytest.mark.slow`).

## Fragile Areas

**State Mutation in `config.json`:**
- Files: `config.json`, `models/shift_manager.py`, `models/config_repository.py`
- Why fragile: All operational state (queue pointers, history, exceptions, personnel) lives in one JSON file. A manual edit or schema mismatch can disrupt future shift allocations.
- Safe modification: Always modify through the UI or `MainController`; verify atomic backups in `backups/` are intact.
- Test coverage: Extensive invariant tests in `tests/test_shift_manager_invariants.py`.

## Scaling Limits

**Personnel Team Size:**
- Current capacity: Designed for teams of ~16 persons with weekly shifts.
- Limit: UI dropdowns and Excel monthly grid layout assume team sizes up to ~30-40 persons before vertical scrolling in Excel tables becomes unwieldy.
- Scaling path: Paginated or filtered Excel exports if staff size grows significantly.

## Dependencies at Risk

**`customtkinter` Development Cadence:**
- Risk: Upstream CustomTkinter updates are infrequent and may have quirks on newer Python versions (such as Python 3.14).
- Impact: Potential UI rendering glitches on Windows DPI scaling.
- Migration plan: Maintain custom geometry workarounds (`setup_windows_dpi()` in `main.py`).

## Missing Critical Features

**Automated CI/CD Pipeline:**
- Problem: No GitHub Actions or CI pipeline configured to run tests automatically on git push or pull requests.
- Blocks: Early detection of regressions before distributing builds.

## Test Coverage Gaps

**UI Component Unit Tests:**
- What's not tested: Standalone visual rendering and themes across various screen resolutions.
- Files: `views/tabs/tab_calendar.py`, `views/components/dialogs.py`
- Risk: Visual overlapping or label clipping on specific display scaling factors.
- Priority: Medium

---

*Concerns audit: 2026-10-06*
