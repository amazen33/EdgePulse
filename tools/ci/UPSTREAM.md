# Twinfra supply-chain port (IOT-WO-02 Part B)

Source: [amazen33/twinfra](https://github.com/amazen33/twinfra), commit `0d950075a8bf43358d9fd406b80b67d657f804e1`.
Read through `git show origin/main:<path>` only; the Twinfra working tree is untouched.
The first port commit copies these files byte for byte. EdgePulse wiring is a separate commit.

| Path | SHA-256 |
| --- | --- |
| `tools/ci/supply_chain.py` | `6e117cc750133d55ae603023d19a925d4838ac5fd8f9445bff350a2e26bd378b` |
| `tools/ci/supply_chain_report.py` | `4178341641e7de019208cd82962672af731828468aa7a3a9e67c523cb21b59fa` |
| `tools/ci/supply_chain_watch.py` | `14ee92be1c80702f6665ab1f17623578822aa2de337bc1cbeebfd7b8f09bf089` |
| `security/vulnerability-exceptions.schema.json` | `10760668d3e618f70c21ff7ee73940aeec78f3e26bd41ef6a52e52377a5f6dba` |
| `.github/workflows/supply-chain.yaml` | `8af93aa9ecd8013a8491d434b9de596edb3106b5f2e909bf244cb9ee9ca8300f` |
| `.github/workflows/supply-chain-tools.yaml` | `46268a39fa0284b09715149c2159738fc3a526c6b5f46eb9cb9ae3e7dd8b4960` |
| `tools/ci/tests/test_supply_chain.py` | `c4fa756b5df5758e1f6f67f3de3e130ae9ddc6df4aaedb11d3161a1be930153c` |
| `tools/ci/tests/test_supply_chain_watch.py` | `958684e4c0d42707e6df0be0ee431b05880f9b431054b1e9f13c701a99c99cb5` |
| `tools/ci/stage_tools.py` | `752ba886b384b4a1d90ee75a0478e0b6bf2e5a4b42ca57026626d2260d0ee4f0` |
| `tools/ci/toolchain_wave.py` | `9bb668a14f06a9d662a7c606328e56a7833e5323cf7f573fb90260d2da88d13d` |
| `tools/ci/check_tool_sbom.py` | `2c94d02567fe0fdbece02b0e75893e8d9884aaa33ec1714bbf6095d01fdeff5c` |
| `tools/ci/requirements.txt` | `cf261469f6b21804b350964739f1b8db7c8810f99e9c57c4a90bd6f14eab65ea` |

The upstream MIT notice is preserved in [security/UPSTREAM-LICENSE.txt](../../security/UPSTREAM-LICENSE.txt).
`security/vulnerability-exceptions.json` starts empty; no upstream exceptions are imported.
No upstream runtime or infrastructure configuration is copied.
