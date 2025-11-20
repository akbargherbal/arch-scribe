# Architecture Generator: Cliff Notes for Code

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

This project provides tooling to enable the automated generation of narrative architectural documentation ("Cliff Notes for Code") for any codebase, using a multi-session, human-in-the-loop workflow with Large Language Models (LLMs).

## 1. The Problem

Understanding an unfamiliar open-source project is time-intensive. Cloning a repository often means facing hundreds of files—abstractions built on abstractions, frameworks partially understood, and architectural decisions left undocumented. The goal is not just to know _what_ the code does, but _how_ it works, _why_ it's structured that way, and _what patterns_ matter.

## 2. The Vision: "Cliff Notes for Code"

This system uses LLMs, guided by a human operator, to explore a codebase and generate a comprehensive `ARCHITECTURE.md` document. This isn't an API reference; it's a narrative guide that explains the software's soul.

The process is designed to be like an image rendering in progressively higher detail. Each session with the LLM sharpens the understanding, building a structured knowledge base that is finally synthesized into a clear, human-readable document.

## 3. How It Works: The Tripartite Architecture

The architecture is intentionally simple, powerful, and robust. It is a direct adaptation of the proven "Student Model" project, which separates state, evidence, and logic into three distinct components.

1.  **State Manager (`arch_state.py`)**: A pure Python CLI tool that manages the persistent knowledge base (`architecture.json`). It has **zero LLM integration**.
2.  **Workspace Protocol (The Terminal)**: The human operator uses standard Unix tools (`cat`, `grep`, `tree`, `find`) to provide the LLM with concrete evidence from the codebase. This is the LLM's "eyes and ears."
3.  **Persona Prompts (The LLM)**: A set of Markdown files (`prompts/*.md`) that are pasted into a web-based chat UI (like Claude or ChatGPT). These prompts define the LLM's role, objectives, and the "File Sharing Protocol" it must use to request evidence.

**The human is the integration layer**, copying text between the terminal and the chat window. This design avoids complex API integrations, authentication, and rate-limiting issues, making the tooling incredibly resilient.

## 4. The Two-Phase Workflow

To manage context limits and ensure high-quality output, the process is divided into two distinct phases, each with its own LLM persona.

### Phase 1: The Survey (System Archaeologist 🏛️)

- **Goal:** Explore the codebase and build a structured knowledge base (`architecture.json`).
- **Persona:** The `System Archaeologist` is an explorer. It asks for file listings, searches for patterns, and reads specific files to map out the "systems" that make up the codebase.
- **Output:** A detailed `architecture.json` file, not prose.

### Phase 2: The Synthesis (Narrative Architect ✍️)

- **Goal:** Convert the structured knowledge base into a readable `ARCHITECTURE.md`.
- **Persona:** The `Narrative Architect` is a writer. It consumes the `architecture.json` from Phase 1 and, section by section, writes the final document in the "Cliff Notes" style.
- **Constraint:** This persona does not perform new exploration. It works with the facts gathered in Phase 1.

## 5. Components

This repository contains two key components:

1.  **`arch_state.py`**: The state management CLI.
2.  **`prompts/`**: A directory containing the system prompts for the LLM personas.
    - `system_archaeologist_final.md`: The prompt for Phase 1.
    - `narrative_architect_final.md`: The prompt for Phase 2.

## 6. Workflow: A Step-by-Step Guide

Here is how to use the tooling to document a target repository.

### Prerequisites

- Python 3.8+
- A target codebase you want to document.
- Access to a powerful LLM via a web chat interface (e.g., Claude 3.5 Sonnet, GPT-4o).

### Setup

1.  Clone this repository.
2.  Navigate to your target codebase in your terminal.
3.  Run the initialization command from the `arch-generator` directory:
    ```bash
    python /path/to/arch_state.py init "My Project Name"
    ```
    This creates the `architecture.json` file in your target repo's root.

### Phase 1: The Survey

