# Stage 1: Foundation Audit Report
## Schema & Metrics Analysis

**Date:** November 28, 2025  
**Scope:** Data layer (schema, metrics, stopping criteria, validation logic)

---

## 1. SCHEMA STRUCTURE

### 1.1 Current `architecture.json` Schema

```json
{
  "schema_version": "2.2",
  "metadata": {
    "project_name": "",
    "project_type": "Unknown",
    "last_updated": "",
    "phase": "survey",
    "total_sessions": 0,
    "scan_stats": {
      "total_files_scanned": 0,
      "significant_files_total": 0,
      "mapped_files_count": 0,
      "coverage_percentage": 0.0,
      "coverage_quality": 0.0
    },
    "session_history": []
  },
  "systems": {
    "SystemName": {
      "description": "TODO",
      "completeness": 0,        // COMPUTED
      "clarity": "low",         // COMPUTED
      "key_files": [],
      "dependencies": [],
      "insights": [],
      "complexities": []
    }
  },
  "progress": {
    "systems_identified": 0,
    "systems_complete": 0,
    "estimated_overall_completeness": 0
  }
}
```

### 1.2 Field Classification

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| `completeness` | Computed | `compute_completeness()` | Cannot be manually set |
| `clarity` | Computed | `compute_clarity()` | Auto-derived from completeness + insights |
| `coverage_percentage` | Computed | File scanner | Percentage of significant files mapped |
| `coverage_quality` | Computed | `calculate_coverage_quality()` | Excludes test/doc files |
| `key_files` | Manual | Flash via `map` command | User-provided |
| `insights` | Manual | Flash via `insight` command | Validated on entry |
| `dependencies` | Manual | Flash via `dep` command | User-provided |
| `session_history` | Auto | `session-start`/`session-end` | Tracks progress |

**Key Finding:** The separation between computed and manual fields is clean. No self-grading vectors detected.

---

## 2. METRIC FORMULAS

### 2.1 Completeness (0-100 points)

**Formula:**
```python
file_score = min(file_count / 10.0, 1.0) * 40      # Max 40 pts
insight_score = min(insight_count / 5.0, 1.0) * 35 # Max 35 pts
dep_score = 15 if has_dependencies else 0          # Max 15 pts
clarity_bonus = {"high": 10, "medium": 5, "low": 0}[clarity] # Max 10 pts

total = min(file_score + insight_score + dep_score + clarity_bonus, 100)
```

**What It Rewards:**
- 10 files = 40 points (caps here)
- 5 insights = 35 points (caps here)
- 1+ dependency = 15 points (binary)
- High clarity = 10 bonus points

**Analysis:**
- ✅ **No self-grading:** All inputs are countable (files, insights, dependencies)
- ✅ **Caps prevent inflation:** 10 files = same as 100 files
- ⚠️ **Gap:** Does NOT reward **interconnection mapping** (relationships between systems)
- ⚠️ **Gap:** Treats all insights equally (no quality weighting)

**Potential Gaming Vector:**
- Flash could map 10 files + write 5 shallow insights + add 1 dependency = 90% completeness
- The insight validation is supposed to prevent this, but...

---

### 2.2 Clarity (High/Medium/Low)

**Formula:**
```python
base_completeness = file_score + insight_score + dep_score  # Without clarity bonus

if insight_count >= 5 and base_completeness >= 70 and has_deps:
    return "high"
if insight_count >= 3 and base_completeness >= 40:
    return "medium"
return "low"
```

