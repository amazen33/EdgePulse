"""Tests for tools/policy/check.py.

The repository must pass; each negative test starts from the real
inventories (or a throw-away tree) and plants exactly one violation.

    python -m unittest discover -s tools/policy/tests -v
"""
import copy
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check  # noqa: E402

REPO = check.REPO
AI = check.load_yaml(REPO / check.AI_INVENTORY)
AI_SCHEMA = check.load_json(REPO / check.AI_SCHEMA)
DEV = check.load_yaml(REPO / check.DEVICE_INVENTORY)
DEV_SCHEMA = check.load_json(REPO / check.DEVICE_SCHEMA)


def integration(doc, integration_id):
    return next(i for i in doc["integrations"] if i["integration_id"] == integration_id)


def device_class(doc, class_id):
    return next(d for d in doc["device_classes"] if d["class_id"] == class_id)


class RepositoryPasses(unittest.TestCase):
    def test_repository_passes_every_check(self):
        self.assertEqual(check.run(), [])

    def test_every_ai_integration_is_unimplemented_until_tested(self):
        for integ in AI["integrations"]:
            self.assertEqual("unimplemented", integ["status"], integ["integration_id"])

    def test_the_legacy_fleet_is_unverified_and_fully_unknown(self):
        legacy = device_class(DEV, "spectrotank-legacy-fleet")
        self.assertEqual("unverified", legacy["status"])
        self.assertEqual([], legacy["sources"])
        self.assertEqual("unknown", legacy["transports"][0]["protocol"])


class AiRules(unittest.TestCase):
    def errors(self, doc):
        return "\n".join(check.check_ai_inventory(doc, AI_SCHEMA))

    def test_ai_mode_must_be_read_only(self):
        doc = copy.deepcopy(AI)
        doc["controls"]["mode"] = "act"
        self.assertIn("controls/mode", self.errors(doc))

    def test_constitutional_forbidden_capabilities_must_be_declared(self):
        doc = copy.deepcopy(AI)
        doc["controls"]["forbidden_capabilities"].remove("firmware.rollout")
        self.assertIn("must include firmware.rollout", self.errors(doc))

    def test_a_tool_cannot_have_a_forbidden_capability(self):
        doc = copy.deepcopy(AI)
        doc["controls"]["tool_policy"]["allowed_tools"].append(
            {"tool_id": "device.command.dispatch", "effect": "read", "owner_service": "devices", "state": "unimplemented"})
        out = self.errors(doc)
        self.assertIn("is a forbidden capability", out)
        self.assertIn("names a mutating action", out)

    def test_a_tool_named_for_a_mutation_is_refused_even_if_marked_read(self):
        for tool_id in ("rules.chain.update", "migration.plan.approve", "firmware.ring.rollout", "config.apply"):
            doc = copy.deepcopy(AI)
            doc["controls"]["tool_policy"]["allowed_tools"].append(
                {"tool_id": tool_id, "effect": "read", "owner_service": "x", "state": "unimplemented"})
            self.assertIn("names a mutating action", self.errors(doc), tool_id)

    def test_a_tool_with_a_write_effect_is_rejected_by_the_contract(self):
        doc = copy.deepcopy(AI)
        doc["controls"]["tool_policy"]["allowed_tools"][0]["effect"] = "write"
        self.assertIn("allowed_tools/0/effect", self.errors(doc))

    def test_mandatory_controls_cannot_be_switched_off(self):
        for path, value in ((("tenant_authorized_retrieval",), False), (("source_attribution",), "optional"),
                            (("failure_isolation",), "fail-closed-platform"),
                            (("tool_policy", "audited"), False), (("rate_and_cost_limits", "per_tenant"), False)):
            doc = copy.deepcopy(AI)
            target = doc["controls"]
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            self.assertIn("schema", self.errors(doc), path)

    def test_redaction_before_embedding_and_prompt_is_required(self):
        doc = copy.deepcopy(AI)
        doc["controls"]["redaction"] = ["before-embedding", "on-output"]
        self.assertIn("must include before-embedding and before-prompt", self.errors(doc))

    def test_retrieval_only_from_certified_or_redacted_sources(self):
        doc = copy.deepcopy(AI)
        doc["controls"]["retrieval_sources"].append("raw-telemetry")
        self.assertIn("retrieval_sources", self.errors(doc))

    def test_status_above_unimplemented_needs_evidence(self):
        doc = copy.deepcopy(AI)
        integration(doc, "azure-openai")["status"] = "contract-tested"
        self.assertIn("needs contract_tests evidence", self.errors(doc))
        integration(doc, "azure-openai")["status"] = "evaluated"
        integration(doc, "azure-openai")["evidence"]["contract_tests"] = ["ai-contract/azure-openai"]
        self.assertIn("needs evaluation evidence", self.errors(doc))

    def test_approval_needs_a_pinned_model_and_known_residency_retention_egress(self):
        doc = copy.deepcopy(AI)
        target = integration(doc, "azure-openai")
        target["status"] = "approved"
        target["evidence"] = {"contract_tests": ["c"], "evaluations": ["e"]}
        out = self.errors(doc)
        self.assertIn("pinned model version", out)
        self.assertIn("known data_residency", out)
        self.assertIn("known retention", out)

    def test_certified_read_models_never_go_to_an_internet_provider_with_unknown_terms(self):
        doc = copy.deepcopy(AI)
        integration(doc, "aws-bedrock")["allowed_data_classes"].append("tenant-certified-read-model")
        self.assertIn("may not go to an internet provider", self.errors(doc))

    def test_unknown_adapter_kinds_are_rejected(self):
        doc = copy.deepcopy(AI)
        integration(doc, "anthropic-api")["adapter"] = "python-service"
        self.assertIn("adapter", self.errors(doc))

    def test_no_executable_or_secret_fields(self):
        doc = copy.deepcopy(AI)
        integration(doc, "anthropic-api")["api_key"] = "not-a-real-key"
        self.assertIn("Additional properties are not allowed", self.errors(doc))


