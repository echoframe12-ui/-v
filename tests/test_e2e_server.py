import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error


def wait_for(url, timeout=10.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False


def http_post(url, data, headers=None):
    b = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=b, method="POST")
    req.add_header("Content-Type", "application/json")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read()
            return resp.getcode(), json.loads(body or b"{}")
    except urllib.error.HTTPError as e:
        body = e.read()
        try:
            return e.code, json.loads(body or b"{}")
        except Exception:
            return e.code, {"error": "http-error", "message": str(e)}


def test_e2e_server_plugin_flow(tmp_path):
    port = 5060
    url_base = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["API_KEY"] = "test-key"

    # Start server subprocess
    cmd = [sys.executable, "-c", "from app import app; app.run(port=%d)" % port]
    proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert wait_for(f"{url_base}/health", timeout=10.0), "server did not start in time"

        headers = {"X-API-Key": "test-key"}

        # register plugin
        code, j = http_post(f"{url_base}/plugins", {"name": "mem_e2e_test", "builtin": True, "builtin_name": "memory_inmem"}, headers)
        assert code == 200
        assert j.get("registered") is True

        # store
        code, j = http_post(
            f"{url_base}/tools/mem_e2e_test",
            {"action": "store", "entry": {"text": "e2e test", "source": "pytest"}},
            headers,
        )
        assert code == 200
        assert j.get("result") and j["result"].get("id") == 1

        # query
        code, j = http_post(f"{url_base}/tools/mem_e2e_test", {"action": "query", "term": "e2e"}, headers)
        assert code == 200
        assert isinstance(j.get("result"), list) and len(j["result"]) >= 1

        # delete
        req = urllib.request.Request(f"{url_base}/plugins/mem_e2e_test", method="DELETE")
        req.add_header("X-API-Key", "test-key")
        with urllib.request.urlopen(req) as resp:
            assert resp.getcode() == 200
            body = json.loads(resp.read() or b"{}")
            assert body.get("unregistered") is True

        # invoke after delete should give 404
        code, j = http_post(f"{url_base}/tools/mem_e2e_test", {"action": "query", "term": "e2e"}, headers)
        assert code == 404

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        # drain outputs
        try:
            proc.stdout and proc.stdout.read()
            proc.stderr and proc.stderr.read()
        except Exception:
            pass
