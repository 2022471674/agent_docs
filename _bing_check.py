# -*- coding: utf-8 -*-
"""Verify BingSiteAuth.xml is served at the site root by the running 4000 server."""
import urllib.request, hashlib, os

ROOT = r"D:\Ai-Agent渗透测试\workspace"
SRC = os.path.join(ROOT, "BingSiteAuth.xml")
URL = "http://localhost:4000/BingSiteAuth.xml"


def sha(b):
    return hashlib.sha256(b).hexdigest()


with open(SRC, "rb") as f:
    expected = f.read()

print("source_file:", SRC)
print("source_size:", len(expected), "source_sha256:", sha(expected))
print("target_url :", URL)
print("=" * 70)
try:
    req = urllib.request.Request(URL, headers={"User-Agent": "hexo-bing-verify/1.0"})
    with urllib.request.urlopen(req, timeout=12) as r:
        body = r.read()
        status = r.status
        ctype = r.headers.get("Content-Type", "")
        print("HTTP status :", status)
        print("Content-Type:", ctype)
        print("body_size   :", len(body))
        print("body_sha256 :", sha(body))
        print("body_equals_source =", body == expected)
        print("\n---- response body ----")
        print(body.decode("utf-8", "replace"))
        print("---- end ----")
        ok = (status == 200 and body == expected)
        print("\nRESULT:", "PASS - reachable at root, byte-identical" if ok else "FAIL")
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.reason)
    print("RESULT: FAIL - not reachable (HTTP %s)" % e.code)
except Exception as e:
    print("Network error:", type(e).__name__, str(e))
    print("RESULT: FAIL - server not reachable")
