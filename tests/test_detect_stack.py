import json
import shutil

import pytest

import detect_stack as ds


def make_project(
    tmp_path,
    *,
    package=None,
    tsconfig=None,
    environment=None,
    nx=None,
    turbo=None,
):
    project = tmp_path / "project"
    project.mkdir()
    if package:
        shutil.copy(package, project / "package.json")
    if tsconfig:
        shutil.copy(tsconfig, project / "tsconfig.json")
    if environment:
        shutil.copy(environment, project / "environment.ts")
    if nx:
        shutil.copy(nx, project / "nx.json")
    if turbo:
        shutil.copy(turbo, project / "turbo.json")
    return project


def test_detects_react19_next_pnpm_stack(fixtures, tmp_path):
    project = make_project(
        tmp_path,
        package=fixtures / "package-react19-next.json",
        tsconfig=fixtures / "tsconfig.json",
        environment=fixtures / "environment.ts",
    )

    data = ds.detect_stack(project)

    assert data["buildTool"] == "pnpm"
    assert data["descriptor"] == "package.json"
    assert data["react"] == {"version": "19.0.0", "major": 19}
    assert data["reactDom"] == {"version": "19.0.0"}
    assert data["typescript"] == {"version": "5.7.2"}
    assert data["framework"] == "next"
    assert data["rendering"] == "ssr"
    assert data["testRunner"] == "vitest"
    assert data["strict"] is True
    assert data["capabilities"]["react19"] is True
    assert data["capabilities"]["actions"] is True
    assert data["capabilities"]["serverActions"] is True
    assert data["capabilities"]["compiler"] is True
    assert data["capabilities"]["testingLibrary"] is True
    assert data["capabilities"]["tailwind"] is True
    assert data["capabilities"]["radix"] is True
    assert data["capabilities"]["tanstackQuery"] is True
    assert "@tanstack/react-query" in data["stateLibraries"]
    assert "tailwindcss" in data["stylingLibraries"]
    assert "radix" in data["stylingLibraries"]
    assert data["warnings"] == []
    assert data["blockers"] == []


def test_detects_react18_vite_jest_stack(fixtures, tmp_path):
    project = make_project(
        tmp_path,
        package=fixtures / "package-react18-vite.json",
        tsconfig=fixtures / "tsconfig.json",
    )

    data = ds.detect_stack(project)

    assert data["react"] == {"version": "18.3.1", "major": 18}
    assert data["framework"] == "vite"
    assert data["rendering"] == "csr"
    assert data["testRunner"] == "jest"
    assert data["buildTool"] == "npm"
    assert data["capabilities"]["react19"] is False
    assert data["capabilities"]["actions"] is False
    assert data["capabilities"]["serverActions"] is False
    assert data["capabilities"]["compiler"] is False
    assert data["capabilities"]["zustand"] is False
    assert data["warnings"] == []
    assert data["blockers"] == []


def test_detects_react17_cra_legacy_stack(fixtures, tmp_path):
    project = make_project(tmp_path, package=fixtures / "package-react17.json")

    data = ds.detect_stack(project)

    assert data["react"] == {"version": "17.0.2", "major": 17}
    assert data["framework"] == "cra"
    assert data["rendering"] == "csr"
    assert data["testRunner"] == "unknown"
    assert data["strict"] is False
    assert data["capabilities"]["swr"] is True
    assert any(w["code"] == "legacy-react-version" for w in data["warnings"])
    assert any(w["code"] == "unknown-test-runner" for w in data["warnings"])
    assert data["blockers"] == []


def test_config_keys_are_collected_without_values(fixtures, tmp_path):
    project = make_project(
        tmp_path,
        package=fixtures / "package-react19-next.json",
        tsconfig=fixtures / "tsconfig.json",
        environment=fixtures / "environment.ts",
    )

    data = ds.detect_stack(project)
    payload = json.dumps(data)

    assert "apiBaseUrl" in data["configKeys"]
    assert "apiToken" in data["configKeys"]
    assert "super-secret-value" not in payload
    assert data["configKeys"] == sorted(set(data["configKeys"]))


def test_missing_descriptor_raises_config_error(tmp_path):
    with pytest.raises(ds.ConfigError):
        ds.detect_stack(tmp_path)


def test_malformed_package_json_raises_parse_error(tmp_path):
    project = make_project(tmp_path)
    (project / "package.json").write_text("{ not json", encoding="utf-8")

    with pytest.raises(ds.ParseError):
        ds.detect_stack(project)


