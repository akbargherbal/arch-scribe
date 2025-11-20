# Architecture Documentation Generator

**Cliff Notes for Code** — Automatically generate comprehensive `ARCHITECTURE.md` documentation for any codebase using LLM-guided exploration and synthesis.

---

## The Problem

Have you ever cloned an unfamiliar open-source project and faced hundreds of files—abstractions built on abstractions, frameworks you're only partially familiar with, architectural decisions that aren't documented anywhere? Complex codebases are like dense literary works: they need an interpretive layer to make them understandable.

Some books can't be read without Cliff Notes. The same is true for code.

## The Solution

This project uses LLMs combined with structured multi-session workflows to create comprehensive architectural documentation for any codebase. Instead of overwhelming the LLM with thousands of files at once, it explores the project incrementally across multiple sessions, building a structured knowledge base that's then synthesized into clear, narrative documentation.

Think of it as **progressive rendering for documentation**—starting pixelated and gradually becoming crystal clear.

---

## How It Works

### Two-Phase Architecture

#### **Phase 1: Survey & Exploration** (Sessions 1-N)

The LLM acts as a **System Archaeologist**, exploring the codebase to discover and document architectural systems:

- Identifies major systems (Authentication, Data Layer, API, etc.)
- Maps key files to each system
- Records insights about design patterns and decisions
- Notes complexities and technical debt
- Tracks system dependencies and integration points

**Output:** `architecture.json` — a structured knowledge base of architectural systems

#### **Phase 2: Synthesis & Writing** (Sessions N+1 onwards)

The LLM becomes a **Narrative Architect**, writing `ARCHITECTURE.md` section by section:

- Transforms structured notes into narrative prose
- Explains the "why" behind design decisions
- Uses a "Cliff Notes" style: clear, educational, narrative-driven
- Focuses on understanding over completeness

**Output:** `ARCHITECTURE.md` — comprehensive architectural documentation

### Why This Approach?

- ✅ **Eliminates context overflow:** LLM explores incrementally, not all at once
- ✅ **Prevents contradictions:** Phase 1 completes before Phase 2 begins
- ✅ **Separates concerns:** Discovery vs. synthesis are different mental modes
- ✅ **Session-friendly:** Natural checkpoint at phase transition
- ✅ **Quality-focused:** Structured exploration produces better synthesis material

---

## Getting Started

### Prerequisites

- Python 3.8+
- Access to an LLM with file access capabilities (Claude, GPT-4, etc.)
- Terminal/command-line access

### Installation

1. **Clone this repository:**

```bash
git clone https://github.com/yourusername/arch-doc-generator.git
cd arch-doc-generator
```

2. **Make `arch_state` globally accessible:**

**Linux/macOS (Bash/Zsh):**

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="/path/to/arch-doc-generator:$PATH"

# Make executable
chmod +x arch_state.py
```

**Windows (PowerShell):**

```powershell
# Add to PowerShell profile
$env:Path += ";C:\path\to\arch-doc-generator"
```

3. **Verify installation:**

```bash
arch_state --help
```

### Usage

#### Step 1: Initialize Your Project

Navigate to the codebase you want to document:

```bash
cd /path/to/your-project
arch_state init "Your Project Name"
```

This creates `architecture.json` with project metadata.

#### Step 2: Phase 1 — Exploration

Start an exploration session with your LLM, using the **System Archaeologist** persona (see `system_archaeologist.md`).

**Session workflow:**

```bash
# Start session tracking
arch_state session-start

# LLM explores the codebase and guides you to run commands like:
arch_state add "Authentication System"
arch_state map "Authentication System" src/auth/login.py src/auth/middleware.py
arch_state insight "Authentication System" "Uses decorator pattern for route protection..."
arch_state dep "Authentication System" "Core Infrastructure" "Uses Redis cache for tokens"

# Check progress
arch_state status
arch_state coverage

