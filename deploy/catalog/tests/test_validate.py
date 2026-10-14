"""Negative and positive tests for deploy/catalog/validate.py.

Each test starts from the real repository catalog and lab profile, plants
exactly one violation, and asserts the validator reports it. Run:

    python -m unittest discover -s deploy/catalog/tests -v
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate  # noqa: E402

CATALOG = validate.load_yaml(validate.CATALOG_PATH)
CATALOG_SCHEMA = validate.load_json(validate.CATALOG_SCHEMA)
PROFILE_SCHEMA = validate.load_json(validate.PROFILE_SCHEMA)
LAB = validate.load_yaml(validate.PROFILES_DIR / "lab-hyperv-single-host.yaml")
CLOUD = validate.load_yaml(validate.PROFILES_DIR / "cloud-aws-eks.yaml")
APP_ONLY = validate.load_yaml(validate.PROFILES_DIR / "cloud-aws-eks-app-only.yaml")


def tool(catalog, tool_id):
    return next(t for t in catalog["tools"] if t["id"] == tool_id)


class RepositoryIsValid(unittest.TestCase):
    def test_repository_catalog_and_profiles_pass(self):
        self.assertEqual(validate.validate_repository(), [])


class CatalogRules(unittest.TestCase):
    def errors(self, catalog):
        return "\n".join(validate.validate_catalog(catalog, CATALOG_SCHEMA))

    def test_default_must_be_osi_open_source(self):
        cat = copy.deepcopy(CATALOG)
        tool(cat, "hashicorp-vault")["role"] = "default"
        tool(cat, "hashicorp-vault")["default_status"] = "proposed"
        self.assertIn("a default must be OSI open source", self.errors(cat))

    def test_approved_requires_all_checks_passed(self):
        cat = copy.deepcopy(CATALOG)
        tool(cat, "rke2")["approval"] = "approved"
        self.assertIn("approved but checks not passed", self.errors(cat))

    def test_only_one_default_per_category(self):
        cat = copy.deepcopy(CATALOG)
        tool(cat, "flux")["role"] = "default"
        tool(cat, "flux")["default_status"] = "proposed"
        self.assertIn("more than one default", self.errors(cat))

    def test_passed_licence_check_needs_a_source(self):
        cat = copy.deepcopy(CATALOG)
        tool(cat, "helm")["checks"]["license"] = {"status": "passed"}
        self.assertIn("without a source or note", self.errors(cat))

    def test_rejected_tool_cannot_be_approved(self):
        cat = copy.deepcopy(CATALOG)
        tool(cat, "minio")["approval"] = "candidate"
        self.assertIn("rejected tool must be not-approved", self.errors(cat))


class ProfileRules(unittest.TestCase):
    def errors(self, profile, catalog=CATALOG):
        return "\n".join(validate.validate_profile(profile, catalog, PROFILE_SCHEMA, "test"))

    def test_application_only_profile_declares_external_dependencies(self):
        self.assertEqual(self.errors(APP_ONLY), "")

    def test_application_only_cannot_install_platform_layers(self):
        p = copy.deepcopy(APP_ONLY)
        p["layers"][2].update({"state": "planned", "path": "deploy/02-cluster-addons"})
        self.assertIn("Layers 0-3 must be not-applicable", self.errors(p))

    def test_application_only_requires_every_external_dependency_once(self):
        p = copy.deepcopy(APP_ONLY)
        p["external_dependencies"] = [d for d in p["external_dependencies"] if d["role"] != "identity"]
        self.assertIn("each external dependency role exactly once", self.errors(p))

    def test_application_only_requires_network_security_capabilities(self):
        p = copy.deepcopy(APP_ONLY)
        p["external_dependencies"][0]["required_capabilities"] = ["kubernetes-api"]
        self.assertIn("needs network policy, routing, peer authentication and encryption", self.errors(p))

    def test_application_only_cannot_select_infrastructure_tools(self):
        p = copy.deepcopy(APP_ONLY)
        p["tools"]["iac-provisioning"] = {"tool": "opentofu", "version": "unpinned"}
        self.assertIn("may select packaging and gitops only", self.errors(p))

    def test_application_only_requires_external_vault_and_storage(self):
        p = copy.deepcopy(APP_ONLY)
        p["vault"]["managed_externally"] = False
        p["storage_classes"][0]["managed_externally"] = False
        out = self.errors(p)
        self.assertIn("secrets backend must be managed_externally", out)
        self.assertIn("storage classes must be managed_externally", out)

    def test_application_only_passed_dependency_needs_evidence(self):
        p = copy.deepcopy(APP_ONLY)
        p["external_dependencies"][0]["readiness"] = "passed"
        self.assertIn("needs evidence_ref", self.errors(p))

    def test_application_only_cannot_be_validated_with_pending_dependencies(self):
        p = copy.deepcopy(APP_ONLY)
        p["status"] = "validated"
        self.assertIn("needs passed external dependency", self.errors(p))

    def test_unknown_tool_rejected(self):
        p = copy.deepcopy(LAB)
        p["tools"]["gateway"] = {"tool": "made-up-gateway", "version": "unpinned"}
        self.assertIn("not in the tool catalog", self.errors(p))

    def test_rejected_tool_cannot_be_selected(self):
        p = copy.deepcopy(LAB)
        p["storage_classes"][0]["tool"] = "minio"
        self.assertIn("cannot be selected by a profile", self.errors(p))

    def test_unlicensed_optional_compatibility_tool_rejected(self):
        p = copy.deepcopy(LAB)
        p["tools"]["iac-provisioning"] = {"tool": "terraform", "version": "unpinned"}
        self.assertIn("licence not accepted", self.errors(p))

    def test_version_must_be_pinned_in_catalog(self):
        p = copy.deepcopy(LAB)
        p["tools"]["kubernetes-distribution"]["version"] = "v9.9.9"
        self.assertIn("is not a catalog version", self.errors(p))

    def test_validated_profile_needs_approved_tools_evidence_and_pins(self):
        p = copy.deepcopy(CLOUD)
        p["status"] = "validated"
        out = self.errors(p)
        self.assertIn("may only select approved tools", out)
        self.assertIn("passed real-environment verification", out)
        self.assertIn("only lab or planned profiles may select an unpinned tool", out)

    def test_cloud_profile_cannot_be_lab(self):
        p = copy.deepcopy(CLOUD)
        p["status"] = "lab"
        p["environment"] = "dev"
        self.assertIn("cloud profiles cannot be lab", self.errors(p))

    def test_lab_profile_cannot_be_production(self):
        p = copy.deepcopy(LAB)
        p["production_use"] = True
        out = self.errors(p)
        self.assertIn("lab profile cannot be production_use", out)
        self.assertIn("production_use requires high_availability", out)

    def test_approved_profile_needs_distinct_system_admin_approver(self):
        p = copy.deepcopy(LAB)
        p["status"] = "approved"
        p["environment"] = "staging"
        p["approval"] = {"plan_ref": "plan-1", "authored_by": "alice", "approved_by": "alice",
                         "approved_by_role": "system-admin", "approved_on": "2026-09-26"}
        self.assertIn("approver must differ from the author", self.errors(p))
        p["approval"]["approved_by_role"] = "tenant-admin"
        self.assertIn("approved_by_role", self.errors(p))

    def test_spring_vault_is_not_a_secrets_backend(self):
        p = copy.deepcopy(LAB)
        p["vault"]["tool"] = "spring-vault"
        self.assertIn("is a secrets-client tool, expected secrets-backend", self.errors(p))

    def test_vault_edition_capabilities_are_explicit(self):
        p = copy.deepcopy(LAB)
        p["vault"]["required_capabilities"].append("performance-replication")
        self.assertIn("openbao community lacks performance-replication", self.errors(p))

    def test_hashicorp_vault_community_has_no_namespaces(self):
        cat = copy.deepcopy(CATALOG)
        tool(cat, "hashicorp-vault")["approval"] = "approved"  # isolate the capability rule
        p = copy.deepcopy(LAB)
        p["vault"].update({"tool": "hashicorp-vault", "edition": "community", "secret_reference_scheme": "vault://"})
        p["vault"]["required_capabilities"].append("namespaces")
        self.assertIn("hashicorp-vault community lacks namespaces", self.errors(p, cat))

    def test_automated_snapshots_are_not_assumed(self):
        p = copy.deepcopy(LAB)
        p["vault"]["backup"]["method"] = "raft-snapshot-automated"
        self.assertIn("openbao community lacks raft-snapshot-automated", self.errors(p))

    def test_provider_managed_storage_is_an_edition_capability(self):
        p = copy.deepcopy(LAB)
        p["vault"]["storage_backend"] = "provider-managed"
        self.assertIn("lacks provider-managed-storage", self.errors(p))

    def test_auto_unseal_needs_a_key_reference(self):
        p = copy.deepcopy(CLOUD)
        del p["vault"]["unseal"]["key_ref"]
        self.assertIn("needs a key_ref", self.errors(p))

    def test_cloud_kms_unseal_must_use_the_profiles_provider(self):
        p = copy.deepcopy(CLOUD)
        p["vault"]["unseal"]["key_ref"] = "gcpckms://other/keyrings/x/keys/y"
        self.assertIn("must be a awskms:// reference on aws", self.errors(p))

    def test_on_prem_has_no_cloud_kms_unseal(self):
        p = copy.deepcopy(LAB)
        p["vault"]["unseal"] = {"method": "auto-unseal-cloud-kms", "key_ref": "awskms://alias/x", "custody": "someone holds it"}
        self.assertIn("needs a cloud provider's KMS", self.errors(p))

    def test_shamir_takes_no_key_reference(self):
        p = copy.deepcopy(LAB)
        p["vault"]["unseal"]["key_ref"] = "openbao://kv/unseal"
        self.assertIn("takes no key_ref", self.errors(p))

    def test_pkcs11_seal_is_enterprise_only_for_hashicorp_vault(self):
        cat = copy.deepcopy(CATALOG)
        tool(cat, "hashicorp-vault")["approval"] = "approved"
        p = copy.deepcopy(LAB)
        p["vault"].update({"tool": "hashicorp-vault", "edition": "community", "secret_reference_scheme": "vault://"})
        p["vault"]["unseal"] = {"method": "auto-unseal-pkcs11", "key_ref": "pkcs11://hsm/slot0/unseal", "custody": "HSM admins"}
        self.assertIn("lacks auto-unseal-pkcs11", self.errors(p, cat))

    def test_vault_data_loss_must_cover_unseal_keys_and_single_replica(self):
        p = copy.deepcopy(LAB)
        p["vault"]["data_loss_effect"] = "Snapshots are manual and restore has never been tested."
        out = self.errors(p)
        self.assertIn("losing the unseal keys", out)
        self.assertIn("single point of failure", out)

    def test_vault_missing_backup_must_be_stated(self):
        p = copy.deepcopy(LAB)
        p["vault"]["backup"] = {"enabled": False, "restore_tested": False}
        self.assertIn("must say 'no backup'", self.errors(p))

    def test_vault_untested_restore_must_be_stated(self):
        p = copy.deepcopy(LAB)
        p["vault"]["data_loss_effect"] = "Single replica. Losing the unseal key shares loses everything; manual snapshots."
        self.assertIn("restore is untested", self.errors(p))

    def test_vault_replicas_need_spread(self):
        p = copy.deepcopy(LAB)
        p["vault"]["topology"] = {"replicas": 3, "spread": "none"}
        self.assertIn("replicas > 1 need a node or zone spread", self.errors(p))

    def test_validated_profile_needs_tested_vault_restore(self):
        p = copy.deepcopy(CLOUD)
        p["status"] = "validated"
        self.assertIn("needs a tested secrets-backend restore", self.errors(p))

    def test_cloud_storage_key_must_use_the_providers_kms(self):
        p = copy.deepcopy(CLOUD)
        p["storage_classes"][0]["encryption"]["key_ref"] = "azurekeyvault://kv/keys/x"
        self.assertIn("must be a openbao:// or awskms:// reference", self.errors(p))

    def test_hashicorp_vault_is_optional_compatibility_until_licence_accepted(self):
        p = copy.deepcopy(LAB)
        p["vault"].update({"tool": "hashicorp-vault", "edition": "enterprise", "secret_reference_scheme": "vault://"})
        self.assertIn("licence not accepted", self.errors(p))

    def test_storage_key_must_be_a_reference(self):
        p = copy.deepcopy(LAB)
        p["storage_classes"][0]["encryption"]["key_ref"] = "c2VjcmV0LWtleS1tYXRlcmlhbA=="
        self.assertIn("must be a openbao:// reference", self.errors(p))

    def test_storage_capabilities_are_validated(self):
        p = copy.deepcopy(LAB)
        p["storage_classes"][1]["required_capabilities"].append("snapshots")
        self.assertIn("local-path-provisioner lacks snapshots", self.errors(p))

    def test_encryption_requires_a_capable_tool(self):
        p = copy.deepcopy(LAB)
        p["storage_classes"][1]["encryption"] = {"at_rest": True, "key_ref": "openbao://kv/x"}
        self.assertIn("does not declare it", self.errors(p))

    def test_delete_reclaim_must_state_data_loss(self):
        p = copy.deepcopy(LAB)
        p["storage_classes"][1]["data_loss_effect"] = "Scratch space for experiments, no backup."
        self.assertIn("reclaim Delete must say", self.errors(p))

    def test_missing_backup_must_be_stated(self):
        p = copy.deepcopy(LAB)
        p["storage_classes"][1]["data_loss_effect"] = "Deleting the claim deletes the data permanently."
        self.assertIn("must say 'no backup'", self.errors(p))

    def test_quota_is_consistent(self):
        p = copy.deepcopy(LAB)
        p["storage_classes"][0]["quota"] = {"max_total_gi": 10, "max_per_claim_gi": 50}
        self.assertIn("per-claim quota exceeds", self.errors(p))

    def test_replicas_need_spread_and_replication(self):
        p = copy.deepcopy(LAB)
        p["storage_classes"][1]["topology"] = {"replicas": 3, "spread": "none"}
        out = self.errors(p)
        self.assertIn("need a node or zone spread", out)
        self.assertIn("does not declare replication", out)

    def test_no_free_form_command_field(self):
        p = copy.deepcopy(LAB)
        p["run"] = "ansible all -m shell -a 'rm -rf /'"
        self.assertIn("Additional properties are not allowed", self.errors(p))

    def test_secret_material_is_rejected(self):
        p = copy.deepcopy(LAB)
        p["limitations"].append("token: abcdef123456")
        self.assertIn("looks like secret material", self.errors(p))

    def test_layers_must_be_zero_to_four(self):
        p = copy.deepcopy(LAB)
        p["layers"][4]["layer"] = 3
        self.assertIn("layers must be exactly 0-4", self.errors(p))


if __name__ == "__main__":
    unittest.main()