def test_non_object_package_json_raises_parse_error(tmp_path):
    project = make_project(tmp_path)
    (project / "package.json").write_text("[]", encoding="utf-8")

    with pytest.raises(ds.ParseError):
        ds.detect_stack(project)


def test_missing_versions_are_blockers(tmp_path):
    project = make_project(tmp_path)
    (project / "package.json").write_text(json.dumps({"name": "empty"}), encoding="utf-8")

    data = ds.detect_stack(project)

    assert any(b["code"] == "missing-react-version" for b in data["blockers"])
    assert any(w["code"] == "missing-typescript-version" for w in data["warnings"])

    (project / "package.json").write_text(
        json.dumps({"dependencies": {"react": "not-a-version"}}), encoding="utf-8"
    )
    data = ds.detect_stack(project)
    assert any(b["code"] == "unknown-react-version" for b in data["blockers"])


def test_mixed_test_runners_become_warning(tmp_path):
    project = make_project(tmp_path)
    (project / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"react": "19.0.0", "react-dom": "19.0.0"},
                "devDependencies": {
                    "jest": "29.7.0",
                    "typescript": "5.7.2",
                    "vitest": "2.1.8",
                },
            }
        ),
        encoding="utf-8",
    )

    data = ds.detect_stack(project)

    assert data["testRunner"] == "mixed"
    assert any(w["code"] == "mixed-test-runners" for w in data["warnings"])
    assert data["blockers"] == []


def test_mixed_framework_becomes_warning(fixtures, tmp_path):
    package = json.loads((fixtures / "package-react19-next.json").read_text(encoding="utf-8"))
    package["dependencies"]["vite"] = "6.0.5"
    project = make_project(tmp_path)
    (project / "package.json").write_text(json.dumps(package), encoding="utf-8")

    data = ds.detect_stack(project)

    assert data["framework"] == "mixed"
    assert data["rendering"] == "mixed"
    assert any(w["code"] == "mixed-framework" for w in data["warnings"])


def test_hybrid_rendering_detected_from_sources(fixtures, tmp_path):
    project = make_project(
        tmp_path,
        package=fixtures / "package-react19-next.json",
        tsconfig=fixtures / "tsconfig.json",
    )
    app = project / "app"
    app.mkdir()
    (app / "page.tsx").write_text('"use client";\nexport default function Page() { return null; }\n', encoding="utf-8")
    (app / "actions.ts").write_text(
        "import serverOnly from 'server-only';\nexport default serverOnly;\n", encoding="utf-8"
    )

    data = ds.detect_stack(project)

    assert data["rendering"] == "hybrid"


def test_css_modules_are_detected(fixtures, tmp_path):
    project = make_project(
        tmp_path,
        package=fixtures / "package-react18-vite.json",
        tsconfig=fixtures / "tsconfig.json",
    )
    source = project / "src"
    source.mkdir()
    (source / "orders.module.css").write_text(".list { color: red; }\n", encoding="utf-8")

    data = ds.detect_stack(project)

    assert data["capabilities"]["cssModules"] is True
    assert "css-modules" in data["stylingLibraries"]


def test_compiler_on_legacy_react_warns(tmp_path):
    project = make_project(tmp_path)
    (project / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"react": "17.0.2"},
                "devDependencies": {"babel-plugin-react-compiler": "19.0.0"},
            }
        ),
        encoding="utf-8",
    )

    data = ds.detect_stack(project)

    assert any(w["code"] == "compiler-on-legacy-react" for w in data["warnings"])


def test_detect_major_for_supported_and_unknown_versions():
    assert ds.detect_major("19.0.0") == 19
    assert ds.detect_major("17.0.2") == 17
    assert ds.detect_major("not-a-version") is None
    assert ds.detect_major(None) is None
    assert ds.normalize_version("^19.0.0") == "19.0.0"
    assert ds.normalize_version(None) is None


def test_strip_json_comments_and_normalize_keys():
    text = '{\n // note\n "strict": true /* inline */\n}'
    assert '"strict": true' in ds.strip_json_comments(text)
    assert "note" not in ds.strip_json_comments(text)
    assert ds.normalize_config_keys(["apiToken", "apiBaseUrl", "apiToken", " zone ", ""]) == [
        "apiBaseUrl",
        "apiToken",
        "zone",
    ]


def test_detect_rendering_distinguishes_modes():
    assert ds.detect_rendering("next", False, False) == "ssr"
    assert ds.detect_rendering("next", True, True) == "hybrid"
    assert ds.detect_rendering("vite", False, False) == "csr"
    assert ds.detect_rendering("mixed", True, True) == "mixed"
    assert ds.detect_rendering("unknown", False, False) == "unknown"