class DeviceRules(unittest.TestCase):
    def errors(self, doc):
        return "\n".join(check.check_device_inventory(doc, DEV_SCHEMA))

    def test_marketing_and_screenshots_are_not_sources(self):
        for kind in ("marketing", "screenshot", "hearsay"):
            doc = copy.deepcopy(DEV)
            device_class(doc, "spectrotank-legacy-fleet")["sources"].append({"type": kind, "reference": "product page"})
            self.assertIn(f"{kind} is not an accepted source", self.errors(doc))

    def test_a_marketing_source_does_not_lift_a_class_out_of_unverified(self):
        doc = copy.deepcopy(DEV)
        legacy = device_class(doc, "spectrotank-legacy-fleet")
        legacy["sources"] = [{"type": "marketing", "reference": "product page"}]
        legacy["status"] = "documented"
        self.assertIn("needs at least one accepted source", self.errors(doc))

    def test_legacy_support_needs_representative_compatibility_tests(self):
        doc = copy.deepcopy(DEV)
        legacy = device_class(doc, "spectrotank-legacy-fleet")
        legacy["sources"] = [{"type": "authorized-protocol-capture", "reference": "capture-001"}]
        legacy["status"] = "supported"
        out = self.errors(doc)
        self.assertIn("needs passing compatibility_tests", out)
        self.assertIn("needs at least one device-tested transport", out)

    def test_tested_classes_must_declare_ack_time_units_and_replay_keys(self):
        doc = copy.deepcopy(DEV)
        legacy = device_class(doc, "spectrotank-legacy-fleet")
        legacy["sources"] = [{"type": "authorized-protocol-capture", "reference": "capture-001"}]
        legacy["status"] = "fixture-tested"
        legacy["compatibility_tests"] = ["device-compat/legacy-capture-001"]
        legacy["commands"]["supported"] = "yes"
        out = self.errors(doc)
        self.assertIn("must declare its acknowledgement", out)
        self.assertIn("must declare its clock and timestamp source", out)
        self.assertIn("must map every metric to a canonical unit", out)
        self.assertIn("needs a message id or sequence", out)
        self.assertIn("cannot have an unknown transport", out)

    def test_ota_needs_on_device_signature_verification_and_compatibility_keys(self):
        doc = copy.deepcopy(DEV)
        ref = device_class(doc, "platform-reference-mqtt")
        ref["firmware"]["on_device_signature_verification"] = "no"
        ref["firmware"]["compatibility_keys"] = []
        out = self.errors(doc)
        self.assertIn("OTA needs on-device signature verification", out)
        self.assertIn("OTA needs compatibility_keys", out)

    def test_new_device_classes_cannot_use_shared_fleet_secrets(self):
        doc = copy.deepcopy(DEV)
        device_class(doc, "platform-reference-mqtt")["authentication"]["credential_kind"] = "shared-fleet-secret"
        self.assertIn("shared fleet secrets are not allowed", self.errors(doc))

    def test_credentials_are_only_vault_references(self):
        doc = copy.deepcopy(DEV)
        device_class(doc, "platform-reference-mqtt")["authentication"]["credential_storage"] = "database"
        self.assertIn("credential_storage", self.errors(doc))

    def test_a_device_tested_transport_needs_a_device_tested_class(self):
        doc = copy.deepcopy(DEV)
        device_class(doc, "platform-reference-mqtt")["transports"][0]["state"] = "device-tested"
        self.assertIn("a device-tested transport needs class status", self.errors(doc))

    def test_unknown_protocol_names_are_rejected(self):
        doc = copy.deepcopy(DEV)
        device_class(doc, "platform-reference-mqtt")["transports"][0]["protocol"] = "lorawan-magic"
        self.assertIn("protocol", self.errors(doc))


