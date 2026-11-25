import json

import validate_plugin as vp


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def replace_in(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def codes(report):
    return {issue.code for issue in report.errors}


def test_repository_validates_cleanly(root):
    report = vp.validate_plugin(root)

    assert report.ok
    assert report.errors == []
    assert vp.expected_version(root, report) == "0.1.0"


def test_missing_required_file(plugin_root):
    (plugin_root / "skills" / "react-expert" / "scripts" / "detect_stack.py").unlink()

    report = vp.validate_plugin(plugin_root)

    assert "missing-required-file" in codes(report)


def test_empty_required_file(plugin_root):
    (plugin_root / "README.md").write_text("", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "empty-file" in codes(report)


def test_duplicate_json_key(plugin_root):
    path = plugin_root / "plugin.json"
    path.write_text(
        '{\n  "$schema": "https://antigravity.google/schemas/v1/plugin.json",\n'
        '  "name": "react-expert",\n  "name": "react-expert",\n'
        '  "description": "A version-aware React implementation plugin."\n}\n',
        encoding="utf-8",
    )

    report = vp.validate_plugin(plugin_root)

    assert "duplicate-json-key" in codes(report)


def test_version_mismatch_across_manifests(plugin_root):
    path = plugin_root / ".cursor-plugin" / "plugin.json"
    data = load_json(path)
    data["version"] = "0.2.0"
    write_json(path, data)

    report = vp.validate_plugin(plugin_root)

    assert "version-mismatch" in codes(report)


def test_invalid_semver(plugin_root):
    path = plugin_root / ".claude-plugin" / "plugin.json"
    data = load_json(path)
    data["version"] = "one"
    write_json(path, data)

    report = vp.validate_plugin(plugin_root)

    assert "invalid-version" in codes(report)


def test_root_manifest_rejects_extra_key(plugin_root):
    path = plugin_root / "plugin.json"
    data = load_json(path)
    data["version"] = "0.1.0"
    write_json(path, data)

    report = vp.validate_plugin(plugin_root)

    assert "root-manifest-extra-key" in codes(report)


def test_root_manifest_requires_schema(plugin_root):
    path = plugin_root / "plugin.json"
    data = load_json(path)
    data["$schema"] = "https://example.com/schema.json"
    write_json(path, data)

    report = vp.validate_plugin(plugin_root)

    assert "root-manifest-schema" in codes(report)


def test_claude_manifest_requires_owner(plugin_root):
    path = plugin_root / ".claude-plugin" / "marketplace.json"
    data = load_json(path)
    del data["owner"]
    write_json(path, data)

    report = vp.validate_plugin(plugin_root)

    assert "missing-owner" in codes(report)


def test_codex_manifest_requires_capabilities(plugin_root):
    path = plugin_root / ".codex-plugin" / "plugin.json"
    data = load_json(path)
    data["interface"]["capabilities"] = []
    write_json(path, data)

    report = vp.validate_plugin(plugin_root)

    assert "codex-capabilities" in codes(report)


def test_cursor_manifest_requires_commands(plugin_root):
    path = plugin_root / ".cursor-plugin" / "plugin.json"
    data = load_json(path)
    del data["commands"]
    write_json(path, data)

    report = vp.validate_plugin(plugin_root)

    assert "cursor-commands" in codes(report)


def test_copilot_marketplace_version_must_match(plugin_root):
    path = plugin_root / ".github" / "plugin" / "marketplace.json"
    data = load_json(path)
    data["plugins"][0]["version"] = "0.2.0"
    write_json(path, data)

    report = vp.validate_plugin(plugin_root)

    assert "version-mismatch" in codes(report)


def test_agents_marketplace_requires_available_policy(plugin_root):
    path = plugin_root / ".agents" / "plugins" / "marketplace.json"
    data = load_json(path)
    data["plugins"][0]["policy"]["installation"] = "DISABLED"
    write_json(path, data)

    report = vp.validate_plugin(plugin_root)

    assert "agents-policy" in codes(report)


def test_skill_requires_frontmatter(plugin_root):
    path = plugin_root / "skills" / "react-expert" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.split("---", 2)[2], encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "missing-frontmatter" in codes(report)


def test_skill_name_must_match(plugin_root):
    replace_in(
        plugin_root / "skills" / "react-expert" / "SKILL.md",
        "name: react-expert",
        "name: wrong-name",
    )

    report = vp.validate_plugin(plugin_root)

    assert "wrong-name" in codes(report)


def test_skill_description_must_be_substantive(plugin_root):
    replace_in(
        plugin_root / "skills" / "react-expert" / "SKILL.md",
        "description: 'Performs React version and framework detection, follows official react.dev guidance and existing codebase conventions before writing version-safe components, hooks and state logic with accessible UI, unit tests and an 80% coverage gate into REACT-EXPERT-IMPL.md.'",
        "description: 'Too short.'",
    )

    report = vp.validate_plugin(plugin_root)

    assert "weak-description" in codes(report)


def test_skill_requires_mit_license(plugin_root):
    replace_in(
        plugin_root / "skills" / "react-expert" / "SKILL.md",
        "license: MIT",
        "license: GPL",
    )

    report = vp.validate_plugin(plugin_root)

    assert "missing-license" in codes(report)


def test_skill_version_must_match(plugin_root):
    replace_in(
        plugin_root / "skills" / "react-expert" / "SKILL.md",
        'version: "0.1.0"',
        'version: "0.2.0"',
    )

    report = vp.validate_plugin(plugin_root)

    assert "skill-version-mismatch" in codes(report)


def test_skill_references_must_exist(plugin_root):
    replace_in(
        plugin_root / "skills" / "react-expert" / "SKILL.md",
        "[Rendering and environment](references/rendering-and-environment.md)",
        "[Rendering and environment](references/missing-doc.md)",
    )

    report = vp.validate_plugin(plugin_root)

    assert "missing-reference" in codes(report)


def test_skill_requires_domain_content(plugin_root):
    text_path = plugin_root / "skills" / "react-expert" / "SKILL.md"
    text = text_path.read_text(encoding="utf-8").replace("react.dev", "reactDevDocs")
    text_path.write_text(text, encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "missing-skill-content" in codes(report)


def test_skill_requires_untrusted_input_guardrail(plugin_root):
    text_path = plugin_root / "skills" / "react-expert" / "SKILL.md"
    text = text_path.read_text(encoding="utf-8").replace("untrusted data", "project data")
    text_path.write_text(text, encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "missing-skill-content" in codes(report)


def test_markdown_link_cannot_escape_root(plugin_root):
    replace_in(
        plugin_root / "skills" / "react-expert" / "SKILL.md",
        "[Rendering and environment](references/rendering-and-environment.md)",
        "[Rendering and environment](../../../etc/passwd)",
    )

    report = vp.validate_plugin(plugin_root)

    assert "path-escape" in codes(report)


def test_openai_yaml_requires_default_prompt(plugin_root):
    path = plugin_root / "agents" / "openai.yaml"
    path.write_text("interface:\n  display_name: React Expert\n", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "missing-default-prompt" in codes(report)


def test_assets_must_be_valid_svg(plugin_root):
    (plugin_root / "assets" / "icon.svg").write_text("<div></div>", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "invalid-svg" in codes(report)


def test_commands_require_frontmatter(plugin_root):
    path = plugin_root / "commands" / "react-expert.md"
    path.write_text("# React Expert\n", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "command-frontmatter" in codes(report)


def test_commands_require_domain_content(plugin_root):
    path = plugin_root / "commands" / "react-expert.md"
    text = path.read_text(encoding="utf-8").replace("80% coverage", "coverage")
    path.write_text(text, encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "missing-command-content" in codes(report)


def test_readme_requires_domain_tokens(plugin_root):
    path = plugin_root / "README.md"
    path.write_text("# React Expert\n\nInstall with npx skills add.\n", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "docs-content" in codes(report)


def test_license_must_be_mit(plugin_root):
    (plugin_root / "LICENSE").write_text("All rights reserved.\n", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "license-content" in codes(report)


def test_makefile_requires_targets(plugin_root):
    path = plugin_root / "Makefile"
    path.write_text("test:\n\ttrue\n", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "makefile-content" in codes(report)


def test_ci_requires_validation_steps(plugin_root):
    path = plugin_root / ".github" / "workflows" / "ci.yml"
    path.write_text("name: CI\n", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "ci-content" in codes(report)


def test_gitignore_requires_secret_ignore(plugin_root):
    path = plugin_root / ".gitignore"
    path.write_text(".coverage\n.env\n", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "gitignore-content" not in codes(report)


def test_gitignore_forbids_ignoring_pyproject(plugin_root):
    path = plugin_root / ".gitignore"
    path.write_text(path.read_text(encoding="utf-8") + "\npyproject.toml\n", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "gitignore-content" in codes(report)


def test_placeholder_scan(plugin_root):
    path = plugin_root / "README.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nTODO write more docs\n", encoding="utf-8")

    report = vp.validate_plugin(plugin_root)

    assert "placeholder" in codes(report)


def test_json_cli_output(root, capsys):
    code = vp.main([str(root), "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"


def test_cli_fails_on_broken_plugin(plugin_root, capsys):
    (plugin_root / "LICENSE").write_text("wrong\n", encoding="utf-8")

    assert vp.main([str(plugin_root)]) == 1
    assert "[ERROR]" in capsys.readouterr().out