def test_detect_framework_distinguishes_supported_frameworks():
    assert ds.detect_framework({"next": "15.0.0"}) == "next"
    assert ds.detect_framework({"@remix-run/react": "2.0.0"}) == "remix"
    assert ds.detect_framework({"@vitejs/plugin-react": "4.0.0"}) == "vite"
    assert ds.detect_framework({"react-scripts": "5.0.1"}) == "cra"
    assert ds.detect_framework({"expo": "52.0.0"}) == "expo"
    assert ds.detect_framework({}) == "unknown"
    assert ds.detect_framework({"next": "15.0.0", "vite": "6.0.0"}) == "mixed"


def test_detect_test_runner_reads_dependencies_and_scripts():
    assert ds.detect_test_runner({"jest": "29.0.0"}, {}) == "jest"
    assert ds.detect_test_runner({}, {"test": "vitest run"}) == "vitest"
    assert ds.detect_test_runner({"jest": "29.0.0", "vitest": "2.0.0"}, {}) == "mixed"
    assert ds.detect_test_runner({}, {}) == "unknown"


def test_detect_build_tool_reads_package_manager_and_monorepo(tmp_path):
    assert ds.detect_build_tool(tmp_path, "pnpm@9.0.0") == "pnpm"
    assert ds.detect_build_tool(tmp_path, "yarn@4.0.0") == "yarn"
    assert ds.detect_build_tool(tmp_path, "bun@1.1.0") == "bun"
    assert ds.detect_build_tool(tmp_path, "npm@10.0.0") == "npm"
    assert ds.detect_build_tool(tmp_path, "") == "npm"
    (tmp_path / "turbo.json").write_text("{}", encoding="utf-8")
    assert ds.detect_build_tool(tmp_path, "") == "turbo"
    (tmp_path / "nx.json").write_text("{}", encoding="utf-8")
    assert ds.detect_build_tool(tmp_path, "") == "nx"


def test_detect_capabilities_gates_actions_and_compiler():
    dependencies = {"react": "19.0.0", "@tanstack/react-query": "5.0.0"}

    next_capabilities = ds.detect_capabilities(dependencies, 19, "next", False, [])
    assert next_capabilities["serverActions"] is True
    assert next_capabilities["compiler"] is False

    vite_capabilities = ds.detect_capabilities(dependencies, 19, "vite", False, [])
    assert vite_capabilities["serverActions"] is False

    compiler_capabilities = ds.detect_capabilities(dependencies, 19, "vite", True, ["reactCompiler"])
    assert compiler_capabilities["compiler"] is True
    assert compiler_capabilities["cssModules"] is True
    assert compiler_capabilities["tanstackQuery"] is True

    legacy_capabilities = ds.detect_capabilities(dependencies, 17, "vite", False, [])
    assert legacy_capabilities["react19"] is False
    assert legacy_capabilities["actions"] is False


def test_cli_writes_stack_json(fixtures, tmp_path):
    project = make_project(tmp_path, package=fixtures / "package-react19-next.json")
    output = tmp_path / "reports" / "stack.json"

    code = ds.main([str(project), "--output", str(output)])

    assert code == ds.EXIT_OK
    text = output.read_text(encoding="utf-8")
    assert text.endswith("\n")
    payload = json.loads(text)
    assert payload["react"]["version"] == "19.0.0"


def test_cli_returns_config_code_for_missing_descriptor(tmp_path, capsys):
    code = ds.main([str(tmp_path)])

    assert code == ds.EXIT_CONFIG
    assert "[ERROR] config:" in capsys.readouterr().err


def test_cli_returns_parse_code_for_invalid_package(tmp_path, capsys):
    project = make_project(tmp_path)
    (project / "package.json").write_text("{", encoding="utf-8")

    code = ds.main([str(project)])

    assert code == ds.EXIT_PARSE
    assert "[ERROR] parse:" in capsys.readouterr().err


def test_cli_strict_mode_fails_on_warnings(fixtures, tmp_path):
    project = make_project(tmp_path, package=fixtures / "package-react17.json")

    assert ds.main([str(project), "--strict"]) == ds.EXIT_STRICT


def test_cli_json_flag_prints_payload(fixtures, tmp_path, capsys):
    project = make_project(tmp_path, package=fixtures / "package-react18-vite.json")

    code = ds.main([str(project), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert code == ds.EXIT_OK
    assert payload["framework"] == "vite"