1.  **Start a Session:** Open your LLM chat interface. Copy the entire contents of `prompts/system_archaeologist_final.md` and paste it as the first message.
2.  **Begin the Loop:** The LLM will now guide you. It will ask you to run commands and paste the output.
    - **LLM:** "I am ready to begin. Please run `python arch_state.py status` and `cat README.md`."
    - **You:** Run the commands in your terminal, copy the output, and paste it back into the chat.
    - **LLM:** "Thank you. I see this is a Django project. To understand the structure, please run `tree -L 2`."
    - **You:** Run `tree -L 2`, copy, and paste.
    - **LLM:** "I've identified an authentication system in `src/auth`. Please run these commands to update our map:"
      ```bash
      python arch_state.py add "Auth System"
      python arch_state.py map "Auth System" src/auth/login.py src/auth/utils.py
      python arch_state.py update "Auth System" --desc "Handles JWT login flow" --comp 20
      ```
    - **You:** Copy the command block and run it in your terminal.
3.  **Continue:** Repeat this loop. The LLM will explore the codebase through you, building up the `architecture.json` file.
4.  **End Phase 1:** The `status` command will tell you when you've met the completion criteria (e.g., >90% file coverage). At this point, run `python arch_state.py validate` to check for errors and proceed to Phase 2.

### Phase 2: The Synthesis

1.  **Start a New Chat:** Open a fresh chat session with your LLM. This is crucial to switch personas.
2.  **Load the Persona:** Copy the entire contents of `prompts/narrative_architect_final.md` and paste it.
3.  **Provide Context:** The LLM will ask for the `architecture.json` data.
    - **LLM:** "I am ready to synthesize. Please paste the output of `python arch_state.py list` and `python arch_state.py status`."
    - **You:** Run the commands and paste the output.
    - **LLM:** "Thank you. Now, please paste the full contents of `architecture.json`."
    - **You:** Run `cat architecture.json`, copy, and paste.
4.  **Write the Document:** The LLM will first propose a Table of Contents. Once you approve it, it will write the `ARCHITECTURE.md` document section by section, asking you to copy-paste each part into your local file.

## 7. CLI Reference (`arch_state.py`)

The state manager provides a rich set of commands for inspecting and manipulating the `architecture.json` file.

| Command                                 | Description                                               |
| --------------------------------------- | --------------------------------------------------------- |
| `init <name>`                           | Initializes a new `architecture.json` file.               |
| `status`                                | Shows high-level project status and coverage metrics.     |
| `list`                                  | Lists all identified systems and their completeness.      |
| `show <name>`                           | Pretty-prints the JSON data for a specific system.        |
| `validate`                              | Checks for data integrity issues before Phase 2.          |
| `graph`                                 | Exports a Mermaid.js dependency graph of all systems.     |
| `coverage`                              | Shows a detailed breakdown of file coverage by directory. |
| `session-start`                         | Marks the beginning of an exploration session.            |
| `session-end`                           | Records session activity and checks for completion.       |
| `add <name>`                            | Adds a new, empty system to the state.                    |
| `map <name> <files...>`                 | Maps one or more files to a system.                       |
| `update <name> --desc/--comp/--clarity` | Updates a system's metadata.                              |
| `insight <name> <text>`                 | Adds a key insight to a system.                           |
| `dep <name> <target> <reason>`          | Creates a dependency link between systems.                |

## 8. Design Philosophy

- **Simplicity Over Power**: The core tooling is a single Python script with no external dependencies beyond the standard library. No API keys, no complex setup.
- **Human as the Integration Layer**: The most flexible and powerful "API" is a human who can think, copy, and paste. This avoids brittle integrations and vendor lock-in.
- **Protocol via Prompting**: The "File Sharing Protocol" is not code; it's a set of plain-text instructions in the system prompt that teaches the LLM how to ask for the data it needs.
- **Evidence-Based Analysis**: The LLM is forbidden from hallucinating file contents. It must request explicit evidence for every claim it makes about the code.