# End session
arch_state session-end
```

**Continue sessions until Phase 1 stopping criteria met:**

- **Gate A:** Coverage ≥ 90% of significant files
- **Gate B:** 3 consecutive low-yield sessions (tracked automatically)

#### Step 3: Validation

Before moving to Phase 2:

```bash
arch_state validate
```

Fix any errors reported (missing descriptions, invalid dependencies, etc.).

#### Step 4: Phase 2 — Synthesis

Switch to the **Narrative Architect** persona (see `narrative_architect.md`).

**Session workflow:**

```bash
# Get overview
arch_state list
arch_state status

# View system details for writing
arch_state show "Authentication System"
arch_state show "Authentication System" --summary

# Generate dependency diagram
arch_state graph

# Write ARCHITECTURE.md section by section using the system data
```

The LLM writes narrative prose based on the structured knowledge from Phase 1.

---

## CLI Reference

### Session Management

```bash
arch_state session-start        # Begin session tracking
arch_state session-end          # Record session metrics
```

### System Management

```bash
arch_state add "System Name"                    # Create new system
arch_state map "System Name" file1.py file2.py  # Map files to system
arch_state update "System Name" --desc "..." --comp 75  # Update metadata
arch_state insight "System Name" "Insight text..."      # Add architectural insight
arch_state dep "System Name" "Target" "Reason"          # Add dependency
```

### Inspection

```bash
arch_state status              # Overall project state & progress
arch_state list                # List all systems with completeness
arch_state show "System Name"  # View system details (full)
arch_state show "System Name" --summary  # Condensed view
arch_state coverage            # Directory-level coverage analysis
arch_state graph               # Generate Mermaid dependency diagram
arch_state validate            # Check for data quality issues
```

---

## State File Structure

The `architecture.json` file uses a system-centric schema:

```json
{
  "schema_version": "2.2",
  "metadata": {
    "project_name": "Your Project",
    "project_type": "Django Web Application",
    "last_updated": "2025-11-20T10:30:00",
    "phase": "survey",
    "total_sessions": 5,
    "scan_stats": {
      "coverage_percentage": 87.5,
      "coverage_quality": 92.3
    }
  },
  "systems": {
    "Authentication System": {
      "description": "Handles user authentication using JWT tokens",
      "completeness": 85,
      "clarity": "high",
      "key_files": ["src/auth/login.py", "src/auth/middleware.py"],
      "insights": [
        "Uses decorator pattern for declarative route protection",
        "Token refresh integrates with Redis cache to reduce DB load"
      ],
      "complexities": [
        "Middleware execution order isn't enforced programmatically"
      ],
      "dependencies": [
        {
          "system": "Core Infrastructure",
          "reason": "Uses Redis for token caching"
        }
      ]
    }
  }
}
```

---

## LLM Personas

This project includes two specialized LLM personas:

### Phase 1: System Archaeologist

**Role:** Explore the codebase and build structured knowledge

**Key behaviors:**

- Breadth-first discovery (identify all systems before deep-diving)
- Evidence-based analysis (never guesses file contents)
- Structured note-taking (insights follow "[WHAT] using [HOW], which [WHY]" template)
- Session discipline (always runs `session-start` and `session-end`)

📄 Full persona: `system_archaeologist.md`

### Phase 2: Narrative Architect

**Role:** Synthesize structured knowledge into narrative documentation

**Key behaviors:**

- "Cliff Notes" writing style (explain WHY, not just WHAT)
- Narrative flow (systems as characters in a story)
- Plain language (define jargon, avoid walls of code)
- Progressive disclosure (high-level → detailed)

📄 Full persona: `narrative_architect.md`

---

## Design Philosophy

### System-Centric Thinking

Documentation is organized around **systems** (cohesive groups of 2-10 files providing a major capability), not files or directories.

**Good system names:**

- ✅ Authentication System
- ✅ Data Persistence Layer
- ✅ Background Task Queue

**Bad system names:**

- ❌ Backend / Frontend (too broad)
- ❌ JWT Token Generation (too narrow—this is a component)
- ❌ Controllers / Models (architectural layers, not capabilities)

### Note Quality Standards

Every insight must follow the template: **[WHAT] using [HOW], which [WHY/IMPACT]**

**Good example:**

> "Implements token refresh using Redis cache with sliding window TTL, which reduces database load during high-traffic periods by 60%"

**Bad example:**

> "Handles authentication stuff"

### Stopping Criteria: Two-Gate Algorithm

Phase 1 ends when **either** condition is met:

- **Gate A:** Coverage ≥ 90% of significant files
- **Gate B:** 3 consecutive low-yield sessions (<1 new system, <3 new files each)

This prevents both premature completion and diminishing returns.

---

## Project Origin

This project started from a personal frustration: understanding complex open-source codebases I didn't write. Some works of literature can't be read without Cliff Notes—not because readers are lazy, but because the layers of abstraction are too dense to parse on first reading. Code is the same way.

The breakthrough was recognizing that this couldn't be a single-session task. By splitting exploration (Phase 1) from synthesis (Phase 2), and using structured state management (`architecture.json`) as the handoff mechanism, we can build comprehensive documentation incrementally without overwhelming LLM context windows.

This is an **educational tool**—designed to make complex codebases learnable in a fraction of the time it would take to read them file by file.

---

## Advanced Usage

### Coverage Analysis

The `coverage` command shows directory-level mapping statistics:

```bash
arch_state coverage
```

**Output:**

```
=== 📊 COVERAGE BY DIRECTORY ===
✅ src/auth                [██████████] 100% (8/8)
⚠️  src/api                [██████░░░░]  60% (12/20)
❌ src/background          [██░░░░░░░░]  20% (2/10)

