from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

EXIT_OK = 0
EXIT_STRICT = 1
EXIT_CONFIG = 2
EXIT_PARSE = 3

DESCRIPTORS = ("package.json",)
JEST_PACKAGES = {"jest", "ts-jest", "@swc/jest", "jest-environment-jsdom"}
VITEST_PACKAGES = {"vitest", "@vitest/coverage-v8", "@vitest/coverage-istanbul"}
COMPILER_PACKAGES = {"babel-plugin-react-compiler", "@react-compiler/eslint-plugin"}
STATE_PACKAGES = {
    "@tanstack/react-query": "tanstackQuery",
    "zustand": "zustand",
    "@reduxjs/toolkit": "reduxToolkit",
    "swr": "swr",
}
CONFIG_KEY_RE = re.compile(r"^([A-Za-z0-9._-]+)\s*[:=]")
CLIENT_DIRECTIVE_RE = re.compile(r"^['\"]use client['\"]")
SERVER_ONLY_RE = re.compile(r"from\s+['\"]server-only['\"]|export\s+const\s+runtime\b")
SKIP_DIRS = {"node_modules", ".next", ".git", "dist", "build", "coverage", ".turbo"}


class ConfigError(Exception):
    pass


class ParseError(Exception):
    pass


def item(code: str, message: str, source: str) -> dict:
    return {"code": code, "message": message, "source": source}


def find_descriptor(root: Path) -> str:
    for name in DESCRIPTORS:
        if (root / name).is_file():
            return name
    raise ConfigError(
        "No package.json found. Provide package.json with the exact "
        "React dependency versions before continuing."
    )