class Tree:
    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")

    def close(self):
        self._tmp.cleanup()


class RepositoryScans(unittest.TestCase):
    def setUp(self):
        self.tree = Tree()
        self.addCleanup(self.tree.close)

    def test_python_outside_approved_areas_is_rejected(self):
        self.tree.write("services/assistant/app.py", "print('x')\n")
        self.tree.write("rag/agent/main.py", "print('ok')\n")
        self.tree.write("spec/x.py", "print('ok')\n")
        errors = check.check_python_scope(self.tree.root)
        self.assertEqual(1, len(errors))
        self.assertIn("services/assistant/app.py", errors[0])

    def test_spring_ai_outside_an_ai_adapter_is_rejected(self):
        self.tree.write("services/assistant/src/main/java/com/iotee/platform/assistant/application/Answer.java",
                        "package x;\nimport org.springframework.ai.chat.client.ChatClient;\n")
        self.tree.write("services/assistant/src/main/java/com/iotee/platform/assistant/adapter/out/ai/springai/Model.java",
                        "package x;\nimport org.springframework.ai.chat.client.ChatClient;\n")
        errors = check.check_ai_sdk_scope(self.tree.root)
        self.assertEqual(1, len(errors))
        self.assertIn("application/Answer.java", errors[0])

    def test_java_test_fixtures_are_not_scanned(self):
        self.tree.write("services/identity/src/test/java/com/iotee/platform/identity/architecture/fixtures/V.java",
                        "package x;\nimport org.springframework.ai.FakeChatClient;\n")
        self.assertEqual([], check.check_ai_sdk_scope(self.tree.root))

    def test_provider_sdks_outside_an_ai_adapter_are_rejected(self):
        for imp in ("com.openai.client.OpenAIClient", "com.anthropic.client.AnthropicClient",
                    "dev.langchain4j.model.chat.ChatModel",
                    "software.amazon.awssdk.services.bedrockruntime.BedrockRuntimeClient"):
            tree = Tree()
            try:
                tree.write("services/x/src/main/java/com/iotee/platform/x/domain/A.java", f"package x;\nimport {imp};\n")
                self.assertTrue(check.check_ai_sdk_scope(tree.root), imp)
            finally:
                tree.close()

    def test_python_provider_sdks_only_in_rag_adapters(self):
        self.tree.write("rag/agent/retrieval.py", "import openai\n")
        self.tree.write("rag/agent/adapters/openai_model.py", "from openai import OpenAI\n")
        errors = check.check_ai_sdk_scope(self.tree.root)
        self.assertEqual(1, len(errors))
        self.assertIn("rag/agent/retrieval.py", errors[0])

    def test_published_contracts_stay_provider_neutral(self):
        self.tree.write("contracts/ai/v1/assistant.proto", "// uses org.springframework.ai.chat.model.ChatResponse\n")
        self.assertIn("contracts must stay provider-neutral", "\n".join(check.check_ai_sdk_scope(self.tree.root)))

    def test_legacy_device_claims_are_rejected_until_a_legacy_class_is_supported(self):
        self.tree.write("README.md", "The platform supports legacy devices over any protocol.\n")
        self.tree.write("docs/a.md", "Do not claim it supports legacy devices until tests pass.\n")
        errors = check.check_legacy_claims(self.tree.root, DEV)
        self.assertEqual(1, len(errors))
        self.assertIn("README.md:1", errors[0])

        supported = copy.deepcopy(DEV)
        device_class(supported, "spectrotank-legacy-fleet")["status"] = "supported"
        self.assertEqual([], check.check_legacy_claims(self.tree.root, supported))

    def test_other_legacy_claim_phrasings_are_caught(self):
        self.tree.write("docs/b.md", "Legacy devices are fully supported.\nCompatible with legacy sensors today.\n")
        self.assertEqual(2, len(check.check_legacy_claims(self.tree.root, DEV)))


if __name__ == "__main__":
    unittest.main()
