# Test Implementation Priority Matrix

## 🔴 Critical Path (P0) - Must Have First
*Core functionality - system cannot work without these*  
**Estimated Time:** 8-12 hours

| Test File | Coverage | Reason | Key Tests | Blockers |
|-----------|----------|--------|-----------|----------|
| `test_state_manager.py` | ~25% | Foundation of entire system | • load_state() validation<br>• save_state() atomic writes<br>• init_project() & detect_project_type()<br>• Backup/recovery mechanisms | Blocks all integration & e2e tests |
| `test_cli_commands.py` | ~20% | Primary user interface | • All command parsing (add, map, update)<br>• Argument validation<br>• Error handling<br>• Command chaining | Blocks workflow tests |
| `test_state_persistence.py` | ~10% | Data integrity non-negotiable | • Save/load cycle integrity<br>• Backup file creation<br>• Corrupted JSON recovery<br>• Atomic write guarantees | Data loss risk |

**Total Critical:** 3 files, ~55% of unit test coverage

---

## 🟠 Essential Features (P1) - High Priority
*Key features users interact with daily*  
**Estimated Time:** 10-15 hours

| Test File | Coverage | Reason | Key Tests |
|-----------|----------|--------|-----------|
| `test_file_scanning.py` | ~15% | Determines what gets analyzed | • scan_files() with various structures<br>• is_ignored() pattern matching<br>• .gitignore parsing<br>• Size threshold enforcement |
| `test_coverage_calc.py` | ~10% | Drives stopping criteria | • Coverage percentage accuracy<br>• Quality metric (test/doc filtering)<br>• update_stats() correctness |
| `test_schema_validation.py` | ~8% | Guards Phase 2 quality | • Missing description detection<br>• Orphaned file detection<br>• Broken dependency links<br>• Empty systems check |
| `test_session_tracking.py` | ~10% | Enables multi-session workflow | • session-start/end lifecycle<br>• Session history recording<br>• Delta calculation<br>• Gate A/B detection |

**Total Essential:** 4 files, ~43% of test coverage

---

## 🟡 Important (P2) - Should Have Soon
*Enhances reliability and user experience*  
**Estimated Time:** 6-8 hours

| Test File | Coverage | Reason | Key Tests |
|-----------|----------|--------|-----------|
| `test_workflow.py` | ~8% | Tests real-world usage patterns | • Multi-command sequences<br>• System creation workflows<br>• Cross-session persistence |
| `test_utilities.py` | ~5% | Prevents subtle bugs | • similar_text() duplicate detection<br>• sanitize_for_mermaid() correctness<br>• Edge cases in helpers |
| `test_new_project_init.py` | ~7% | E2E initialization testing | • Django/Flask/Node detection<br>• Overwrite handling<br>• Fresh state creation |

**Total Important:** 3 files, ~20% of test coverage

---

## 🟢 Complementary (P3) - Nice to Have
*Polishing and advanced features*  
**Estimated Time:** 4-6 hours

| Test File | Coverage | Reason | Key Tests |
|-----------|----------|--------|-----------|
| `test_phase1_workflow.py` | ~5% | Validates Phase 1 completeness | • Progressive coverage increase<br>• System completeness tracking |
| `test_phase2_workflow.py` | ~3% | Validates Phase 2 consumption | • --summary flag output<br>• Graph generation accuracy |
| `test_stopping_criteria.py` | ~4% | Tests Gate A/B logic | • 90%+ coverage detection<br>• 3 low-yield session detection |
| `test_incremental_survey.py` | ~5% | Multi-session integration | • 3-session workflows<br>• Coverage progression |
| `test_validation_mode.py` | ~3% | Phase 1.5 testing | • Error detection<br>• Clean state validation |

**Total Complementary:** 5 files, ~20% of test coverage

---

## 📊 Implementation Strategy

### Week 1: Critical Path (Days 1-3)
- Day 1: `test_state_manager.py` - Get core state operations working
- Day 2: `test_cli_commands.py` - Ensure CLI interface is solid
- Day 3: `test_state_persistence.py` - Lock down data integrity

### Week 2: Essential Features (Days 4-7)
- Day 4: `test_file_scanning.py` - File discovery accuracy
- Day 5: `test_coverage_calc.py` + `test_schema_validation.py` - Metrics & validation
- Day 6-7: `test_session_tracking.py` - Multi-session support

### Week 3: Important & Complementary (Days 8-10)
- Day 8: `test_workflow.py` + `test_utilities.py` - Integration patterns
- Day 9: `test_new_project_init.py` - E2E initialization
- Day 10: Remaining P3 tests as time allows

---

## 🎯 Quick Start Recommendation

**Start with these 3 files in order:**

1. **`test_state_manager.py`** - Without this, nothing else matters
2. **`test_cli_commands.py`** - Validates the user-facing contract
3. **`test_state_persistence.py`** - Ensures data safety

After these 3, you'll have ~55% coverage and all critical paths protected. Everything else builds on this foundation.

---

## 📈 Coverage Goals by Milestone

| Milestone | Files Complete | Est. Coverage | Status |
|-----------|----------------|---------------|---------|
| MVP (Critical Path) | 3 files | ~55% | 🔴 Start here |
| Production Ready | +4 files (Essential) | ~85% | 🟠 Week 2 target |
| Hardened | +3 files (Important) | ~95% | 🟡 Week 3 target |
| Complete | All 15 files | ~100% | 🟢 Final polish |