def normalize_version(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = str(value).strip().strip("'\"").lstrip("^~><= ")
    match = re.match(r"^v?\d+(?:\.\d+)*(?:[.-][0-9A-Za-z.-]+)?$", cleaned)
    return cleaned if match else None


def detect_major(version: str | None) -> int | None:
    match = re.match(r"^(\d+)", (version or "").strip())
    return int(match.group(1)) if match else None


def normalize_config_keys(values: list[str]) -> list[str]:
    return sorted({value.strip() for value in values if value.strip()})


def strip_json_comments(text: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False
    while index < len(text):
        char = text[index]
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == '"':
            in_string = True
            result.append(char)
            index += 1
            continue
        if text.startswith("//", index):
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = len(text) if end < 0 else end + 2
            continue
        result.append(char)
        index += 1
    return "".join(result)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(strip_json_comments(path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError) as exc:
        raise ParseError(f"Cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ParseError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ParseError(f"Invalid JSON object in {path}")
    return data


def parse_package(path: Path) -> dict:
    raw = load_json(path)
    dependencies: dict[str, str] = {}
    for section in ("dependencies", "devDependencies"):
        values = raw.get(section) or {}
        if isinstance(values, dict):
            dependencies.update({str(name): str(version) for name, version in values.items()})
    scripts = raw.get("scripts") or {}
    if not isinstance(scripts, dict):
        scripts = {}
    return {
        "dependencies": dependencies,
        "packageManager": str(raw.get("packageManager") or ""),
        "scripts": {str(name): str(value) for name, value in scripts.items()},
    }


def parse_tsconfig(path: Path) -> dict:
    empty = {"strict": False, "baseUrl": None, "paths": []}
    if not path.is_file():
        return empty
    raw = load_json(path)
    options = raw.get("compilerOptions") or {}
    if not isinstance(options, dict):
        options = {}
    paths = options.get("paths") or {}
    path_keys = list(paths.keys()) if isinstance(paths, dict) else []
    return {
        "strict": bool(options.get("strict")),
        "baseUrl": options.get("baseUrl"),
        "paths": normalize_config_keys([str(key) for key in path_keys]),
    }


def detect_build_tool(root: Path, package_manager: str) -> str:
    manager = package_manager.strip().lower()
    for name in ("pnpm", "yarn", "bun", "npm"):
        if manager.startswith(name):
            return name
    if (root / "nx.json").is_file():
        return "nx"
    if (root / "turbo.json").is_file():
        return "turbo"
    return "npm"


def detect_framework(dependencies: dict[str, str]) -> str:
    names = set(dependencies)
    detected: list[str] = []
    if "next" in names:
        detected.append("next")
    if "@remix-run/react" in names or "@remix-run/node" in names:
        detected.append("remix")
    if "vite" in names or "@vitejs/plugin-react" in names:
        detected.append("vite")
    if "react-scripts" in names:
        detected.append("cra")
    if "expo" in names:
        detected.append("expo")
    if len(detected) > 1:
        return "mixed"
    return detected[0] if detected else "unknown"


def detect_test_runner(dependencies: dict[str, str], scripts: dict[str, str]) -> str:
    names = set(dependencies)
    commands = " ".join(scripts.values()).lower()
    jest = bool(names & JEST_PACKAGES) or "jest" in commands
    vitest = bool(names & VITEST_PACKAGES) or "vitest" in commands
    detected = [name for name, present in (("jest", jest), ("vitest", vitest)) if present]
    if len(detected) > 1:
        return "mixed"
    return detected[0] if detected else "unknown"


def source_files(root: Path, pattern: str) -> list[Path]:
    return [
        path
        for path in root.rglob(pattern)
        if path.is_file() and not SKIP_DIRS.intersection(path.parts)
    ]


def scan_sources(root: Path) -> tuple[bool, bool, bool]:
    has_client_directive = False
    has_server_only = False
    for pattern in ("*.ts", "*.tsx", "*.js", "*.jsx"):
        for path in source_files(root, pattern):
            text = path.read_text(encoding="utf-8", errors="ignore")
            has_client_directive = has_client_directive or bool(CLIENT_DIRECTIVE_RE.search(text))
            has_server_only = has_server_only or bool(SERVER_ONLY_RE.search(text))
            if has_client_directive and has_server_only:
                break
    has_css_modules = bool(source_files(root, "*.module.css"))
    return has_client_directive, has_server_only, has_css_modules


def scan_config_keys(root: Path) -> list[str]:
    paths: set[Path] = set()
    for pattern in (
        "environment*.ts",
        "*.config.ts",
        "*.config.js",
        ".babelrc",
        "components.json",
    ):
        paths.update(source_files(root, pattern))

    keys: set[str] = set()
    for path in sorted(paths):
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip().lstrip("\"'")
            if not stripped or stripped.startswith(("//", "/*", "*")):
                continue
            match = CONFIG_KEY_RE.match(stripped)
            if match:
                keys.add(match.group(1))
    return sorted(keys)


def detect_rendering(framework: str, has_client_directive: bool, has_server_only: bool) -> str:
    if framework == "mixed":
        return "mixed"
    if framework in {"next", "remix"}:
        if has_client_directive and has_server_only:
            return "hybrid"
        return "ssr"
    if framework in {"vite", "cra", "expo"}:
        return "csr"
    return "unknown"


def detect_capabilities(
    dependencies: dict[str, str],
    react_major: int | None,
    framework: str,
    has_css_modules: bool,
    config_keys: list[str],
) -> dict:
    names = set(dependencies)
    compiler_keys = {"reactCompiler", "react_compiler", "compiler"}
    compiler = bool(names & COMPILER_PACKAGES) or bool(compiler_keys.intersection(config_keys))
    radix = any(name.startswith("@radix-ui/") for name in names)
    state_libraries = sorted(name for name in STATE_PACKAGES if name in names)
    styling_libraries = ["css-modules"] if has_css_modules else []
    if "tailwindcss" in names:
        styling_libraries.append("tailwindcss")
    if "styled-components" in names:
        styling_libraries.append("styled-components")
    if (Path("components.json").name in config_keys) or "components.json" in config_keys:
        styling_libraries.append("shadcn-ui")
    if radix:
        styling_libraries.append("radix")
    return {
        "react19": react_major is not None and react_major >= 19,
        "actions": react_major is not None and react_major >= 19,
        "serverActions": react_major is not None
        and react_major >= 19
        and framework in {"next", "remix"},
        "compiler": compiler,
        "typescript": "typescript" in names,
        "testingLibrary": bool(names & {"@testing-library/react", "react-testing-library"}),
        "ssr": framework in {"next", "remix", "mixed"},
        "tailwind": "tailwindcss" in names,
        "cssModules": has_css_modules,
        "styledComponents": "styled-components" in names,
        "shadcn": "shadcn-ui" in styling_libraries,
        "radix": radix,
        "tanstackQuery": "@tanstack/react-query" in names,
        "zustand": "zustand" in names,
        "reduxToolkit": "@reduxjs/toolkit" in names,
        "swr": "swr" in names,
    }


def detect_stack(root: Path) -> dict:
    root = Path(root).resolve()
    descriptor = find_descriptor(root)
    warnings: list[dict] = []
    blockers: list[dict] = []

    package = parse_package(root / "package.json")
    tsconfig = parse_tsconfig(root / "tsconfig.json")
    dependencies = package["dependencies"]

    raw_react = dependencies.get("react")
    react_version = normalize_version(raw_react)
    react_major = detect_major(react_version)
    react_dom_version = normalize_version(dependencies.get("react-dom"))
    ts_version = normalize_version(dependencies.get("typescript"))

    build_tool = detect_build_tool(root, package["packageManager"])
    framework = detect_framework(dependencies)
    test_runner = detect_test_runner(dependencies, package["scripts"])
    has_client_directive, has_server_only, has_css_modules = scan_sources(root)
    rendering = detect_rendering(framework, has_client_directive, has_server_only)
    config_keys = scan_config_keys(root)
    capabilities = detect_capabilities(
        dependencies, react_major, framework, has_css_modules, config_keys
    )

    state_libraries = sorted(
        name for name in STATE_PACKAGES if name in dependencies
    )
    styling_flags = {
        "tailwind": "tailwindcss",
        "cssModules": "css-modules",
        "styledComponents": "styled-components",
        "shadcn": "shadcn-ui",
        "radix": "radix",
    }
    styling_libraries = sorted(
        reported for key, reported in styling_flags.items() if capabilities[key]
    )

    if not raw_react:
        blockers.append(
            item(
                "missing-react-version",
                "React version not found in package.json dependencies.",
                descriptor,
            )
        )
    elif react_version is None or react_major is None:
        blockers.append(
            item(
                "unknown-react-version",
                "React version in package.json could not be parsed.",
                "package.json",
            )
        )
    elif react_major < 18:
        warnings.append(
            item(
                "legacy-react-version",
                f"React {react_major} is a legacy line; preserve existing patterns.",
                "package.json",
            )
        )

    if not ts_version:
        warnings.append(
            item(
                "missing-typescript-version",
                "TypeScript version not found in package.json dependencies.",
                "package.json",
            )
        )
    if test_runner == "unknown":
        warnings.append(
            item(
                "unknown-test-runner",
                "No Jest or Vitest runner found in dependencies or scripts.",
                "package.json",
            )
        )
    elif test_runner == "mixed":
        warnings.append(
            item(
                "mixed-test-runners",
                "Jest and Vitest are both detected; select a single test runner.",
                "package.json",
            )
        )
    if framework == "mixed":
        warnings.append(
            item(
                "mixed-framework",
                "Multiple React frameworks are declared; select the authoritative one.",
                "package.json",
            )
        )
    elif framework == "unknown":
        warnings.append(
            item(
                "unknown-framework",
                "No supported React framework or bundler was found.",
                "package.json",
            )
        )
    if capabilities["compiler"] and react_major is not None and react_major < 18:
        warnings.append(
            item(
                "compiler-on-legacy-react",
                "React Compiler evidence found on a legacy React line; verify support.",
                "package.json",
            )
        )

    return {
        "projectRoot": str(root),
        "buildTool": build_tool,
        "descriptor": descriptor,
        "react": {"version": react_version, "major": react_major},
        "reactDom": {"version": react_dom_version},
        "typescript": {"version": ts_version},
        "framework": framework,
        "rendering": rendering,
        "testRunner": test_runner,
        "strict": tsconfig["strict"],
        "capabilities": capabilities,
        "stateLibraries": state_libraries,
        "stylingLibraries": styling_libraries,
        "configKeys": config_keys,
        "warnings": warnings,
        "blockers": blockers,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="detect_stack.py",
        description="Detect React versions, framework and capabilities from a project build.",
    )
    parser.add_argument("root", nargs="?", default=".", help="Project root directory.")
    parser.add_argument("--output", help="Write the JSON result to this path.")
    parser.add_argument("--json", action="store_true", help="Print the JSON result to stdout.")
    parser.add_argument("--strict", action="store_true", help="Fail when warnings are present.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = detect_stack(Path(args.root))
    except ConfigError as exc:
        print(f"[ERROR] config: {exc}", file=sys.stderr)
        return EXIT_CONFIG
    except ParseError as exc:
        print(f"[ERROR] parse: {exc}", file=sys.stderr)
        return EXIT_PARSE

    payload = json.dumps(data, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
    if args.json or not args.output:
        print(payload)

    if data["blockers"]:
        return EXIT_CONFIG
    if args.strict and data["warnings"]:
        return EXIT_STRICT
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
