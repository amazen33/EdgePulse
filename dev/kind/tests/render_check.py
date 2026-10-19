"""Offline chart renders and restricted-v2 checks; no Kubernetes clients."""
import argparse
import copy
import json
from pathlib import Path
import re
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[3]
CHART = ROOT / "charts/edgepulse-thingsboard"
DIGEST = re.compile(r"^[a-z0-9./-]+(?::[a-zA-Z0-9._-]+)?@sha256:[0-9a-f]{64}$")
ALLOWED = {"Deployment", "Job", "Service", "Cluster"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def memory(value):
    match = re.fullmatch(r"(\d+)(Mi|Gi)", value)
    require(match is not None, "explicit Mi/Gi memory required")
    return int(match[1]) * (1024 if match[2] == "Gi" else 1)


def no_fixed_identity(value):
    if isinstance(value, dict):
        for key, child in value.items():
            require(key not in {"runAsUser", "runAsGroup", "fsGroup", "supplementalGroups",
                                "postgresUID", "postgresGID"}, "fixed identity forbidden")
            no_fixed_identity(child)
    elif isinstance(value, list):
        for child in value:
            no_fixed_identity(child)


def check(documents):
    require(documents, "empty chart")
    for obj in documents:
        require(obj["kind"] in ALLOWED, "cluster scope, Namespace and CRDs forbidden")
        require(obj["metadata"]["namespace"] == "edgepulse-dev", "namespace differs")
        no_fixed_identity(obj)
        spec = obj["spec"]
        if obj["kind"] == "Service":
            require(spec["type"] == "ClusterIP", "external exposure forbidden")
        elif obj["kind"] == "Cluster":
            require(spec["instances"] == 1, "single database instance required")
            require(DIGEST.fullmatch(spec["imageName"]), "database digest missing")
            require(re.search(r":[0-9]+\.[0-9]+[^@]*@sha256:", spec["imageName"]), "CNPG requires the PostgreSQL version tag alongside the digest")
            require(memory(spec["resources"]["limits"]["memory"]) <= 2048, "database budget")
        else:
            if obj["kind"] == "Deployment":
                require(spec["replicas"] == 1, "single TB replica required")
            pod = spec["template"]["spec"]
            require(not any(pod.get(x) for x in ("hostNetwork", "hostPID", "hostIPC")), "host access forbidden")
            require(not any("hostPath" in x for x in pod.get("volumes", [])), "host path forbidden")
            security = pod["securityContext"]
            require(security["runAsNonRoot"] is True, "non-root required")
            require(security["seccompProfile"]["type"] == "RuntimeDefault", "seccomp required")
            require(pod["automountServiceAccountToken"] is False, "unneeded API mount")
            for container in sum((pod.get(k, []) for k in ("containers", "initContainers", "ephemeralContainers")), []):
                sc = container["securityContext"]
                require(sc.get("privileged", False) is False, "privileged forbidden")
                require(sc["allowPrivilegeEscalation"] is False, "escalation forbidden")
                require(sc["runAsNonRoot"] is True, "container non-root required")
                require(sc["capabilities"]["drop"] == ["ALL"] and not sc["capabilities"].get("add"), "drop ALL required")
                require(sc["seccompProfile"]["type"] == "RuntimeDefault", "container seccomp required")
                require(sc["readOnlyRootFilesystem"] is True, "read-only root required")
                require(not any(p.get("hostPort") for p in container.get("ports", [])), "host port forbidden")
                require(DIGEST.fullmatch(container["image"]), "TB digest missing")
                require(memory(container["resources"]["limits"]["memory"]) <= 4096, "TB budget")
                for env in container["env"]:
                    if env["name"] in {"SPRING_DATASOURCE_USERNAME", "SPRING_DATASOURCE_PASSWORD"}:
                        require("value" not in env and "secretKeyRef" in env["valueFrom"], "database reference required")
                    if env["name"] == "TB_QUEUE_TYPE":
                        require(env["value"] == "in-memory", "queue changed")


class NegativeChecks(unittest.TestCase):
    sample = None

    def test_base(self):
        check([self.sample])

    def test_rejects_fixed_uid(self):
        obj = copy.deepcopy(self.sample)
        obj["spec"]["template"]["spec"]["securityContext"]["runAsUser"] = 12345
        with self.assertRaises(ValueError): check([obj])

    def test_rejects_host_access(self):
        for field in ("hostNetwork", "hostPID", "hostIPC"):
            obj = copy.deepcopy(self.sample)
            obj["spec"]["template"]["spec"][field] = True
            with self.subTest(field=field), self.assertRaises(ValueError): check([obj])

    def test_rejects_host_path(self):
        obj = copy.deepcopy(self.sample)
        obj["spec"]["template"]["spec"]["volumes"] = [{"name": "bad", "hostPath": {"path": "/"}}]
        with self.assertRaises(ValueError): check([obj])

    def test_rejects_missing_security(self):
        for field in ("allowPrivilegeEscalation", "runAsNonRoot", "readOnlyRootFilesystem"):
            obj = copy.deepcopy(self.sample)
            obj["spec"]["template"]["spec"]["containers"][0]["securityContext"][field] = not (field != "allowPrivilegeEscalation")
            with self.subTest(field=field), self.assertRaises(ValueError): check([obj])

    def test_rejects_added_capability(self):
        obj = copy.deepcopy(self.sample)
        obj["spec"]["template"]["spec"]["containers"][0]["securityContext"]["capabilities"]["add"] = ["NET_ADMIN"]
        with self.assertRaises(ValueError): check([obj])

    def test_rejects_missing_drop(self):
        obj = copy.deepcopy(self.sample)
        obj["spec"]["template"]["spec"]["containers"][0]["securityContext"]["capabilities"]["drop"] = []
        with self.assertRaises(ValueError): check([obj])

    def test_rejects_seccomp(self):
        obj = copy.deepcopy(self.sample)
        obj["spec"]["template"]["spec"]["containers"][0]["securityContext"]["seccompProfile"]["type"] = "Unconfined"
        with self.assertRaises(ValueError): check([obj])

    def test_rejects_cluster_scope(self):
        for kind in ("Namespace", "CustomResourceDefinition", "ClusterRole", "ClusterRoleBinding"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                check([{"kind": kind, "metadata": {}}])

    def test_rejects_exposure(self):
        for kind in ("NodePort", "LoadBalancer"):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                check([{"kind": "Service", "metadata": {"namespace": "edgepulse-dev"}, "spec": {"type": kind}}])

    def test_rejects_digest_only_database_image(self):
        obj = {"kind": "Cluster", "metadata": {"namespace": "edgepulse-dev"},
               "spec": {"instances": 1, "imageName": "ghcr.io/cloudnative-pg/postgresql@sha256:" + "0" * 64,
                        "resources": {"limits": {"memory": "2Gi"}}}}
        with self.assertRaises(ValueError): check([obj])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--helm", required=True)
    args = parser.parse_args()
    out = ROOT / "target/kind-static"
    out.mkdir(parents=True, exist_ok=True)
    for profile in ("twinfra", "openshift", "kind"):
        values = CHART / f"values-{profile}.yaml"
        subprocess.run([args.helm, "lint", str(CHART), "--strict", "-f", str(values)], check=True)
        for initialize in (False, True):
            extra = ["--set", "bootstrap.enabled=true", "--set", "tb.enabled=false"] if initialize else []
            render = subprocess.check_output([args.helm, "template", "edgepulse", str(CHART), "-n", "edgepulse-dev", "-f", str(values), *extra])
            docs = [d for d in yaml.safe_load_all(render) if d]
            check(docs)
            (out / f"{profile}{'-initialize' if initialize else ''}.yaml").write_bytes(render)
            if not initialize:
                NegativeChecks.sample = next(d for d in docs if d["kind"] == "Deployment")
            print(f"{profile}, {'initialization' if initialize else 'application'}: namespaced/restricted-v2 PASS")
    pins = json.loads((ROOT / "dev/kind/pins.json").read_text(encoding="utf-8"))
    values = yaml.safe_load((CHART / "values.yaml").read_text(encoding="utf-8"))
    require(values["image"] == pins["thingsboard"]["image"], "TB pin differs")
    require(values["database"]["image"] == pins["postgresql"]["image"], "PostgreSQL pin differs")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NegativeChecks)
    require(unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful(), "negative checks failed")


if __name__ == "__main__":
    main()
