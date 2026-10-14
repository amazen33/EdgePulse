"""Tests for deploy/checks/static_guards.py.

The repository must pass every guard; each negative test builds a minimal
throw-away tree in a temporary directory and plants exactly one violation.

    python -m unittest discover -s deploy/checks/tests -v
"""
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import static_guards as g  # noqa: E402

GOOD_CFG = """\
[defaults]
inventory = inventory/hosts.ini
roles_path = roles
"""
GOOD_INVENTORY = """\
[rke2_server]
rke2-master-01 ansible_host=192.0.2.10
[rke2_agent]
rke2-worker-01 ansible_host=198.51.100.21
"""
GOOD_PROFILE = """\
profile_id: p
layers:
  - {layer: 3, path: deploy/03-observability, state: planned, static_checks: []}
  - {layer: 4, path: deploy/04-apps, state: planned, static_checks: []}
"""


class Tree:
    """A minimal repository layout that passes every guard."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.write("deploy/01-k8s-engine/rke2-ansible/ansible.cfg", GOOD_CFG)
        self.write("deploy/01-k8s-engine/rke2-ansible/inventory/hosts.example.ini", GOOD_INVENTORY)
        self.write("deploy/01-k8s-engine/rke2-ansible/README.md",
                   "ansible-playbook -i inventory/hosts.ini site-rke2.yml --limit rke2-worker-01\n")
        self.write("deploy/03-observability/README.md", "Planned.\n")
        self.write("deploy/04-apps/README.md", "Planned: no Helm chart exists.\n")
        self.write("deploy/profiles/p.yaml", GOOD_PROFILE)

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")

    def errors(self):
        return "\n".join(g.run(self.root))

    def close(self):
        self._tmp.cleanup()


class RepositoryPasses(unittest.TestCase):
    def test_repository_passes_every_guard(self):
        self.assertEqual(g.run(), [])


class Guards(unittest.TestCase):
    def setUp(self):
        self.tree = Tree()
        self.addCleanup(self.tree.close)

    def test_baseline_tree_is_clean(self):
        self.assertEqual(self.tree.errors(), "")

    def test_ansible_cfg_rejects_node_addresses(self):
        self.tree.write("deploy/01-k8s-engine/rke2-ansible/ansible.cfg", GOOD_CFG + "[ssh_connection]\nssh_args = -o ProxyJump=10.20.0.1\n")
        self.assertIn("must not contain node addresses", self.tree.errors())

    def test_ansible_cfg_rejects_inline_host_list(self):
        self.tree.write("deploy/01-k8s-engine/rke2-ansible/ansible.cfg", "[defaults]\ninventory = master-01,worker-01,\n")
        self.assertIn("inline host lists are not allowed", self.tree.errors())

    def test_ansible_cfg_rejects_host_variables(self):
        self.tree.write("deploy/01-k8s-engine/rke2-ansible/ansible.cfg", GOOD_CFG + "# ok in a comment: ansible_host\nx = ansible_host\n")
        self.assertIn("must not define hosts or groups", self.tree.errors())

    def test_ansible_cfg_comments_may_mention_addresses(self):
        self.tree.write("deploy/01-k8s-engine/rke2-ansible/ansible.cfg", GOOD_CFG + "# never put 10.20.0.10 here\n")
        self.assertEqual(self.tree.errors(), "")

    def test_committed_inventory_must_use_documentation_addresses(self):
        self.tree.write("deploy/01-k8s-engine/rke2-ansible/inventory/hosts.example.ini",
                        GOOD_INVENTORY + "rke2-worker-02 ansible_host=10.20.0.22\n")
        self.assertIn("10.20.0.22 is not an RFC 5737 documentation address", self.tree.errors())

    def test_committed_group_vars_must_use_documentation_addresses(self):
        self.tree.write("deploy/01-k8s-engine/rke2-ansible/inventory/group_vars/all/main.yml",
                        "rke2_tls_san: ['172.16.5.4']\n")
        self.assertIn("172.16.5.4 is not an RFC 5737", self.tree.errors())

    def test_local_inventory_files_are_not_scanned(self):
        # git-ignored; kept out of Git by .gitignore and the CI ls-files check
        self.tree.write("deploy/01-k8s-engine/rke2-ansible/inventory/hosts.ini", "m ansible_host=10.20.0.10\n")
        self.tree.write("deploy/01-k8s-engine/rke2-ansible/inventory/host_vars/m.yml", "x: 10.20.0.10\n")
        self.assertEqual(self.tree.errors(), "")

    def test_extra_vars_in_documented_commands_rejected(self):
        self.tree.write("deploy/01-k8s-engine/rke2-ansible/README.md",
                        "ansible-playbook -i inventory/hosts.ini heal.yml -e heal_confirm=yes\n")
        self.assertIn("-e/--extra-vars", self.tree.errors())

    def test_long_form_extra_vars_rejected(self):
        self.tree.write(".github/workflows/infra.yml",
                        "run: ansible-playbook site-rke2.yml --extra-vars '@override.yml'\n")
        self.assertIn("-e/--extra-vars", self.tree.errors())

    def test_readme_must_admit_there_is_no_chart(self):
        self.tree.write("deploy/04-apps/README.md", "Helm charts deploy every service.\n")
        self.assertIn("must say there is no Helm chart", self.tree.errors())

    def test_readme_must_not_deny_existing_charts(self):
        self.tree.write("deploy/04-apps/identity/Chart.yaml", "apiVersion: v2\nname: identity\nversion: 0.1.0\n")
        self.assertIn("says there is no Helm chart", self.tree.errors())

    def test_profile_cannot_mark_empty_layer_implemented(self):
        self.tree.write("deploy/profiles/p.yaml", GOOD_PROFILE.replace(
            "path: deploy/03-observability, state: planned", "path: deploy/03-observability, state: implemented"))
        self.assertIn("layer 3 is marked implemented but deploy/03-observability has no artifacts", self.tree.errors())

    def test_profile_cannot_mark_layer4_implemented_without_charts(self):
        self.tree.write("deploy/04-apps/argocd/app.yaml", "kind: Application\n")
        self.tree.write("deploy/profiles/p.yaml", GOOD_PROFILE.replace(
            "path: deploy/04-apps, state: planned", "path: deploy/04-apps, state: implemented"))
        self.assertIn("layer 4 is marked implemented but no Helm chart exists", self.tree.errors())


if __name__ == "__main__":
    unittest.main()
