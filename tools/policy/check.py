#!/usr/bin/env python3
"""Repository policy checks for AI and device integration boundaries.

Static only: reads files, never calls a model, a device, a broker or a
network. CI tooling, not platform code (the same standing as
deploy/catalog/validate.py); it is not a Python platform service.

    python tools/policy/check.py
    python -m unittest discover -s tools/policy/tests -v

Checks:
  1. docs/inventory/ai-integrations.yaml against
     contracts/ai/ai-integration-profile.schema.json plus cross-field rules:
     AI stays read-only; the constitutional forbidden capabilities are
     declared and no tool can have them; every integration is
     "unimplemented" until contract tests (and, above that, evaluations)
     exist; tenant data does not go to an internet provider whose residency
     or retention is unknown.
  2. docs/inventory/device-classes.yaml against
     contracts/device/device-class-profile.schema.json plus cross-field
     rules: marketing, screenshots and hearsay are not sources; tested
     statuses need listed compatibility tests; tested classes must declare
     acknowledgement, time, unit and replay-protection behaviour; OTA needs
     on-device signature verification; no shared fleet secrets for new
     device classes; credentials only as vault references.
  3. Python stays in its approved areas (ADR 0011 Decision 1: the RAG
     subsystem and standalone adapters; plus the frozen spec and CI tooling).
  4. AI and model-provider SDKs appear only in AI adapter packages
     (Java production sources: .../adapter/out/ai/...; Python:
     rag/**/adapters/...) and never in published contracts. Java test
     sources are skipped: ArchUnit fixtures import SDK stubs on purpose.
  5. No document claims legacy device support while no legacy device class
     is "supported".

Requires PyYAML and jsonschema >= 4.0.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml

REPO = Path(__file__).resolve().parents[2]
AI_INVENTORY = Path("docs/inventory/ai-integrations.yaml")
AI_SCHEMA = Path("contracts/ai/ai-integration-profile.schema.json")
DEVICE_INVENTORY = Path("docs/inventory/device-classes.yaml")
DEVICE_SCHEMA = Path("contracts/device/device-class-profile.schema.json")

# The requirement "AI must never autonomously issue device commands, alter
# rules, approve migrations, or roll out firmware", as capability ids.
CONSTITUTIONAL_FORBIDDEN = {
    "device.command.dispatch",
    "device.property.write",
    "rules.modify",
    "migration.approve",
    "firmware.rollout",
}
# A read tool whose id names a mutating verb is refused even if its effect says "read".
MUTATING_WORDS = re.compile(
    r"(^|[._-])(command|dispatch|write|modify|update|create|delete|approve|rollout|deploy|grant|revoke|apply|execute|pay)([._-]|$)"
)
STATUS_ORDER = ["unimplemented", "contract-tested", "evaluated", "approved"]

REJECTED_SOURCE_TYPES = {"marketing", "screenshot", "hearsay"}
DEVICE_STATUS_ORDER = ["unverified", "documented", "fixture-tested", "device-tested", "supported"]

# Python is allowed only here (ADR 0011 Decision 1 + frozen spec + CI tooling).
PYTHON_ALLOWED_ROOTS = ("spec/", "rag/", "adapters/", "deploy/", "tools/")
SKIP_DIRS = {".git", "target", "__pycache__", ".venv", "node_modules", ".terraform"}

JAVA_AI_SDK_ROOTS = (
    "org.springframework.ai",
    "dev.langchain4j",
    "com.openai",
    "com.anthropic",
    "com.azure.ai",
    "com.google.cloud.vertexai",
    "software.amazon.awssdk.services.bedrock",
    "io.github.ollama4j",
)
PYTHON_AI_SDK_MODULES = ("openai", "anthropic", "langchain", "langchain_core", "langchain_community",
                         "llama_index", "google.cloud.aiplatform", "vertexai", "ollama")
JAVA_AI_ADAPTER_SEGMENT = "/adapter/out/ai/"

LEGACY_CLAIM = re.compile(
    r"\b(supports?|supported|supporting|compatible with|works with)\b[^.\n]{0,40}\blegacy\s+(device|devices|fleet|sensor|sensors|protocols?)\b"
    r"|\blegacy\s+(devices?|fleet|sensors?)\s+(are|is)\s+(fully\s+)?supported\b",
    re.IGNORECASE,
)
NEGATION = re.compile(r"\b(not|no|never|until|unless|cannot|can't|don't|do not|without|claim|claims|claimed)\b",
                      re.IGNORECASE)


class _NoDateLoader(yaml.SafeLoader):
    """Keeps YYYY-MM-DD as strings, matching the JSON Schema 'date' format."""


_NoDateLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(path: Path):
    with path.open(encoding="utf-8") as fh:
        return yaml.load(fh, Loader=_NoDateLoader)  # noqa: S506 -- SafeLoader subclass


def load_json(path: Path):
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _schema_errors(document, schema, label: str) -> list[str]:
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    return [
        f"{label}: schema: {'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path))
    ]


# --------------------------------------------------------------------- AI

def check_ai_inventory(doc: dict, schema: dict, label: str = "ai-integrations") -> list[str]:
    errors = _schema_errors(doc, schema, label)
    if errors:
        return errors
    controls = doc["controls"]
    missing = CONSTITUTIONAL_FORBIDDEN - set(controls["forbidden_capabilities"])
    if missing:
        errors.append(f"{label}: forbidden_capabilities must include {', '.join(sorted(missing))}")
    forbidden = set(controls["forbidden_capabilities"])
    for tool in controls["tool_policy"]["allowed_tools"]:
        tid = tool["tool_id"]
        if tid in forbidden or any(tid.startswith(f + ".") for f in forbidden):
            errors.append(f"{label}: tool {tid} is a forbidden capability")
        if MUTATING_WORDS.search(tid):
            errors.append(f"{label}: tool {tid} names a mutating action; AI tools are read-only")
    if len(set(controls["redaction"]) & {"before-embedding", "before-prompt"}) < 2:
        errors.append(f"{label}: redaction must include before-embedding and before-prompt")

    ids = set()
    for integ in doc["integrations"]:
        where = f"{label}: {integ['integration_id']}"
        if integ["integration_id"] in ids:
            errors.append(f"{where}: duplicate integration_id")
        ids.add(integ["integration_id"])
        status = integ["status"]
        evidence = integ["evidence"]
        if status in STATUS_ORDER:
            rank = STATUS_ORDER.index(status)
            if rank >= 1 and not evidence["contract_tests"]:
                errors.append(f"{where}: status {status} needs contract_tests evidence")
            if rank >= 2 and not evidence["evaluations"]:
                errors.append(f"{where}: status {status} needs evaluation evidence")
            if rank >= 3:
                if integ["model"]["version"] in ("unpinned", ""):
                    errors.append(f"{where}: an approved integration needs a pinned model version")
                for field in ("data_residency", "retention"):
                    if integ[field].strip().lower() in ("unknown", ""):
                        errors.append(f"{where}: an approved integration needs a known {field}")
                if integ["egress"] == "unknown":
                    errors.append(f"{where}: an approved integration needs a known egress")
        if (integ["egress"] == "internet" and "tenant-certified-read-model" in integ["allowed_data_classes"]
                and ("unknown" in (integ["data_residency"].lower(), integ["retention"].lower()))):
            errors.append(f"{where}: certified tenant read models may not go to an internet provider "
                          "with unknown residency or retention")
        if integ["adapter"] == "python-rag" and integ["hosting"] == "public-cloud-api":
            errors.append(f"{where}: the Python RAG agent runs in the deployment's AI cluster; "
                          "a public API provider is reached through its own adapter entry")
    return errors


# ------------------------------------------------------------------ devices

def _rank(status: str) -> int:
    return DEVICE_STATUS_ORDER.index(status) if status in DEVICE_STATUS_ORDER else -1


def check_device_inventory(doc: dict, schema: dict, label: str = "device-classes") -> list[str]:
    errors = _schema_errors(doc, schema, label)
    if errors:
        return errors
    ids = set()
    for dc in doc["device_classes"]:
        where = f"{label}: {dc['class_id']}"
        if dc["class_id"] in ids:
            errors.append(f"{where}: duplicate class_id")
        ids.add(dc["class_id"])
        status = dc["status"]
        rank = _rank(status)
        accepted = [s for s in dc["sources"] if s["type"] not in REJECTED_SOURCE_TYPES]
        for source in dc["sources"]:
            if source["type"] in REJECTED_SOURCE_TYPES:
                errors.append(f"{where}: {source['type']} is not an accepted source ({source['reference']})")
        if rank >= 1 and not accepted:
            errors.append(f"{where}: status {status} needs at least one accepted source")
        if rank >= 2 and not dc["compatibility_tests"]:
            errors.append(f"{where}: status {status} needs passing compatibility_tests")
        if status == "supported" and not any(t["state"] == "device-tested" for t in dc["transports"]):
            errors.append(f"{where}: supported needs at least one device-tested transport")
        for transport in dc["transports"]:
            if transport["state"] == "device-tested" and rank < 3:
                errors.append(f"{where}: a device-tested transport needs class status device-tested or better")
            if transport["state"] == "fixture-tested" and rank < 2:
                errors.append(f"{where}: a fixture-tested transport needs class status fixture-tested or better")

        auth = dc["authentication"]
        if auth["credential_kind"] == "shared-fleet-secret" and dc["generation"] != "legacy":
            errors.append(f"{where}: shared fleet secrets are not allowed for new device classes; use per-device credentials")
        if auth["credential_kind"] not in ("none", "unknown") and auth["credential_storage"] != "vault-reference":
            errors.append(f"{where}: device credentials must be vault references")
        if isinstance(auth["per_device"], str) and auth["per_device"] != "unknown":
            errors.append(f"{where}: per_device must be true, false or 'unknown'")

        fw = dc["firmware"]
        if fw["ota"] == "supported" and fw["on_device_signature_verification"] != "yes":
            errors.append(f"{where}: OTA needs on-device signature verification")
        if fw["ota"] == "supported" and not fw["compatibility_keys"]:
            errors.append(f"{where}: OTA needs compatibility_keys (for example hardware revision)")

        if rank >= 2:
            if dc["commands"]["supported"] == "yes" and dc["commands"]["acknowledgement"] in ("unknown",):
                errors.append(f"{where}: a tested class that accepts commands must declare its acknowledgement")
            if dc["time"]["timestamp_source"] == "unknown" or dc["time"]["clock"] == "unknown":
                errors.append(f"{where}: a tested class must declare its clock and timestamp source")
            if any(u["conversion"] == "unknown" or u["canonical_unit"] == "unknown" for u in dc["units"]):
                errors.append(f"{where}: a tested class must map every metric to a canonical unit")
            if dc["offline_buffer"]["message_id"] in ("none", "unknown"):
                errors.append(f"{where}: a tested class needs a message id or sequence for dedupe and replay prevention")
            if any(t["protocol"] == "unknown" for t in dc["transports"]):
                errors.append(f"{where}: a tested class cannot have an unknown transport")
    return errors


# ---------------------------------------------------------- repository scans

def _walk(repo: Path, suffixes: tuple[str, ...]):
    for path in repo.rglob("*"):
        if not path.is_file() or path.suffix not in suffixes:
            continue
        rel = path.relative_to(repo)
        if SKIP_DIRS.intersection(rel.parts):
            continue
        yield path, rel.as_posix()


def check_python_scope(repo: Path) -> list[str]:
    return [
        f"{rel}: Python outside the approved areas ({', '.join(PYTHON_ALLOWED_ROOTS)}); "
        "ADR 0011 Decision 1 limits Python to the RAG subsystem and standalone adapters -- a new area needs a new ADR"
        for _, rel in _walk(repo, (".py",))
        if not rel.startswith(PYTHON_ALLOWED_ROOTS)
    ]


_JAVA_IMPORT = re.compile(r"^\s*import\s+(static\s+)?([\w.]+)", re.MULTILINE)
_PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE)


def check_ai_sdk_scope(repo: Path) -> list[str]:
    errors = []
    for path, rel in _walk(repo, (".java",)):
        if "/src/main/" not in "/" + rel:
            continue  # test fixtures deliberately import SDK stubs to prove ArchUnit rules fire
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in _JAVA_IMPORT.finditer(text):
            name = match.group(2)
            if name.startswith(JAVA_AI_SDK_ROOTS) and JAVA_AI_ADAPTER_SEGMENT not in "/" + rel:
                errors.append(f"{rel}: imports {name}; AI/provider SDKs (including Spring AI) belong only in "
                              "an adapter/out/ai package")
    for path, rel in _walk(repo, (".py",)):
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in _PY_IMPORT.finditer(text):
            name = match.group(1) or match.group(2)
            top_hit = any(name == m or name.startswith(m + ".") for m in PYTHON_AI_SDK_MODULES)
            if top_hit and not (rel.startswith("rag/") and "/adapters/" in rel):
                errors.append(f"{rel}: imports {name}; model-provider SDKs belong only in rag/**/adapters/")
    contracts = repo / "contracts"
    if contracts.exists():
        for path in contracts.rglob("*"):
            if not path.is_file() or path.suffix not in (".proto", ".json", ".yaml", ".yml"):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for root in JAVA_AI_SDK_ROOTS:
                if root in text:
                    errors.append(f"{path.relative_to(repo).as_posix()}: published contract names {root}; "
                                  "contracts must stay provider-neutral")
    return errors


def check_legacy_claims(repo: Path, device_doc: dict) -> list[str]:
    if any(dc["generation"] == "legacy" and dc["status"] == "supported" for dc in device_doc.get("device_classes", [])):
        return []
    errors = []
    for path, rel in _walk(repo, (".md",)):
        if rel.startswith("spec/"):
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if LEGACY_CLAIM.search(line) and not NEGATION.search(line):
                errors.append(f"{rel}:{lineno}: claims legacy device support, but no legacy device class is "
                              "'supported' in docs/inventory/device-classes.yaml")
    return errors


# ------------------------------------------------------------------- driver

def run(repo: Path = REPO) -> list[str]:
    errors = []
    ai_doc = load_yaml(repo / AI_INVENTORY)
    errors += check_ai_inventory(ai_doc, load_json(repo / AI_SCHEMA))
    device_doc = load_yaml(repo / DEVICE_INVENTORY)
    errors += check_device_inventory(device_doc, load_json(repo / DEVICE_SCHEMA))
    errors += check_python_scope(repo)
    errors += check_ai_sdk_scope(repo)
    errors += check_legacy_claims(repo, device_doc)
    return errors


def main() -> int:
    errors = run()
    for error in errors:
        print(f"ERROR {error}")
    if errors:
        print(f"{len(errors)} error(s)")
        return 1
    print("AI and device policy checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
