#!/usr/bin/env python3
"""Static validation for the deployment tool catalog and deployment profiles.

Checks deploy/catalog/tools.yaml and every deploy/profiles/*.yaml against the
JSON Schemas in contracts/deploy/ and against cross-field rules that JSON
Schema cannot express. It reads files only: it never runs a tool, contacts a
host or cloud API, or executes anything named in a profile.

    python deploy/catalog/validate.py            # validate the repository
    python -m unittest discover -s deploy/catalog/tests

This is CI tooling for deploy/, not platform code. Deployment Studio (M8) is
expected to enforce the same contracts in Java.

Requires PyYAML and jsonschema >= 4.0.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml

if not hasattr(jsonschema, "Draft202012Validator"):
    sys.exit(
        "deploy/catalog/validate.py needs jsonschema >= 4.0 (JSON Schema draft 2020-12); "
        f"found {getattr(jsonschema, '__version__', 'unknown')}. "
        "Install it with: python -m pip install 'jsonschema>=4.0' pyyaml"
    )

REPO = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO / "deploy" / "catalog" / "tools.yaml"
PROFILES_DIR = REPO / "deploy" / "profiles"
CATALOG_SCHEMA = REPO / "contracts" / "deploy" / "tool-catalog.schema.json"
PROFILE_SCHEMA = REPO / "contracts" / "deploy" / "deployment-profile.schema.json"

# Categories whose tools complement rather than replace each other, so more
# than one default is allowed (LGTM plus the OTel Collector).
COMPLEMENTARY_CATEGORIES = {"observability"}
STORAGE_CATEGORIES = {"block-storage", "object-storage"}
USABLE_STATUSES = {"validated", "approved"}
PRE_USE_STATUSES = {"lab", "planned"}
EXTERNAL_ROLES = {"kubernetes", "identity", "secrets", "relational-database",
                  "event-stream", "object-storage", "ingress", "observability", "gitops"}
KUBERNETES_SECURITY_CAPABILITIES = {"kubernetes-api", "network-policy", "service-routing",
                                    "workload-peer-authentication", "transport-encryption"}
# Reference scheme each secrets backend's key references must use.
SECRET_SCHEMES = {"openbao": "openbao://", "hashicorp-vault": "vault://"}
# Key-management-service reference scheme per cloud provider. A cloud profile
# may point storage encryption or auto-unseal at its own provider's KMS only.
KMS_SCHEMES = {"aws": "awskms://", "azure": "azurekeyvault://", "gcp": "gcpckms://"}
# Unseal methods that need a key reference, and the storage backend
# capability each vault storage_backend needs.
AUTO_UNSEAL_METHODS = {"auto-unseal-cloud-kms", "auto-unseal-transit", "auto-unseal-pkcs11", "auto-unseal-kmip"}
BACKUP_TARGET_SCHEMES = ("s3://", "gs://", "azblob://", "pvc://")
VAULT_STORAGE_CAPABILITY = {"integrated-raft": "integrated-raft-storage", "provider-managed": "provider-managed-storage"}
# Strings that must never appear in a catalog or profile.
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(password|passwd|secret|token)\s*[:=]\s*\S+"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


class _NoDateLoader(yaml.SafeLoader):
    """SafeLoader that keeps YYYY-MM-DD as strings, matching the JSON Schema."""


_NoDateLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.load(fh, Loader=_NoDateLoader)  # noqa: S506 -- SafeLoader subclass


def _schema_errors(document: dict, schema: dict, label: str) -> list[str]:
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    return [
        f"{label}: schema: {'/'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    ]


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)


def _secret_errors(document, label: str) -> list[str]:
    errors = []
    for text in _strings(document):
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{label}: looks like secret material, not a reference: {text[:40]!r}")
    return errors


def validate_catalog(catalog: dict, schema: dict) -> list[str]:
    """Return a list of errors for the catalog (empty means valid)."""
    errors = _schema_errors(catalog, schema, "catalog")
    if errors:
        return errors
    errors += _secret_errors(catalog, "catalog")
    seen: set[str] = set()
    defaults: dict[str, list[str]] = {}
    for tool in catalog["tools"]:
        tid = tool["id"]
        where = f"catalog: {tid}"
        if tid in seen:
            errors.append(f"{where}: duplicate id")
        seen.add(tid)
        if tool["role"] == "default":
            if tool["license"]["class"] != "osi-open-source":
                errors.append(f"{where}: a default must be OSI open source, not {tool['license']['class']}")
            if "default_status" not in tool:
                errors.append(f"{where}: a default needs default_status (proposed or confirmed)")
            defaults.setdefault(tool["category"], []).append(tid)
        if tool["approval"] == "approved":
            not_passed = [k for k, v in tool["checks"].items() if v["status"] not in ("passed", "not-applicable")]
            if not_passed:
                errors.append(f"{where}: approved but checks not passed: {', '.join(sorted(not_passed))}")
        for name, check in tool["checks"].items():
            if check["status"] in ("passed", "failed") and not (check.get("source") or check.get("note")):
                errors.append(f"{where}: {name} check is {check['status']} without a source or note")
            if name == "license" and check["status"] == "passed" and not (check.get("source") and check.get("checked_on")):
                errors.append(f"{where}: a passed licence check needs source and checked_on")
        if tool["role"] == "rejected" and tool["approval"] != "not-approved":
            errors.append(f"{where}: a rejected tool must be not-approved")
    for category, ids in defaults.items():
        if len(ids) > 1 and category not in COMPLEMENTARY_CATEGORIES:
            errors.append(f"catalog: category {category} has more than one default: {', '.join(ids)}")
    return errors


def _tool_errors(profile: dict, tools: dict, label: str, tool_id: str, version: str | None,
                 expected_categories: set[str]) -> list[str]:
    errors = []
    status = profile["status"]
    tool = tools.get(tool_id)
    if tool is None:
        return [f"{label}: {tool_id} is not in the tool catalog"]
    if tool["category"] not in expected_categories:
        errors.append(f"{label}: {tool_id} is a {tool['category']} tool, expected {'/'.join(sorted(expected_categories))}")
    role = tool["role"]
    if role in ("rejected", "test-only"):
        errors.append(f"{label}: {tool_id} is {role} in the catalog and cannot be selected by a profile")
    if role == "lab-only" and status != "lab":
        errors.append(f"{label}: {tool_id} is lab-only; this profile is {status}")
    if role == "optional-compatibility" and tool["approval"] == "not-approved":
        errors.append(f"{label}: {tool_id} is optional-compatibility and not approved (licence not accepted)")
    if status in USABLE_STATUSES and tool["approval"] != "approved":
        errors.append(f"{label}: a {status} profile may only select approved tools; {tool_id} is {tool['approval']}")
    if version is not None:
        if version == "unpinned":
            if status not in PRE_USE_STATUSES:
                errors.append(f"{label}: {tool_id} is unpinned; only lab or planned profiles may select an unpinned tool")
        elif version not in tool["versions"]:
            errors.append(f"{label}: {tool_id} version {version!r} is not a catalog version ({tool['versions'] or 'none pinned'})")
    return errors


def _vault_errors(profile: dict, tools: dict, label: str) -> list[str]:
    """Secrets backend rules: explicit edition capabilities, unseal, backup, topology, data loss."""
    errors = []
    status = profile["status"]
    vault = profile["vault"]
    where = f"{label}: vault"
    errors += _tool_errors(profile, tools, where, vault["tool"], None, {"secrets-backend"})
    if "client" in vault:
        errors += _tool_errors(profile, tools, f"{where}.client", vault["client"], None, {"secrets-client"})
    backend = tools.get(vault["tool"])
    if backend is None or backend["category"] != "secrets-backend":
        return errors

    expected_scheme = SECRET_SCHEMES.get(vault["tool"])
    if expected_scheme and vault["secret_reference_scheme"] != expected_scheme:
        errors.append(f"{where}: secret_reference_scheme should be {expected_scheme} for {vault['tool']}")

    editions = {e["edition"]: e for e in backend.get("editions", [])}
    edition = editions.get(vault["edition"])
    if edition is None:
        errors.append(f"{where}: {vault['tool']} has no edition {vault['edition']!r} (declared: {sorted(editions) or 'none'})")
        return errors
    caps = set(edition["capabilities"])
    name = f"{vault['tool']} {vault['edition']}"
    if status in USABLE_STATUSES and edition["license_class"] != "osi-open-source" and backend["approval"] != "approved":
        errors.append(f"{where}: {vault['edition']} edition is {edition['license_class']} and not approved")

    # Every capability the profile relies on must be declared by the edition.
    needed = set(vault["required_capabilities"])
    needed.add(VAULT_STORAGE_CAPABILITY[vault["storage_backend"]])
    unseal = vault["unseal"]
    if unseal["method"] == "shamir":
        needed.add("shamir-unseal")
    elif unseal["method"] == "provider-managed":
        needed.add("provider-managed-unseal")
    else:
        needed.add(unseal["method"])
    backup = vault["backup"]
    if backup["enabled"] and "method" in backup:
        needed.add(backup["method"])
    missing = needed - caps
    if missing:
        errors.append(f"{where}: {name} lacks {', '.join(sorted(missing))}")

    # Unseal: auto-unseal needs a key reference (never material); shamir and
    # provider-managed must not carry one.
    key_ref = unseal.get("key_ref")
    if unseal["method"] in AUTO_UNSEAL_METHODS:
        if not key_ref:
            errors.append(f"{where}: unseal method {unseal['method']} needs a key_ref")
        elif unseal["method"] == "auto-unseal-cloud-kms":
            kms = KMS_SCHEMES.get(profile["provider"])
            if kms is None:
                errors.append(f"{where}: auto-unseal-cloud-kms needs a cloud provider's KMS; this profile is {profile['provider']}")
            elif not key_ref.startswith(kms):
                errors.append(f"{where}: unseal key_ref must be a {kms} reference on {profile['provider']}")
        elif unseal["method"] == "auto-unseal-transit" and not key_ref.startswith(tuple(SECRET_SCHEMES.values())):
            errors.append(f"{where}: transit auto-unseal key_ref must reference another secrets backend ({', '.join(SECRET_SCHEMES.values())})")
        elif unseal["method"] == "auto-unseal-pkcs11" and not key_ref.startswith("pkcs11://"):
            errors.append(f"{where}: PKCS#11 auto-unseal key_ref must be a pkcs11:// reference")
        elif unseal["method"] == "auto-unseal-kmip" and not key_ref.startswith("kmip://"):
            errors.append(f"{where}: KMIP auto-unseal key_ref must be a kmip:// reference")
    elif key_ref:
        errors.append(f"{where}: unseal method {unseal['method']} takes no key_ref")

    # Topology: more than one replica needs a spread; production needs 3+.
    topo = vault["topology"]
    if topo["replicas"] > 1 and topo["spread"] == "none":
        errors.append(f"{where}: replicas > 1 need a node or zone spread")
    if profile["production_use"] and topo["replicas"] < 3:
        errors.append(f"{where}: production_use needs at least 3 secrets-backend replicas")

    # Backup/restore and an explicit data-loss statement.
    effect = vault["data_loss_effect"].lower()
    if "unseal" not in effect:
        errors.append(f"{where}: data_loss_effect must state what losing the unseal keys or KMS key means")
    if topo["replicas"] == 1 and "single" not in effect:
        errors.append(f"{where}: one replica, so data_loss_effect must say it is a single point of failure")
    if backup["enabled"]:
        if "method" not in backup or "retention_days" not in backup or "target_ref" not in backup:
            errors.append(f"{where}: an enabled backup needs method, retention_days and target_ref")
        elif not backup["target_ref"].startswith(BACKUP_TARGET_SCHEMES):
            errors.append(f"{where}: backup target_ref must be a storage reference ({', '.join(BACKUP_TARGET_SCHEMES)})")
        if backup.get("method") == "raft-snapshot-manual" and "manual" not in effect:
            errors.append(f"{where}: manual snapshots only, so data_loss_effect must say backups are manual")
        if not backup["restore_tested"]:
            if status in USABLE_STATUSES:
                errors.append(f"{where}: a {status} profile needs a tested secrets-backend restore")
            if "restore" not in effect:
                errors.append(f"{where}: data_loss_effect must say the restore is untested")
    elif "no backup" not in effect:
        errors.append(f"{where}: backup disabled, so data_loss_effect must say 'no backup'")
    elif status in USABLE_STATUSES:
        errors.append(f"{where}: a {status} profile needs secrets-backend backups")
    return errors


def validate_profile(profile: dict, catalog: dict, schema: dict, label: str) -> list[str]:
    """Return a list of errors for one profile (empty means valid)."""
    errors = _schema_errors(profile, schema, label)
    if errors:
        return errors
    errors += _secret_errors(profile, label)
    tools = {t["id"]: t for t in catalog["tools"]}
    status = profile["status"]

    layers = sorted(layer["layer"] for layer in profile["layers"])
    if layers != [0, 1, 2, 3, 4]:
        errors.append(f"{label}: layers must be exactly 0-4, once each; got {layers}")

    app_only = profile.get("deployment_scope", "full-stack") == "applications-only"
    dependencies = profile.get("external_dependencies", [])
    if app_only:
        if profile["provider"] == "on_prem":
            errors.append(f"{label}: applications-only cloud profile needs a cloud provider")
        for layer in profile["layers"]:
            if layer["layer"] < 4 and (layer["state"] != "not-applicable" or layer["path"] is not None):
                errors.append(f"{label}: applications-only Layers 0-3 must be not-applicable with no path")
            if layer["layer"] == 4 and layer["state"] == "not-applicable":
                errors.append(f"{label}: applications-only Layer 4 must be planned or implemented")
        if "packaging" not in profile["tools"] or set(profile["tools"]) - {"packaging", "gitops"}:
            errors.append(f"{label}: applications-only tools may select packaging and gitops only")
        if not profile["vault"].get("managed_externally"):
            errors.append(f"{label}: applications-only secrets backend must be managed_externally")
        if not profile["storage_classes"] or any(not sc.get("managed_externally") for sc in profile["storage_classes"]):
            errors.append(f"{label}: applications-only storage classes must be managed_externally")
        roles = [dep["role"] for dep in dependencies]
        if set(roles) != EXTERNAL_ROLES or len(roles) != len(EXTERNAL_ROLES):
            errors.append(f"{label}: applications-only needs each external dependency role exactly once")
        for dep in dependencies:
            if dep["role"] == "kubernetes" and not KUBERNETES_SECURITY_CAPABILITIES.issubset(
                    dep["required_capabilities"]):
                errors.append(f"{label}: applications-only kubernetes needs network policy, routing, peer authentication and encryption capabilities")
            if dep["readiness"] == "passed" and not dep.get("evidence_ref"):
                errors.append(f"{label}: passed external dependency {dep['role']} needs evidence_ref")
            if status in USABLE_STATUSES and dep["readiness"] != "passed":
                errors.append(f"{label}: a {status} applications-only profile needs passed external dependency {dep['role']}")
    elif dependencies:
        errors.append(f"{label}: external_dependencies require applications-only scope")

    if status == "lab":
        if profile["environment"] != "dev":
            errors.append(f"{label}: a lab profile must use environment dev")
        if profile["production_use"]:
            errors.append(f"{label}: a lab profile cannot be production_use")
    if profile["production_use"]:
        if status != "approved":
            errors.append(f"{label}: production_use requires status approved")
        if profile["tier"] != "high_availability" or profile["ha"]["control_plane_nodes"] < 3 or not profile["ha"]["host_redundancy"]:
            errors.append(f"{label}: production_use requires high_availability, >=3 control-plane nodes and host redundancy")
    if profile["provider"] != "on_prem" and status == "lab":
        errors.append(f"{label}: cloud profiles cannot be lab; they stay planned until verified in a real isolated account")

    passed_runs = [r for r in profile["verification"]["real_environment"] if r["result"] == "passed"]
    if status in USABLE_STATUSES and not passed_runs:
        errors.append(f"{label}: a {status} profile needs at least one passed real-environment verification")
    if status == "approved":
        approval = profile.get("approval")
        if not approval:
            errors.append(f"{label}: an approved profile needs an approval record (plan and review)")
        elif approval["approved_by"] == approval["authored_by"]:
            errors.append(f"{label}: the approver must differ from the author")

    for category, choice in profile["tools"].items():
        errors += _tool_errors(profile, tools, f"{label}: tools.{category}", choice["tool"], choice["version"], {category})

    errors += _vault_errors(profile, tools, label)

    vault = profile["vault"]
    scheme = vault["secret_reference_scheme"]
    kms_scheme = KMS_SCHEMES.get(profile["provider"])
    key_schemes = tuple(s for s in (scheme, kms_scheme) if s)
    for sc in profile["storage_classes"]:
        where = f"{label}: storage {sc['name']}"
        errors += _tool_errors(profile, tools, where, sc["tool"], None, STORAGE_CATEGORIES)
        tool = tools.get(sc["tool"])
        caps = set(tool["capabilities"]) if tool else set()
        missing = set(sc["required_capabilities"]) - caps
        if missing:
            errors.append(f"{where}: {sc['tool']} lacks {', '.join(sorted(missing))}")
        if sc["quota"]["max_per_claim_gi"] > sc["quota"]["max_total_gi"]:
            errors.append(f"{where}: per-claim quota exceeds the total quota")
        enc = sc["encryption"]
        if enc["at_rest"]:
            if "encryption-at-rest" not in caps:
                errors.append(f"{where}: encryption at rest requested but {sc['tool']} does not declare it")
            if not enc.get("key_ref", "").startswith(key_schemes):
                errors.append(f"{where}: encryption key must be a {' or '.join(key_schemes)} reference, never key material")
        if sc["topology"]["replicas"] > 1:
            if sc["topology"]["spread"] == "none":
                errors.append(f"{where}: replicas > 1 need a node or zone spread")
            if "replication" not in caps:
                errors.append(f"{where}: {sc['tool']} does not declare replication")
        effect = sc["data_loss_effect"].lower()
        if sc["reclaim_policy"] == "Delete" and "delet" not in effect:
            errors.append(f"{where}: reclaim Delete must say in data_loss_effect that data is deleted")
        backup = sc["backup"]
        if backup["enabled"]:
            if "tool" not in backup or "retention_days" not in backup:
                errors.append(f"{where}: an enabled backup needs a tool and retention_days")
            else:
                errors += _tool_errors(profile, tools, f"{where}: backup", backup["tool"], None, {"backup"})
            if not backup["restore_tested"] and status in USABLE_STATUSES:
                errors.append(f"{where}: a {status} profile needs a tested restore")
            if not backup["restore_tested"] and "restore" not in effect:
                errors.append(f"{where}: data_loss_effect must say the restore is untested")
        elif "no backup" not in effect:
            errors.append(f"{where}: backup disabled, so data_loss_effect must say 'no backup'")
    return errors


def validate_repository() -> list[str]:
    catalog = load_yaml(CATALOG_PATH)
    errors = validate_catalog(catalog, load_json(CATALOG_SCHEMA))
    if errors:
        return errors
    profile_schema = load_json(PROFILE_SCHEMA)
    profiles = sorted(PROFILES_DIR.glob("*.yaml"))
    if not profiles:
        errors.append("no profiles found in deploy/profiles")
    ids: set[str] = set()
    for path in profiles:
        profile = load_yaml(path)
        label = path.relative_to(REPO).as_posix()
        errors += validate_profile(profile, catalog, profile_schema, label)
        pid = profile.get("profile_id")
        if pid in ids:
            errors.append(f"{label}: duplicate profile_id {pid}")
        ids.add(pid)
        if pid and path.stem != pid:
            errors.append(f"{label}: file name must match profile_id {pid}")
    return errors


def main() -> int:
    errors = validate_repository()
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        print(f"{len(errors)} error(s)")
        return 1
    print("catalog and profiles valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