**Analysis:**
- ✅ **Objective thresholds:** No subjective judgment
- ✅ **Prevents circular logic:** Uses base completeness (doesn't include clarity bonus)
- ⚠️ **Assumes insight quality:** Counts insights, doesn't measure depth

---

### 2.3 Coverage Quality (0-100%)

**Formula:**
```python
mapped_significant = significant_files.intersection(mapped_files)
coverage_quality = len(mapped_significant) / len(significant_files) * 100
```

**Analysis:**
- ✅ **Fixed the 144% bug:** Uses set intersection, can't exceed 100%
- ✅ **Excludes test/doc files:** Only counts "significant" files
- ✅ **Objective:** Pure math, no gaming possible

---

### 2.4 Stopping Criteria

#### **Gate A: Coverage Threshold**
```python
if coverage_percentage >= 90:
    print("Gate A: Coverage threshold met")
```

**Analysis:**
- ✅ **Clear, objective**
- ⚠️ **Question:** Is 90% appropriate for all project sizes?
  - 100-file project: Need to map 90 files
  - 1000-file project: Need to map 900 files (may be excessive)

#### **Gate B: Diminishing Returns**
```python
if last_3_sessions.all(new_systems == 0 and new_files < 3):
    print("Gate B: Diminishing returns detected")
```

**Analysis:**
- ✅ **Prevents infinite loops:** Detects when exploration stalls
- ⚠️ **Question:** Does `<3 files` catch "shallow mapping"?
  - Flash could map 2 files per session with minimal insights
  - This would NOT trigger Gate B (needs 3 consecutive low-yield sessions)
  - But would those 2 files be substantive?

---

## 3. VALIDATION LOGIC (THE BLOCKING ISSUE)

### 3.1 Current Implementation

**Location:** `state_manager.py::validate_insight_quality()`

```python
def validate_insight_quality(self, text):
    errors = []
    
    # Check 1: Word count
    if len(text.split()) < MIN_WORD_COUNT:  # 15 words
        errors.append(f"Too short ({len(words)} words, need 15+)")
    
    # Check 2: Action verb (PROBLEM)
    has_action = any(verb in text.lower() for verb in ACTION_VERBS)
    if not has_action:
        errors.append("Missing [WHAT] - no clear action verb found")
    
    # Check 3: Impact word (PROBLEM)
    has_impact = any(
        re.search(r"\b" + re.escape(word) + r"\b", text_lower)
        for word in IMPACT_WORDS
    )
    if not has_impact:
        errors.append("Missing [WHY/IMPACT] - no consequence or benefit stated")
    
    return errors
```

**Then, in `add_insight()`:**
```python
if errors:
    print("⚠️  Insight quality issues:")
    for e in errors:
        print(f"   • {e}")
    
    response = input("Add anyway? (y/N): ")  # BLOCKS AGENT
    if response.lower() != "y":
        return  # Rejects insight
```

### 3.2 Problems Identified

#### **Problem 1: Exact String Matching**
```python
any(verb in text.lower() for verb in ACTION_VERBS)
```

- ❌ **Fails on morphology:** "implemented" not in list (only "implements")
- ❌ **Fails on phrases:** "is responsible for managing" won't match "manages"
- ❌ **No stemming:** "caching" won't match "caches"

**Example Failure:**
```
Insight: "This system implemented JWT validation using bcrypt hashing..."
Error: "Missing [WHAT] - no clear action verb found"
Reason: "implemented" ∉ ACTION_VERBS (only "implements" is listed)
```

#### **Problem 2: Interactive Prompt Blocks Agents**
```python
response = input("Add anyway? (y/N): ")
```

- ❌ **GCLI freezes:** Gemini CLI can't respond to interactive prompts
- ❌ **Breaks automation:** Agent workflow requires non-blocking validation

#### **Problem 3: Multi-Word Phrases Not Handled**
```python
IMPACT_WORDS = [
    'reducing latency', 'improving throughput', ...
]
```

The regex searches for exact phrases with word boundaries:
```python
re.search(r"\b" + re.escape('reducing latency') + r"\b", text)
```

This works IF the phrase appears verbatim. But:
- "reduces latency by 60%" → Fails (verb tense mismatch)
- "latency reduction of 60%" → Fails (different word form)

---

## 4. FILE CLASSIFICATION LOGIC

### 4.1 Significant File Determination

**Heuristic Pipeline:**
1. **Size check:** `size_bytes / 1024 >= SIGNIFICANT_SIZE_KB` (1 KB minimum)
2. **Directory check:** Not in `data_directories` (data/, assets/, fixtures/, etc.)
3. **Extension check:**
   - **Code extensions** (`.py`, `.ts`, `.js`, etc.) → Significant
   - **Data extensions** (`.csv`, `.log`, `.db`) → Not significant
   - **Config extensions** (`.json`, `.yaml`, `.md`) → Significant IF < 50KB
4. **Outlier check:** IQR-based detection to exclude anomalously large files

### 4.2 Analysis

**Strengths:**
- ✅ **Multi-phase filtering:** Progressive refinement
- ✅ **Statistical outlier detection:** Catches wordlists, generated files
- ✅ **Framework-agnostic:** Works for PY/TS/JS/TSX

**Potential Issues:**
- ⚠️ **Documentation counted as significant:** `.md` files treated like code
  - Is this intentional? (You mentioned wanting to exclude docs in some contexts)
- ⚠️ **Test files:** Not explicitly filtered in classification
  - Are they handled separately in coverage_quality calculation?

---

## 5. GAPS & DISCONNECTS

### 5.1 Schema Gaps

| What's Missing | Impact |
|----------------|--------|
| **Integration points field** | Flash has no place to explicitly document system boundaries/APIs |
| **Priority/criticality field** | All systems treated equally in synthesis |
| **Verification status field** | No way to mark "needs verification" vs. "confirmed" |
| **File role/category** | Files not categorized (entry point vs. utility vs. config) |

### 5.2 Metric Gaps

| Issue | Current State | Desired State |
|-------|--------------|---------------|
| **Interconnection rewards** | Completeness doesn't reward relationship mapping | Should weight dependencies higher |
| **Insight quality weighting** | All insights count equally | Should reward depth/specificity |
| **Coverage threshold flexibility** | Fixed 90% for all projects | Should scale with project size? |

### 5.3 Validation Gaps

| Issue | Current State | Impact |
|-------|--------------|--------|
| **Morphology handling** | Exact string match | False negatives on valid insights |
| **Agent compatibility** | Interactive prompts | Blocks automation |
| **Multi-word phrase matching** | Regex exact match | Misses valid variations |

---

## 6. PRIORITIZED FINDINGS

### 🔴 **Critical (Blocks Automation)**

1. **Insight validation blocks agents**
   - Interactive prompt incompatible with GCLI
   - **Fix:** Non-blocking validation (log + retry with feedback)

### 🟡 **High Impact (Accuracy/Efficiency)**

2. **No interconnection reward in completeness formula**
   - Flash not incentivized to map relationships
   - **Fix:** Add dependency density weighting

3. **Validation logic too strict (false negatives)**
   - Morphology not handled ("implemented" fails)
   - **Fix:** Regex patterns for verb stems, or remove validation entirely

### 🟢 **Medium Impact (Quality/Scalability)**

4. **No system priority field**
   - All systems treated equally in synthesis
   - **Fix:** Add `priority` field (critical/important/supplementary)

5. **Coverage threshold fixed at 90%**
   - May be excessive for large projects
   - **Fix:** Dynamic threshold based on project size?

6. **No "verification needed" marker**
   - Flash can't flag uncertain claims
   - **Fix:** Add `verification_needed: true` field to insights/systems

---

## 7. NEXT STEPS

### **Immediate (This Session):**
- Proceed to **Stage 2: Persona Audit**
- Examine System Archaeologist AI agent prompt
- Examine Narrative Architect prompt
- Map where personas can introduce errors

### **Next Session:**
- **Stage 3: Gap Analysis** (compare Stage 1 + 2 findings)
- **Stage 4: Design Phase** (Phase 1.5 Quality Gatekeeper + fixes)

### **Future Session:**
- **Stage 5: Implementation Blueprint** (PHASED_PLAN.md)

---

## SUMMARY

**What Works:**
- ✅ Clean separation of computed vs. manual fields
- ✅ No self-grading vectors in metrics
- ✅ Coverage math fixed (no more 144% bug)
- ✅ File classification robust for PY/TS/JS

**What's Broken:**
- 🔴 Insight validation blocks agent automation
- 🔴 Validation logic has false negatives (morphology)

**What's Missing:**
- ⚠️ No interconnection rewards in completeness
- ⚠️ No system priority field
- ⚠️ No verification status markers
- ⚠️ No file role categorization

**Core Insight:**
The foundation is solid, but the **incentive structure** doesn't reward the behavior we want (deep relationship mapping). The **validation layer** is architecturally incompatible with agent automation.
