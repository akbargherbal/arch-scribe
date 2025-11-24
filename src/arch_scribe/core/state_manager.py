import json
import os
import sys
import shutil
import datetime
import re
import copy
from collections import defaultdict

# Core imports
from .constants import (
    STATE_FILE, BACKUP_FILE, SESSION_FILE, Colors, DEFAULT_STATE
)
# Config imports
from ..config.insight_quality import ACTION_VERBS, IMPACT_WORDS, MIN_WORD_COUNT

# New modular imports
from ..scanning.file_scanner import FileScanner
from ..metrics.coverage import calculate_coverage_quality
from ..metrics.clarity import compute_clarity
from ..metrics.completeness import compute_completeness


class StateManager:
    def __init__(self):
        self.data = self.load_state()
        self.scanner = FileScanner()
        self.session_start_state = None

    def load_state(self):
        if not os.path.exists(STATE_FILE):
            return None
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"{Colors.FAIL}❌ Error: {STATE_FILE} is corrupted.{Colors.ENDC}")
            if os.path.exists(BACKUP_FILE):
                print(f"{Colors.WARNING}⚠️  Restoring from backup...{Colors.ENDC}")
                with open(BACKUP_FILE, "r") as f:
                    return json.load(f)
            sys.exit(1)

    def save_state(self):
        if not self.data:
            return
        self.data["metadata"]["last_updated"] = datetime.datetime.now().isoformat()

        # Atomic Write Pattern
        if os.path.exists(STATE_FILE):
            shutil.copy(STATE_FILE, BACKUP_FILE)
        temp = STATE_FILE + ".tmp"
        with open(temp, "w") as f:
            json.dump(self.data, f, indent=2)
        os.replace(temp, STATE_FILE)
        print(f"{Colors.GREEN}💾 State saved.{Colors.ENDC}")

    def init_project(self, name):
        if os.path.exists(STATE_FILE):
            if input(f"Overwrite {STATE_FILE}? (y/N): ").lower() != "y":
                return

        self.data = copy.deepcopy(DEFAULT_STATE)

        self.data["metadata"]["project_name"] = name
        self.data["metadata"]["project_type"] = self.detect_project_type()
        self.save_state()
        print(f"{Colors.BLUE}🚀 Initialized project: {name}{Colors.ENDC}")
        print(
            f"{Colors.BLUE}   Detected type: {self.data['metadata']['project_type']}{Colors.ENDC}"
        )

    def detect_project_type(self):
        """Infer project type from file signatures"""
        if os.path.exists("manage.py") or os.path.exists("wsgi.py"):
            return "Django Web Application"
        if os.path.exists("app.py") and os.path.exists("requirements.txt"):
            return "Flask Web Application"
        if os.path.exists("package.json"):
            with open("package.json") as f:
                try:
                    pkg = json.load(f)
                    if "express" in pkg.get("dependencies", {}):
                        return "Node.js/Express Application"
                except:
                    pass
            return "Node.js Application"
        if os.path.exists("Cargo.toml"):
            return "Rust Project"
        if os.path.exists("go.mod"):
            return "Go Project"
        if os.path.exists("setup.py") or os.path.exists("pyproject.toml"):
            return "Python Package/Library"
        if os.path.exists("Dockerfile"):
            return "Containerized Application"
        return "Unknown"

    # --- METRICS & SCANNING ---
    def update_stats(self):
        if not self.data:
            return
        
        # Delegate to scanner
        total, sig_total, sig_paths = self.scanner.scan_files()

        mapped = set()
        systems = self.data.get("systems", {})
        for s in systems.values():
            mapped.update(s.get("key_files", []))

        mapped_sig = len(sig_paths.intersection(mapped))
        cov = (mapped_sig / sig_total * 100) if sig_total > 0 else 0.0
        
        # Delegate to metrics
        quality = calculate_coverage_quality(sig_paths, mapped)

        stats = self.data["metadata"]["scan_stats"]
        stats.update(
            {
                "total_files_scanned": total,
                "significant_files_total": sig_total,
                "mapped_files_count": mapped_sig,
                "coverage_percentage": round(cov, 1),
                "coverage_quality": quality,
            }
        )

        prog = self.data["progress"]
        prog["systems_identified"] = len(systems)
        prog["systems_complete"] = len(
            [s for s in systems.values() if s.get("completeness", 0) >= 85]
        )
        if systems:
            prog["estimated_overall_completeness"] = round(
                sum(s.get("completeness", 0) for s in systems.values()) / len(systems),
                1,
            )
        self.save_state()

    # --- SESSION TRACKING ---
    def start_session(self):
        """Mark the beginning of a new session"""
        if not self.data:
            return

        with open(SESSION_FILE, "w") as f:
            json.dump(self.data, f)

        self.session_start_state = copy.deepcopy(self.data)
        self.data["metadata"]["total_sessions"] += 1
        self.save_state()
        print(
            f"{Colors.BLUE}📍 Session {self.data['metadata']['total_sessions']} started{Colors.ENDC}"
        )

    def end_session(self):
        """Record what happened in this session"""
        if not self.data:
            return

        if self.session_start_state is None and os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    self.session_start_state = json.load(f)
            except json.JSONDecodeError:
                pass

        if not self.session_start_state:
            print(
                f"{Colors.WARNING}⚠️  No active session found (run session-start first).{Colors.ENDC}"
            )
            return

        old_systems = set(self.session_start_state.get("systems", {}).keys())
        new_systems = set(self.data["systems"].keys())
        systems_added = len(new_systems - old_systems)

        old_files = set()
        for s in self.session_start_state.get("systems", {}).values():
            old_files.update(s.get("key_files", []))

        new_files = set()
        for s in self.data["systems"].values():
            new_files.update(s.get("key_files", []))

        files_mapped = len(new_files - old_files)

        old_insights = sum(
            len(s.get("insights", []))
            for s in self.session_start_state.get("systems", {}).values()
        )
        new_insights = sum(
            len(s.get("insights", [])) for s in self.data["systems"].values()
        )
        insights_added = new_insights - old_insights

        session_id = self.data["metadata"]["total_sessions"]
        self.data["metadata"]["session_history"].append(
            {
                "session_id": session_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "new_systems_found": systems_added,
                "new_files_mapped": files_mapped,
                "insights_added": insights_added,
            }
        )

        self.save_state()

        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

        print(f"{Colors.GREEN}✅ Session {session_id} recorded:{Colors.ENDC}")
        print(f"   Systems added: {systems_added}")
        print(f"   Files mapped: {files_mapped}")
        print(f"   Insights added: {insights_added}")

    # --- MODIFICATION COMMANDS ---
    def add_system(self, name):
        if not self.data:
            return
        if name in self.data["systems"]:
            print(f"{Colors.WARNING}⚠️  System '{name}' already exists.{Colors.ENDC}")
            return
        self.data["systems"][name] = {
            "description": "TODO",
            "completeness": 0,
            "clarity": "low",
            "key_files": [],
            "dependencies": [],
            "insights": [],
            "complexities": [],
        }
        print(f"{Colors.GREEN}✅ Added system: {name}{Colors.ENDC}")
        self.save_state()

    def update_system(self, name, desc=None):
        if name not in self.data["systems"]:
            print(f"{Colors.FAIL}❌ System '{name}' not found.{Colors.ENDC}")
            return

        sys = self.data["systems"][name]

        if desc:
            if "\n" in desc:
                print(
                    f"{Colors.FAIL}❌ Description cannot contain newlines. Use single-line descriptions.{Colors.ENDC}"
                )
                return
            sys["description"] = desc

        # Delegate to metrics
        sys["clarity"] = compute_clarity(sys)
        sys["completeness"] = compute_completeness(sys)

        print(f"{Colors.GREEN}✅ Updated metadata for: {name}{Colors.ENDC}")
        self.save_state()

    def map_files(self, name, files):
        if name not in self.data["systems"]:
            print(f"{Colors.FAIL}❌ System '{name}' not found.{Colors.ENDC}")
            return

        sys = self.data["systems"][name]
        sys["key_files"].extend(files)
        sys["key_files"] = list(set(sys["key_files"]))

        # Delegate to metrics
        sys["clarity"] = compute_clarity(sys)
        sys["completeness"] = compute_completeness(sys)

        print(f"{Colors.GREEN}✅ Mapped {len(files)} files to: {name}{Colors.ENDC}")
        self.update_stats()

    def similar_text(self, a, b, threshold=0.8):
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return False
        overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
        return overlap > threshold

    def add_insight(self, name, text, force=False):
        if name not in self.data["systems"]:
            return

        if not force:
            errors = self.validate_insight_quality(text)
            if errors:
                print(f"{Colors.WARNING}⚠️  Insight quality issues:{Colors.ENDC}")
                for e in errors:
                    print(f"   • {e}")

                print(
                    f"\n{Colors.BLUE}Quality template: [WHAT] using [HOW], which [WHY/IMPACT]{Colors.ENDC}"
                )
                print(
                    f"{Colors.BLUE}Example: 'Implements token refresh using Redis cache, which reduces DB load'{Colors.ENDC}"
                )

                response = input(f"\n{Colors.WARNING}Add anyway? (y/N): {Colors.ENDC}")
                if response.lower() != "y":
                    print(
                        f"{Colors.FAIL}❌ Insight rejected. Please rewrite.{Colors.ENDC}"
                    )
                    return
                else:
                    print(
                        f"{Colors.WARNING}⚠️  Added with quality issues (consider revising later){Colors.ENDC}"
                    )

        existing = self.data["systems"][name]["insights"]
        if any(self.similar_text(text, e) for e in existing):
            print(
                f"{Colors.WARNING}⚠️  Similar insight already exists. Skipping.{Colors.ENDC}"
            )
            return

        existing.append(text)

        sys = self.data["systems"][name]
        # Delegate to metrics
        sys["clarity"] = compute_clarity(sys)
        sys["completeness"] = compute_completeness(sys)

        print(f"{Colors.GREEN}✅ Added insight to: {name}{Colors.ENDC}")
        self.save_state()

    def add_dependency(self, name, target, reason):
        if name not in self.data["systems"]:
            print(f"{Colors.FAIL}❌ System '{name}' not found.{Colors.ENDC}")
            return

        if target not in self.data["systems"]:
            print(
                f"{Colors.WARNING}⚠️  Target system '{target}' doesn't exist yet.{Colors.ENDC}"
            )
            if input("Create it now? (y/N): ").lower() == "y":
                self.add_system(target)
            else:
                return

        sys = self.data["systems"][name]
        sys["dependencies"].append({"system": target, "reason": reason})

        # Delegate to metrics
        sys["clarity"] = compute_clarity(sys)
        sys["completeness"] = compute_completeness(sys)

        print(f"{Colors.GREEN}✅ Linked {name} -> {target}{Colors.ENDC}")
        self.save_state()

    def validate_schema(self):
        if not self.data:
            return []

        errors = []
        systems = self.data.get("systems", {})

        for name, sys in systems.items():
            if not sys.get("description") or sys["description"] == "TODO":
                errors.append(f"{name}: Missing or placeholder description")
            if not sys.get("key_files"):
                errors.append(f"{name}: No key_files listed")
            if not sys.get("insights"):
                errors.append(f"{name}: No insights recorded")

            insight_count = len(sys.get("insights", []))
            completeness = sys.get("completeness", 0)

            if completeness >= 50 and insight_count < 3:
                errors.append(
                    f"{name}: {completeness}% complete but only {insight_count} insights "
                    f"(need 3+ for 50%+ completeness)"
                )

            if completeness >= 80 and insight_count < 5:
                errors.append(
                    f"{name}: {completeness}% complete but only {insight_count} insights "
                    f"(need 5+ for 80%+ completeness)"
                )

        for name, sys in systems.items():
            for dep in sys.get("dependencies", []):
                if dep["system"] not in systems:
                    errors.append(
                        f"{name}: References non-existent system '{dep['system']}'"
                    )

        # Delegate to scanner
        total, sig_total, sig_paths = self.scanner.scan_files()
        mapped = set()
        for sys in systems.values():
            mapped.update(sys["key_files"])

        orphans = sig_paths - mapped
        core_orphans = [
            f
            for f in orphans
            if not any(x in f.lower() for x in ["test", "doc", "example", "spec"])
        ]

        if core_orphans and len(core_orphans) > 5:
            errors.append(
                f"Found {len(core_orphans)} unmapped significant files (sample: {list(core_orphans)[:5]})"
            )

        return errors

    # --- REPORTING ---
    def print_status(self):
        self.update_stats()
        meta = self.data["metadata"]
        stats = meta["scan_stats"]
        cov_color = (
            Colors.GREEN if stats["coverage_percentage"] >= 90 else Colors.WARNING
        )

        print(f"\n{Colors.HEADER}=== 🏛️  PROJECT STATE ==={Colors.ENDC}")
        print(
            f"Project:  {Colors.BOLD}{meta.get('project_name')}{Colors.ENDC} ({meta.get('project_type', 'Unknown')})"
        )
        print(f"Phase:    {meta.get('phase', 'survey')}")
        print(f"Sessions: {meta.get('total_sessions', 0)}")
        print(
            f"Coverage: {cov_color}{stats['coverage_percentage']}%{Colors.ENDC} ({stats['mapped_files_count']}/{stats['significant_files_total']} significant files)"
        )
        print(f"Quality:  {stats['coverage_quality']}% (excluding tests/docs)")
        print(
            f"Systems:  {self.data['progress']['systems_identified']} identified, {self.data['progress']['systems_complete']} complete"
        )

        if stats["coverage_percentage"] >= 90:
            print(
                f"\n{Colors.GREEN}🎯 Gate A: Coverage threshold met (90%+){Colors.ENDC}"
            )

        if len(meta.get("session_history", [])) >= 3:
            last_3 = meta["session_history"][-3:]
            if all(
                s["new_systems_found"] == 0 and s["new_files_mapped"] < 3
                for s in last_3
            ):
                print(
                    f"\n{Colors.GREEN}🎯 Gate B: Diminishing returns detected (3 low-yield sessions){Colors.ENDC}"
                )

    def list_systems(self):
        print(f"\n{Colors.HEADER}=== 🗺️  SYSTEMS ==={Colors.ENDC}")
        for name, s in sorted(
            self.data["systems"].items(),
            key=lambda x: x[1]["completeness"],
            reverse=True,
        ):
            print(
                f"{name:<30} | {s['completeness']:>3}% | {len(s['key_files']):>2} files | {len(s['insights']):>2} insights"
            )

    def show_system(self, name, summary=False):
        if name not in self.data["systems"]:
            print(f"{Colors.FAIL}System not found.{Colors.ENDC}")
            return

        sys = self.data["systems"][name]

        if summary:
            output = {
                "description": sys["description"],
                "completeness": sys["completeness"],
                "dependencies": [d["system"] for d in sys.get("dependencies", [])],
                "top_insights": sys.get("insights", [])[:3],
            }
            print(json.dumps(output, indent=2))
        else:
            print(json.dumps(sys, indent=2))

    def sanitize_for_mermaid(self, name):
        return re.sub(r"[^\w]", "_", name)

    def export_graph(self):
        print(f"\n{Colors.HEADER}=== 🕸️  DEPENDENCY GRAPH (Mermaid) ==={Colors.ENDC}")
        print("```mermaid")
        print("graph TD")

        for name in self.data["systems"].keys():
            safe_name = self.sanitize_for_mermaid(name)
            print(f'  {safe_name}["{name}"]')

        for name, s in self.data["systems"].items():
            source = self.sanitize_for_mermaid(name)
            for dep in s.get("dependencies", []):
                target = self.sanitize_for_mermaid(dep["system"])
                reason = (
                    (dep["reason"][:30] + "..")
                    if len(dep["reason"]) > 30
                    else dep["reason"]
                )
                print(f"  {source} -->|{reason}| {target}")
        print("```")

    def print_coverage_detail(self):
        if not self.data:
            return

        # Delegate to scanner
        total, sig_total, sig_paths = self.scanner.scan_files()
        mapped = set()
        for s in self.data["systems"].values():
            mapped.update(s["key_files"])

        dir_stats = defaultdict(lambda: {"total": 0, "mapped": 0, "files": []})

        for path in sig_paths:
            dir_name = os.path.dirname(path) or "."
            dir_stats[dir_name]["total"] += 1
            if path in mapped:
                dir_stats[dir_name]["mapped"] += 1
            else:
                dir_stats[dir_name]["files"].append(path)

        print(f"\n{Colors.HEADER}=== 📊 COVERAGE BY DIRECTORY ==={Colors.ENDC}")
        for dir_name in sorted(dir_stats.keys()):
            stat = dir_stats[dir_name]
            pct = (stat["mapped"] / stat["total"] * 100) if stat["total"] > 0 else 0
            bar_filled = int(pct / 10)
            bar = "█" * bar_filled + "░" * (10 - bar_filled)

            if pct >= 90:
                icon = "✅"
            elif pct >= 60:
                icon = "⚠️ "
            else:
                icon = "❌"

            print(
                f"{icon} {dir_name:<30} [{bar}] {pct:>3.0f}% ({stat['mapped']}/{stat['total']})"
            )

        all_unmapped = []
        for stat in dir_stats.values():
            all_unmapped.extend(stat["files"])

        if all_unmapped:
            print(f"\n{Colors.HEADER}=== 📄 TOP UNMAPPED FILES ==={Colors.ENDC}")
            unmapped_with_size = []
            for f in all_unmapped[:20]:
                try:
                    size = os.path.getsize(f)
                    unmapped_with_size.append((f, size))
                except OSError:
                    pass

            unmapped_with_size.sort(key=lambda x: x[1], reverse=True)
            for i, (f, size) in enumerate(unmapped_with_size[:10], 1):
                kb = size / 1024
                print(f"  {i}. {f:<50} ({kb:.1f} KB)")

    def validate_insight_quality(self, text):
        errors = []
        words = text.split()

        if len(words) < MIN_WORD_COUNT:
            errors.append(f"Too short ({len(words)} words, need 15+)")

        action_verbs = ACTION_VERBS
        has_action = any(verb in text.lower() for verb in action_verbs)
        if not has_action:
            errors.append("Missing [WHAT] - no clear action verb found")

        impact_words = IMPACT_WORDS
        text_lower = text.lower()
        has_impact = any(
            re.search(r"\b" + re.escape(word) + r"\b", text_lower)
            for word in impact_words
        )
        if not has_impact:
            errors.append("Missing [WHY/IMPACT] - no consequence or benefit stated")

        return errors