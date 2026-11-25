from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_MIN_COVERAGE = 80

ARTIFACT_MARKER_RE = re.compile(r"<!--\s*react-expert:artifact\s+([^>]*?)-->")
MARKER_RE = re.compile(r"<!--\s*react-expert:([a-z-]+)\s+([^>]*?)-->")
METADATA_RE = re.compile(r"^-\s+([^:]+):\s*(.+?)\s*$", re.M)
COVERAGE_VALUE_RE = re.compile(r"^(\d{1,3})\s*%\s*$")
ID_RE = re.compile(r"^(CHG|T|CFG|EV)-(\d{3})$")

REQUIRED_SECTIONS = (
    "analysis",
    "stack",
    "design",
    "implementation",
    "tests",
    "validation",
    "configurations",
    "evidence",
    "assumptions",
    "traceability",
)

SECTION_HEADINGS = {
    "analysis": "Brief Analysis",
    "stack": "Detected Stack",
    "design": "Design",
    "implementation": "Clean and Complete Code",
    "tests": "Unit Tests",
    "validation": "Validation",
    "configurations": "Configuration",
    "evidence": "Evidence",
    "assumptions": "Assumptions",
    "traceability": "Traceability",
}

METADATA_FIELDS = (
    "Status",
    "Date",
    "Reviewer",
    "Artifact",
    "React Version",
    "TypeScript Version",
    "Build Tool",
    "Framework",
    "Rendering Mode",
    "Test Runner",
    "Changes Applied",
    "Tests Run",
    "Coverage",
    "Coverage Tool",
)

ALLOWED_STATUSES = ("draft", "final")
ALLOWED_BUILD_TOOLS = ("npm", "yarn", "pnpm", "bun", "turbo", "nx")
ALLOWED_FRAMEWORKS = ("next", "remix", "vite", "cra", "expo", "mixed", "unknown")
ALLOWED_RENDERING_MODES = ("csr", "ssr", "hybrid", "mixed", "unknown")
ALLOWED_TEST_RUNNERS = ("jest", "vitest")
ALLOWED_CHANGE_STATUSES = ("implemented", "needs-review", "blocked", "alternative")
ALLOWED_EVIDENCE_STATUSES = ("passed", "partial", "failed")

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONFIG_FILE_RE = re.compile(
    r"^(?:package\.json|tsconfig(?:[^/]*)\.json|vite\.config\.[^/]+|"
    r"next\.config\.[^/]+|remix\.config\.[^/]+|jest\.config\.[^/]+|"
    r"vitest\.config\.[^/]+|babel\.config\.[^/]+|\.babelrc|components\.json|"
    r"tailwind\.config\.[^/]+|postcss\.config\.[^/]+|"
    r"src/environments/[^/]+\.ts|environment\.ts)$"
)

FENCED_CODE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`]*`")


@dataclass
class Issue:
    code: str
    message: str
    location: str = ""


@dataclass
class Report:
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    strict: bool = False

    def error(self, code: str, message: str, location: str = "") -> None:
        self.errors.append(Issue(code, message, location))

    def warning(self, code: str, message: str, location: str = "") -> None:
        self.warnings.append(Issue(code, message, location))

    @property
    def ok(self) -> bool:
        return not self.errors and not (self.strict and self.warnings)

    def to_dict(self, path: str = "") -> dict:
        return {
            "path": path,
            "status": "PASS" if self.ok else "FAIL",
            "errors": [issue.__dict__ for issue in self.errors],
            "warnings": [issue.__dict__ for issue in self.warnings],
        }


