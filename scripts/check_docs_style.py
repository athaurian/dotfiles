#!/usr/bin/env python3
"""Style-guide checks for docs and inline documentation.

Covers the ratified patterns from style-guide.md as errors, and the
team punctuation bans (semicolons, em/en dashes, label-then-colon) plus
a docstring-voice heuristic as warnings. First-person voice ('my', 'I')
is never flagged, by explicit team choice. See the Enforcement section
in style-guide.md for the rule-to-check mapping.

Usage: python3 scripts/check_docs_style.py [--strict]

Exit status is 1 when any error is found, or when --strict is given and
any warning is found. Warnings are advisory: fix them when the flag is
a true positive.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD_FILES = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]

CODE_FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
TABLE_ROW = re.compile(r"^\s*\|")
# A code span, then +, then another code span, with whitespace on at least
# one side of the plus. The joined Control+C style has no spaces, and the
# backtick-key form (`Super`+`` ` ``) has none either, so neither matches.
KEY_SPACED = re.compile(r"`[^`\n]+`(?:\s+\+\s*`|\s*\+\s+`)")
CODE_IN_HEADING = re.compile(r"`[^`]+`")
ING_HEADING = re.compile(r"^#{1,6}\s+([A-Za-z]+ing)\b")
YES_NO_CODE = re.compile(r"`(yes|no)`")
URL = re.compile(r"https?://")
EM_DASH = re.compile(r"[—–]")
SPACED_DOUBLE_HYPHEN = re.compile(r"\S -- \S")
INLINE_CODE = re.compile(r"`[^`\n]*`")
# A short leading label ending in a colon, followed by a capital letter,
# a quote, or code. Catches 'Overview: this module ...' style sentences.
LABEL_COLON = re.compile(r"^[#>\-*\d.\s]*[A-Z][A-Za-z0-9 ,/'-]{1,40}: [A-Z\"`]")
NOTICE_LABEL = re.compile(r"^\s*(Note|Caution|Warning):")
DOC_SECTION = re.compile(r"^\s*(Args|Returns|Raises|Note|Caution|Warning):")
# Schematic comment headers are reference entries, not prose sentences:
# case/action labels, caller metadata, numbered scenario titles, and
# function signature headers. The guide exempts them from the
# label-then-colon and em/en dash bans.
SCHEMATIC_HEADER = re.compile(r"^(Case [A-Z]|Action|Called by|\d+\.\s+[A-Z][A-Za-z ]*):")
SIG_HEADER = re.compile(r"^[a-z_]+(\s+[A-Z_]+)+ — ")

# Bare imperative verb forms that must not open a docstring first line.
# Third-person forms (Renders, Exports, Checks, ...) pass.
IMPERATIVES = (
    "Render", "Export", "Return", "Convert", "Run", "Check", "Parse",
    "Match", "Take", "Consume", "Extract", "Warn", "Build", "Create",
    "Provide", "Define", "Detect", "Orchestrate", "Compute", "Load",
    "Save", "Restore", "Show", "Perform", "Clamp", "Report", "List",
    "Copy", "Decode", "Split", "Collapse", "Format", "Launch", "Toggle",
    "Write", "Read", "Send", "Delete", "Update", "Remove", "Add", "Map",
)
IMPERATIVE_LEAD = re.compile(r"^(" + "|".join(IMPERATIVES) + r")\b(?!s\b)")

MAX_WIDTH = 80

errors: list[str] = []
warnings: list[str] = []


def err(path: Path, line: int, code: str, text: str) -> None:
    errors.append(f"{path}:{line}: [{code}] {text}")


def warn(path: Path, line: int, code: str, text: str) -> None:
    warnings.append(f"{path}:{line}: [{code}] {text}")


def check_markdown(path: Path) -> None:
    rel = path.relative_to(ROOT)
    in_fence = False
    for i, raw in enumerate(path.read_text().splitlines(), 1):
        line = raw.rstrip("\n")
        if CODE_FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        heading = HEADING.match(stripped)
        if heading:
            title = heading.group(2)
            if CODE_IN_HEADING.search(title):
                err(rel, i, "E4", "code item in heading, move it to the body")
            ing = ING_HEADING.match(stripped)
            if ing:
                err(rel, i, "E5", f"heading starts with -ing form {ing.group(1)!r}")
            continue
        if KEY_SPACED.search(line):
            err(rel, i, "E2", "spaced key combo, use Control+C style")
        if YES_NO_CODE.search(line):
            err(rel, i, "E3", "menu option in code font, use bold")
        if TABLE_ROW.match(line):
            continue
        if not stripped:
            continue
        if len(line) > MAX_WIDTH and not URL.search(line):
            err(rel, i, "E1", f"prose line is {len(line)} chars, wrap at 80")
        bare = INLINE_CODE.sub("", line)
        if ";" in bare:
            warn(rel, i, "W1", "semicolon in prose, split into sentences")
        if EM_DASH.search(bare) or SPACED_DOUBLE_HYPHEN.search(bare):
            warn(rel, i, "W2", "em/en dash in prose, rewrite the sentence")
        if LABEL_COLON.match(line) and not NOTICE_LABEL.match(stripped):
            warn(rel, i, "W3", "label-then-colon sentence, rewrite it")


ASSIGN_OPEN = re.compile(r"=\s*[rRbBuUfF]*(\"\"\"|''')")


def docstring_spans(text: str) -> list[tuple[int, int, list[str]]]:
    """Rough (start, end, lines) spans of triple-quoted strings.

    Assignment-opened spans (lua = f\"\"\"...\"\"\") hold embedded code,
    not documentation, so they are skipped.
    """
    spans = []
    current: list[str] | None = None
    start = 0
    skip = False
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        fence = line.count('"""') + line.count("'''")
        if current is None:
            if fence == 1:
                current, start = [raw], i
                skip = bool(ASSIGN_OPEN.search(line))
            elif fence >= 2:
                spans.append((i, i, [raw]))
        else:
            current.append(raw)
            if fence >= 1:
                if not skip:
                    spans.append((start, i, current))
                current = None
    return spans


def check_python(path: Path) -> None:
    rel = path.relative_to(ROOT)
    text = path.read_text()
    lines = text.splitlines()
    for start, end, span in docstring_spans(text):
        first = span[0].strip().lstrip('uUrRbBfF')
        body = first.lstrip("\"'").strip()
        if body and not DOC_SECTION.match(body):
            word = body.split()[0].rstrip(",:;.")
            if IMPERATIVE_LEAD.match(word):
                warn(rel, start, "W4", f"docstring opens with {word!r}")
        for offset, raw in enumerate(span):
            if len(raw) > MAX_WIDTH:
                err(rel, start + offset, "E6", "docstring line over 80")
            if ";" in raw.replace("`", ""):
                warn(rel, start + offset, "W1", "semicolon in docstring")
    for i, raw in enumerate(lines, 1):
        stripped = raw.strip()
        if stripped.startswith("#") and len(raw) > MAX_WIDTH:
            err(rel, i, "E6", "comment line over 80")
        if stripped.startswith("#"):
            bare = stripped.lstrip("#").strip()
            if EM_DASH.search(bare) and not SIG_HEADER.match(bare):
                warn(rel, i, "W2", "em/en dash in comment")
            if (
                LABEL_COLON.match(bare)
                and not NOTICE_LABEL.match(bare)
                and not SCHEMATIC_HEADER.match(bare)
            ):
                warn(rel, i, "W3", "label-then-colon in comment")


def check_shell(path: Path) -> None:
    rel = path.relative_to(ROOT)
    for i, raw in enumerate(path.read_text().splitlines(), 1):
        stripped = raw.strip()
        if not stripped.startswith("#"):
            continue
        if len(raw) > MAX_WIDTH:
            err(rel, i, "E6", "comment line over 80")
        bare = stripped.lstrip("#").strip()
        if EM_DASH.search(bare) and not SIG_HEADER.match(bare):
            warn(rel, i, "W2", "em/en dash in comment")
        if (
            LABEL_COLON.match(bare)
            and not NOTICE_LABEL.match(bare)
            and not SCHEMATIC_HEADER.match(bare)
        ):
            warn(rel, i, "W3", "label-then-colon in comment")


def iter_source_files() -> tuple[list[Path], list[Path]]:
    py_files, sh_files = [], []
    for base in (ROOT / "home", ROOT / "scripts"):
        for path in sorted(base.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            if path.suffix == ".py":
                py_files.append(path)
                continue
            try:
                first = path.read_text().splitlines()[0]
            except (UnicodeDecodeError, IndexError):
                continue
            if "python3" in first:
                py_files.append(path)
            elif first.startswith("#!") and ("sh" in first or "bash" in first):
                sh_files.append(path)
    return py_files, sh_files


def main() -> int:
    strict = "--strict" in sys.argv
    for path in MD_FILES:
        check_markdown(path)
    py_files, sh_files = iter_source_files()
    for path in py_files:
        check_python(path)
    for path in sh_files:
        check_shell(path)
    for item in errors:
        print(f"error: {item}")
    for item in warnings:
        print(f"warning: {item}")
    print(f"{len(errors)} errors, {len(warnings)} warnings "
          f"({len(MD_FILES)} docs, {len(py_files)} python, "
          f"{len(sh_files)} shell files)")
    if errors or (strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
