#!/usr/bin/env python3
"""Static guards for deploy/: repository rules that no single tool checks.

Reads files only. It never runs Ansible, OpenTofu, kubectl or Helm, and never
contacts a host, cluster or cloud API.

    python deploy/checks/static_guards.py
    python -m unittest discover -s deploy/checks/tests

Guards:
  1. ansible.cfg holds no node addresses or inline host lists: node addresses
     and groups live only in the inventory, group_vars and host_vars.
  2. Committed Layer 1 inventory and variable files use only RFC 5737
     documentation addresses (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24);
     real inventories and private addresses stay out of Git.
  3. No documented or scripted ansible-playbook command passes -e /
     --extra-vars: extra vars have the highest precedence in Ansible and
     would silently override reviewed defaults and privileged switches.
  4. Helm chart claims match reality: while no Chart.yaml exists, Layer 4's
     README must say so and no profile may mark Layer 4 implemented; a layer
     directory with no artifacts beyond its README must be "planned" in every
     profile that points at it.

Standard library only (PyYAML is used when available for guard 4).
"""
from __future__ import annotations

import ipaddress
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DEPLOY = REPO / "deploy"
LAYER1 = DEPLOY / "01-k8s-engine"
LAYER4 = DEPLOY / "04-apps"
PROFILES = DEPLOY / "profiles"

IPV4 = re.compile(r"(?<![\d.])(\d{1,3}(?:\.\d{1,3}){3})(?![\d.])")
DOC_NETS = [ipaddress.ip_network(n) for n in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24")]
# Anything that looks like a node address or inventory entry in ansible.cfg.
CFG_HOST_HINTS = re.compile(r"(?i)\bansible_host\b|^\s*\[(?:all|[a-z0-9_]+:children)\]")
# ansible-playbook invocations with extra vars (short or long form).
EXTRA_VARS = re.compile(r"ansible-playbook\b[^\n]*?\s(?:-e|--extra-vars)(?:\s|=|@|$)")
# Files that document or script playbook runs.
COMMAND_FILE_GLOBS = ("*.md", "*.yml", "*.yaml", "*.sh", "*.ps1")
# Files under deploy/ that are skipped (vendored binaries, local-only output).
SKIP_PARTS = {"tools", "reports", ".terraform", ".seed", "__pycache__"}
NO_CHART = re.compile(r"(?i)no helm chart")


def _files(root: Path, patterns) -> list[Path]:
    out = []
    for pattern in patterns:
        for path in root.rglob(pattern):
            if path.is_file() and not SKIP_PARTS.intersection(path.relative_to(root).parts):
                out.append(path)
    return sorted(set(out))


def _rel(path: Path, repo: Path) -> str:
    return path.relative_to(repo).as_posix()


def check_ansible_cfg(repo: Path = REPO) -> list[str]:
    errors = []
    for cfg in _files(repo / "deploy", ("ansible.cfg",)):
        for lineno, line in enumerate(cfg.read_text(encoding="utf-8").splitlines(), 1):
            code = line.split("#", 1)[0].split(";", 1)[0]
            if not code.strip():
                continue
            where = f"{_rel(cfg, repo)}:{lineno}"
            if IPV4.search(code):
                errors.append(f"{where}: ansible.cfg must not contain node addresses; use the inventory and host_vars")
            if CFG_HOST_HINTS.search(code):
                errors.append(f"{where}: ansible.cfg must not define hosts or groups; use the inventory")
            key, _, value = code.partition("=")
            if key.strip() in ("inventory", "hostfile") and "," in value:
                errors.append(f"{where}: inline host lists are not allowed; point inventory at a file")
    return errors


def _committed_layer1_files(repo: Path) -> list[Path]:
    """Inventory and variable files that are meant to be committed (examples, reviewed defaults)."""
    files = []
    for path in _files(repo / "deploy" / "01-k8s-engine", ("*.ini", "*.yml", "*.yaml")):
        rel = path.relative_to(repo / "deploy" / "01-k8s-engine").parts
        name = path.name
        if name == "hosts.ini" or "host_vars" in rel or name == "local.yml":
            continue  # git-ignored local files: guarded by .gitignore and the CI ls-files check
        if "inventory" in rel or "group_vars" in rel or "inventories" in rel:
            files.append(path)
    return files


def check_committed_addresses(repo: Path = REPO) -> list[str]:
    errors = []
    for path in _committed_layer1_files(repo):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in IPV4.finditer(line):
                try:
                    addr = ipaddress.ip_address(match.group(1))
                except ValueError:
                    continue  # malformed on purpose (negative fixture); inventory validation rejects it
                if not any(addr in net for net in DOC_NETS):
                    errors.append(
                        f"{_rel(path, repo)}:{lineno}: {addr} is not an RFC 5737 documentation address; "
                        "real node addresses belong in the git-ignored inventory/hosts.ini"
                    )
    return errors


def check_no_extra_vars(repo: Path = REPO) -> list[str]:
    errors = []
    roots = [repo / "deploy", repo / ".github" / "workflows"]
    for root in roots:
        if not root.exists():
            continue
        for path in _files(root, COMMAND_FILE_GLOBS):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if EXTRA_VARS.search(line):
                    errors.append(
                        f"{_rel(path, repo)}:{lineno}: ansible-playbook with -e/--extra-vars; put site values in "
                        "inventory/group_vars/all/local.yml or host_vars, and privileged actions behind tags and prompts"
                    )
    return errors


def _load_profiles(repo: Path) -> list[tuple[str, dict]]:
    try:
        import yaml
    except ImportError:  # pragma: no cover -- CI installs PyYAML
        return []
    out = []
    for path in sorted((repo / "deploy" / "profiles").glob("*.yaml")):
        with path.open(encoding="utf-8") as fh:
            out.append((_rel(path, repo), yaml.safe_load(fh)))
    return out


def check_layer_claims(repo: Path = REPO) -> list[str]:
    errors = []
    charts = [p for p in repo.rglob("Chart.yaml") if ".git" not in p.parts]
    readme = repo / "deploy" / "04-apps" / "README.md"
    says_none = readme.exists() and bool(NO_CHART.search(readme.read_text(encoding="utf-8")))
    if not charts and not says_none:
        errors.append("deploy/04-apps/README.md: no Chart.yaml exists, so the README must say there is no Helm chart")
    if charts and says_none:
        errors.append(f"deploy/04-apps/README.md: says there is no Helm chart, but {len(charts)} Chart.yaml file(s) exist")

    empty_layers = set()
    for layer_dir in (repo / "deploy").glob("0[0-4]-*"):
        artifacts = [p for p in layer_dir.rglob("*") if p.is_file() and p.name != "README.md"]
        if not artifacts:
            empty_layers.add(_rel(layer_dir, repo))
    for label, profile in _load_profiles(repo):
        for layer in profile.get("layers", []):
            if layer.get("state") == "implemented":
                if layer.get("path") in empty_layers:
                    errors.append(f"{label}: layer {layer['layer']} is marked implemented but {layer['path']} has no artifacts")
                if layer.get("layer") == 4 and not charts:
                    errors.append(f"{label}: layer 4 is marked implemented but no Helm chart exists")
    return errors


GUARDS = (check_ansible_cfg, check_committed_addresses, check_no_extra_vars, check_layer_claims)


def run(repo: Path = REPO) -> list[str]:
    errors = []
    for guard in GUARDS:
        errors += guard(repo)
    return errors


def main() -> int:
    errors = run()
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        print(f"{len(errors)} error(s)")
        return 1
    print("deploy/ static guards passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