=== 📄 TOP UNMAPPED FILES ===
  1. src/background/celery_config.py     (15.2 KB)
  2. src/api/serializers.py              (12.8 KB)
```

Use this to identify exploration gaps.

### Dependency Visualization

Generate a Mermaid diagram of system dependencies:

```bash
arch_state graph
```

**Output:**

```mermaid
graph TD
  Auth_System["Authentication System"]
  Core_Infrastructure["Core Infrastructure"]
  Data_Layer["Data Layer"]

  Auth_System -->|Uses Redis for tokens| Core_Infrastructure
  Auth_System -->|Stores user credentials| Data_Layer
```

Paste this into `ARCHITECTURE.md` for visual system relationships.

### Session History

View exploration trajectory:

```bash
arch_state status
```

Shows:

- Total sessions run
- Systems identified per session
- Files mapped per session
- Insights added per session
- Gate A/B status

---

## Contributing

Contributions welcome! This is an experimental project focused on LLM-guided documentation workflows.

**Areas of interest:**

- Improved heuristics for system discovery
- Project type detection and templates
- Note quality validation
- Phase transition optimization

**To contribute:**

1. Fork the repository
2. Create a feature branch
3. Make your changes with clear commit messages
4. Submit a pull request

---

## License

MIT License

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Acknowledgments

- Inspired by the challenge of understanding complex open-source projects
- Built on experience with 30+ session multi-turn LLM workflows
- Architecture adapted from proven `student.py` state management pattern
- Special thanks to the concept of "Cliff Notes for code"—documentation should educate, not just enumerate

---

## Roadmap

- [ ] Automated project type detection improvements
- [ ] Template-based Phase 2 section generation
- [ ] Git integration for tracking documentation drift
- [ ] Web UI for `architecture.json` visualization
- [ ] Export formats (Markdown, HTML, PDF)
- [ ] Integration with documentation hosting platforms

---

**Questions? Issues? Feedback?**

Open an issue on GitHub or start a discussion. This is an experimental educational project—collaboration and ideas are welcome!