def parse_attributes(fragment: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for match in re.finditer(r'([A-Za-z][A-Za-z0-9_-]*)\s*=\s*("[^"]*"|\'[^\']*\'|[^\s]+)', fragment):
        attributes[match.group(1)] = match.group(2).strip("\"'")
    return attributes


def marker_records(text: str) -> list[dict]:
    return [
        {
            "kind": match.group(1),
            "attributes": parse_attributes(match.group(2)),
            "start": match.start(),
            "end": match.end(),
        }
        for match in MARKER_RE.finditer(text)
    ]


def markers_of(text: str, kind: str) -> list[dict]:
    return [record for record in marker_records(text) if record["kind"] == kind]


def strip_markers(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.strip().startswith("<!--"))


def strip_code(text: str) -> str:
    return INLINE_CODE_RE.sub("", FENCED_CODE_RE.sub("", text))


def content_lines(text: str) -> list[str]:
    return [line.strip() for line in strip_markers(text).splitlines() if line.strip()]


def parse_metadata(text: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for match in METADATA_RE.finditer(text):
        key = match.group(1).strip()
        if key in METADATA_FIELDS and key not in metadata:
            metadata[key] = match.group(2).strip()
    return metadata


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    match = re.match(r"^(\d+)$", value.strip())
    return int(match.group(1)) if match else None


def parse_coverage(value: str | None) -> int | None:
    if value is None:
        return None
    match = COVERAGE_VALUE_RE.match(value.strip())
    return int(match.group(1)) if match else None


def section_bodies(text: str, report: Report) -> dict[str, str]:
    artifacts = ARTIFACT_MARKER_RE.findall(text)
    if not artifacts:
        report.error("missing-artifact-marker", "The artifact marker is missing.")
    elif len(artifacts) > 1:
        report.error("duplicate-artifact-marker", "The artifact marker appears more than once.")
    else:
        attributes = parse_attributes(artifacts[0])
        if attributes.get("type") != "implementation":
            report.error("wrong-artifact-type", "The artifact type must be implementation.")
        if attributes.get("version") != "1":
            report.error("artifact-version", "The artifact version must be 1.")

    section_markers = markers_of(text, "section")
    found: dict[str, list[int]] = {name: [] for name in REQUIRED_SECTIONS}
    for record in section_markers:
        name = record["attributes"].get("id", "")
        if name in found:
            found[name].append(record["start"])
        else:
            report.error("unknown-section", f"Unknown section marker: {name}.", name)

    for name in REQUIRED_SECTIONS:
        if not found[name]:
            report.error("missing-section", f"Section marker is missing: {name}.", name)
        elif len(found[name]) > 1:
            report.error("duplicate-section", f"Section marker appears twice: {name}.", name)

    section_starts = sorted(
        record["start"] for record in section_markers if record["attributes"].get("id") in found
    )
    bodies: dict[str, str] = {}
    for name in REQUIRED_SECTIONS:
        starts = found[name]
        if len(starts) != 1:
            continue
        start = starts[0]
        marker_end = next(record["end"] for record in section_markers if record["start"] == start)
        following = [value for value in section_starts if value > start]
        end = min(following) if following else len(text)
        bodies[name] = text[marker_end:end]
        if not content_lines(bodies[name]):
            report.error("empty-section", f"Section has no content: {name}.", name)
    return bodies


def validate_metadata(metadata: dict[str, str], min_coverage: int, report: Report) -> None:
    for name in METADATA_FIELDS:
        if not metadata.get(name):
            report.error("missing-metadata", f"Metadata field is missing: {name}.", name)

    status = metadata.get("Status", "").lower()
    if status and status not in ALLOWED_STATUSES:
        report.error("invalid-status", f"Invalid report status: {status}.", "Status")

    date = metadata.get("Date", "")
    if date and not DATE_RE.match(date):
        report.error("invalid-date", "Date must use YYYY-MM-DD.", "Date")

    build_tool = metadata.get("Build Tool", "").lower()
    if build_tool and build_tool not in ALLOWED_BUILD_TOOLS:
        report.error("invalid-build-tool", f"Invalid build tool: {build_tool}.", "Build Tool")

    framework = metadata.get("Framework", "").lower()
    if framework and framework not in ALLOWED_FRAMEWORKS:
        report.error("invalid-framework", f"Invalid framework: {framework}.", "Framework")

    rendering = metadata.get("Rendering Mode", "").lower()
    if rendering and rendering not in ALLOWED_RENDERING_MODES:
        report.error("invalid-rendering", f"Invalid rendering mode: {rendering}.", "Rendering Mode")

    runner = metadata.get("Test Runner", "").lower()
    if runner and runner not in ALLOWED_TEST_RUNNERS:
        report.error("invalid-test-runner", f"Invalid test runner: {runner}.", "Test Runner")

    react = metadata.get("React Version", "")
    if react and not VERSION_RE.match(react):
        report.error(
            "invalid-react-version",
            "React Version must use the form 19.0.0.",
            "React Version",
        )

    typescript = metadata.get("TypeScript Version", "")
    if typescript and not VERSION_RE.match(typescript):
        report.error(
            "invalid-typescript-version",
            "TypeScript Version must use the form 5.7.2.",
            "TypeScript Version",
        )

    coverage = parse_coverage(metadata.get("Coverage"))
    if metadata.get("Coverage") and (coverage is None or coverage > 100):
        report.error("invalid-coverage", "Coverage must be a percentage such as 88%.", "Coverage")
    elif coverage is not None and coverage < min_coverage:
        report.error(
            "coverage-below-gate",
            f"Coverage {coverage}% is below the {min_coverage}% gate.",
            "Coverage",
        )

    tool = metadata.get("Coverage Tool", "").lower()
    if tool and tool not in ALLOWED_TEST_RUNNERS:
        report.error("invalid-coverage-tool", "Coverage Tool must be jest or vitest.", "Coverage Tool")
    elif tool and runner and tool != runner:
        report.error(
            "coverage-tool-mismatch",
            "Coverage Tool must match the configured Test Runner.",
            "Coverage Tool",
        )


def bounded_body(text: str, record: dict) -> str:
    following = [other["start"] for other in marker_records(text) if other["start"] > record["start"]]
    end = min(following) if following else len(text)
    return text[record["end"] : end]


def parse_numbered_entries(text: str, kind: str, prefix: str, report: Report) -> list[dict]:
    records = markers_of(text, kind)
    if not records:
        report.error(f"missing-{kind}", f"At least one {kind} entry is required.")
        return []

    entries: list[dict] = []
    seen: set[str] = set()
    for record in records:
        identifier = record["attributes"].get("id", "")
        match = ID_RE.match(identifier)
        if not match or match.group(1) != prefix:
            report.error(f"invalid-{kind}-id", f"Invalid {kind} id: {identifier}.", identifier)
        if identifier in seen:
            report.error(f"duplicate-{kind}-id", f"Duplicate {kind} id: {identifier}.", identifier)
        seen.add(identifier)
        entries.append(
            {
                "id": identifier,
                "attributes": record["attributes"],
                "body": bounded_body(text, record),
            }
        )
    return entries


def require_fields(entry: dict, fields: dict[str, int], report: Report, prefix: str = "") -> None:
    for name, minimum in fields.items():
        match = re.search(rf"^- {re.escape(name)}:\s*(.+)$", entry["body"], re.M)
        value = match.group(1).strip() if match else ""
        if len(value) < minimum:
            field_code = name.lower().replace(" ", "-")
            code = f"missing-{prefix}-{field_code}" if prefix else f"missing-{field_code}"
            report.error(
                code,
                f"Entry {entry['id']} needs a substantive {name} field.",
                entry["id"],
            )


def validate_analysis(body: str, metadata: dict[str, str], changes: list[dict], report: Report) -> None:
    if SECTION_HEADINGS["analysis"] not in strip_markers(body):
        report.error("missing-analysis-heading", "The analysis section needs the Brief Analysis heading.")
    if len(content_lines(body)) < 2:
        report.error("thin-analysis", "The analysis section needs an explanation.")

    raw_declared = metadata.get("Changes Applied", "")
    declared = parse_int(raw_declared)
    if raw_declared and declared is None:
        report.error(
            "invalid-changes-count",
            "Changes Applied must be an integer.",
            "Changes Applied",
        )
    elif declared is not None and declared != len(changes):
        report.error(
            "count-mismatch",
            f"Changes Applied ({declared}) does not match the {len(changes)} change entries.",
            "Changes Applied",
        )


def validate_stack(body: str, metadata: dict[str, str], report: Report) -> None:
    records = markers_of(body, "stack")
    if len(records) != 1:
        report.error("missing-stack-marker", "Exactly one stack marker is required.", "stack")
        return
    attributes = records[0]["attributes"]
    expected = {
        "react": metadata.get("React Version", ""),
        "typescript": metadata.get("TypeScript Version", ""),
        "build": metadata.get("Build Tool", ""),
        "framework": metadata.get("Framework", ""),
        "rendering": metadata.get("Rendering Mode", ""),
        "test-runner": metadata.get("Test Runner", ""),
    }
    for key, value in expected.items():
        if attributes.get(key, "").lower() != value.lower():
            report.error("stack-mismatch", f"Stack marker {key} does not match metadata.", key)
    if attributes.get("strict", "").lower() not in {"true", "false"}:
        report.error("stack-mismatch", "Stack marker strict must be true or false.", "strict")

    if not re.search(r"package\.json|tsconfig\.json", strip_markers(body), re.I):
        report.warning(
            "unverified-stack",
            "The stack section does not name a detected React descriptor.",
            "stack",
        )


def validate_changes(text: str, report: Report) -> list[dict]:
    changes = parse_numbered_entries(text, "change", "CHG", report)
    for entry in changes:
        status = entry["attributes"].get("status", "")
        if status not in ALLOWED_CHANGE_STATUSES:
            report.error("invalid-change-status", f"Invalid change status: {status}.", entry["id"])
        require_fields(entry, {"File": 8, "Change": 15, "Design": 15}, report)
    return changes


def validate_tests(text: str, body: str, expected_runner: str, report: Report) -> list[dict]:
    tests = parse_numbered_entries(text, "test", "T", report)
    if expected_runner not in strip_code(strip_markers(body)).lower():
        report.error("runner-required", f"The tests section must mention {expected_runner}.")

    for entry in tests:
        attributes = entry["attributes"]
        if attributes.get("framework", "").lower() != expected_runner:
            report.error("runner-mismatch", f"A test entry must declare framework={expected_runner}.", entry["id"])
        if attributes.get("context", "").lower() != "unit":
            report.error("unit-context-required", "A test entry must have context=unit.", entry["id"])
        require_fields(entry, {"File": 8, "Cases": 10, "Coverage": 10}, report)
    return tests


def validate_configurations(text: str, body: str, report: Report) -> list[dict]:
    entries = parse_numbered_entries(text, "config", "CFG", report) if markers_of(text, "config") else []
    if not entries:
        lines = [
            line
            for line in (item.strip() for item in strip_markers(body).splitlines())
            if line and not line.startswith("#")
        ]
        if lines != ["No changes."]:
            report.error(
                "missing-config-declaration",
                "The configurations section must say 'No changes.' or declare configuration entries.",
            )
    for entry in entries:
        file_name = entry["attributes"].get("file", "")
        if not CONFIG_FILE_RE.match(file_name):
            report.error("invalid-config-file", "A config entry must name an allowed React config file.", entry["id"])
        require_fields(entry, {"Property": 3, "Reason": 10}, report, prefix="config")
    return entries


def validate_validation(
    body: str, min_coverage: int, expected_runner: str, report: Report
) -> None:
    records = markers_of(body, "coverage")
    if len(records) != 1:
        report.error("missing-coverage-marker", "Exactly one coverage marker is required.", "validation")
        return
    attributes = records[0]["attributes"]
    value = parse_int(attributes.get("value"))
    gate = parse_int(attributes.get("gate"))
    if value is None or gate is None or value > 100 or gate > 100:
        report.error("invalid-coverage", "The coverage marker needs numeric value and gate.", "validation")
        return
    if value < min_coverage or gate < min_coverage:
        report.error(
            "coverage-below-gate",
            f"Coverage marker must satisfy the {min_coverage}% gate.",
            "validation",
        )
    if attributes.get("tool", "").lower() != expected_runner:
        report.error(
            "invalid-coverage-tool",
            f"The coverage marker must declare tool={expected_runner}.",
            "validation",
        )

    checkboxes = len(re.findall(r"^- \[[ xX]\]", body, re.M))
    if checkboxes < 4:
        report.error("insufficient-validation", "The validation section needs at least four checkboxes.")

    stripped = strip_markers(body).lower()
    for token in ("test", expected_runner, f"{min_coverage}%"):
        if token not in stripped:
            report.error("missing-validation-detail", f"Validation evidence must mention {token}.")


def validate_evidence(text: str, report: Report) -> list[dict]:
    entries = parse_numbered_entries(text, "evidence", "EV", report)
    for entry in entries:
        status = entry["attributes"].get("status", "")
        if status not in ALLOWED_EVIDENCE_STATUSES:
            report.error("invalid-evidence-status", f"Invalid evidence status: {status}.", entry["id"])
        require_fields(entry, {"Result": 8}, report)
    if entries and not any(entry["attributes"].get("status") == "passed" for entry in entries):
        report.error("evidence-not-passed", "At least one evidence row must have status=passed.")
    return entries


def validate_traceability(
    body: str,
    changes: list[dict],
    tests: list[dict],
    evidence: list[dict],
    report: Report,
) -> None:
    stripped = strip_markers(body)
    for token in ("Change", "Test", "Evidence"):
        if token not in stripped:
            report.error("missing-traceability-header", f"Traceability table needs a {token} column.")
    for entry in changes + tests + evidence:
        if entry["id"] and entry["id"] not in stripped:
            report.error("traceability-gap", f"Entry {entry['id']} is not linked in traceability.", entry["id"])

    rows = [
        line
        for line in stripped.splitlines()
        if line.strip().startswith("|") and line.count("|") >= 4
    ]
    for change in changes:
        linked = [
            row
            for row in rows
            if change["id"] in row
            and any(test["id"] in row for test in tests)
            and any(evidence["id"] in row for evidence in evidence)
        ]
        if not linked:
            report.error(
                "traceability-gap",
                f"Change {change['id']} needs a table row with a test and an evidence id.",
                change["id"],
            )


def validate_suppressions(text: str, report: Report) -> None:
    stripped = strip_code(text)
    if re.search(r"@ts-ignore|@ts-expect-error|eslint-disable|NOSONAR", stripped, re.I) and "Suppression approved" not in stripped:
        report.error(
            "suppression-without-approval",
            "Suppressions require a recorded false positive and approval.",
        )


def validate_approval(text: str, report: Report) -> None:
    if re.search(r"\b(LGTM|Ship it|Approved by|Approval:)", text, re.I):
        report.error("approval-verdict", "Do not include an approval verdict in the artifact.")


def scan_placeholders(text: str, report: Report) -> None:
    stripped = strip_code(text)
    if re.search(r"\b(TODO|FIXME|TBD)\b|\bplaceholder\b|\bomitted\b", stripped, re.I):
        report.error("placeholder", "The artifact contains a placeholder.")


def scan_secrets(text: str, report: Report) -> None:
    patterns = (
        r"gh[pousr]_[A-Za-z0-9]{20,}",
        r"\b(AKIA|ASIA)[0-9A-Z]{16}\b",
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        r"(?i)(?:password|token|apiKey)\s*[:=]\s*(?!\[REDACTED\]|\$\{)[^\s]+",
        r"\b[0-9a-fA-F]{40}\b",
        r"Bearer\s+(?!\[REDACTED\])[A-Za-z0-9._-]{20,}",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        report.error("secret", "The artifact contains a possible secret.")


def validate_report(
    text: str,
    report: Report,
    min_coverage: int = DEFAULT_MIN_COVERAGE,
    strict: bool = False,
) -> None:
    report.strict = strict
    bodies = section_bodies(text, report)
    metadata = parse_metadata(text)
    expected_runner = metadata.get("Test Runner", "").lower()
    validate_metadata(metadata, min_coverage, report)

    changes = validate_changes(text, report)
    tests = validate_tests(text, bodies.get("tests", ""), expected_runner, report)
    configurations = validate_configurations(text, bodies.get("configurations", ""), report)
    evidence = validate_evidence(text, report)

    if "analysis" in bodies:
        validate_analysis(bodies["analysis"], metadata, changes, report)
    if "stack" in bodies:
        validate_stack(bodies["stack"], metadata, report)
    if "design" in bodies and len(content_lines(bodies["design"])) < 2:
        report.error("thin-design", "The design section needs at least two content lines.")
    if "implementation" in bodies and not changes:
        report.error("missing-change", "The implementation section needs a change entry.")
    if "assumptions" in bodies and not content_lines(bodies["assumptions"]):
        report.error("empty-section", "The assumptions section needs content.", "assumptions")
    if "validation" in bodies:
        validate_validation(bodies["validation"], min_coverage, expected_runner, report)
    if "traceability" in bodies:
        validate_traceability(bodies["traceability"], changes, tests, evidence, report)

    validate_suppressions(text, report)
    validate_approval(text, report)
    scan_placeholders(text, report)
    scan_secrets(text, report)

    assert configurations is not None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_report.py",
        description="Validate a REACT-EXPERT-IMPL.md implementation report.",
    )
    parser.add_argument("paths", nargs="+", help="Report files to validate.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    parser.add_argument(
        "--min-coverage",
        type=int,
        default=DEFAULT_MIN_COVERAGE,
        help=f"Minimum coverage percentage (default {DEFAULT_MIN_COVERAGE}).",
    )
    return parser


def format_issue(issue: Issue) -> str:
    location = f" ({issue.location})" if issue.location else ""
    return f"[ERROR] {issue.code}: {issue.message}{location}"


def print_report(path: str, report: Report) -> None:
    print(f"PASS: {path}" if report.ok else f"FAIL: {path}")
    for issue in report.errors:
        print(format_issue(issue))
    for issue in report.warnings:
        print(f"[WARN] {issue.code}: {issue.message}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results: list[tuple[str, Report]] = []
    for value in args.paths:
        path = Path(value)
        report = Report()
        if not path.is_file():
            report.error("missing-report", f"Report not found: {path}.")
        else:
            validate_report(
                path.read_text(encoding="utf-8"),
                report,
                min_coverage=args.min_coverage,
                strict=args.strict,
            )
        results.append((str(path), report))

    all_ok = all(report.ok for _, report in results)
    if args.json:
        print(
            json.dumps(
                {
                    "status": "PASS" if all_ok else "FAIL",
                    "reports": [report.to_dict(path) for path, report in results],
                },
                indent=2,
            )
        )
    else:
        for path, report in results:
            print_report(path, report)

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
