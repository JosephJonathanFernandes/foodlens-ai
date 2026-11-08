"""Phase 6: Report and translation endpoint tests + error handling tests."""

import json
import urllib.request
import urllib.error

BASE = "http://localhost:8000"


def req(method, path, data=None, files=None):
    url = BASE + path
    headers = {}
    body = None
    if files:
        boundary = "----FoodLensBoundary"
        body = b""
        for f in files:
            body += f"--{boundary}\r\n".encode()
            body += f'Content-Disposition: form-data; name="files"; filename="{f["name"]}"\r\n'.encode()
            body += f"Content-Type: {f['type']}\r\n\r\n".encode()
            body += f["data"] + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif isinstance(data, dict):
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        raw = resp.read().decode()
        return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"_raw": raw[:300]}


passed = 0
failed = 0


def check(condition, msg):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {msg}")
    else:
        failed += 1
        print(f"  FAIL: {msg}")


print("=" * 60)
print("PHASE 6: REPORT & TRANSLATION TESTS")
print("=" * 60)

# First create a scan
img_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
st, body = req("POST", "/api/scan/upload", files=[{"name": "test.jpg", "type": "image/jpeg", "data": img_bytes}])
check(st == 200, "Upload for report test returns 200")
scan_id = body.get("id")

# Process it
st, body = req("POST", "/api/scan/process", {"scan_id": scan_id, "language": "en"})
check(st == 200, "Process for report test returns 200")

# ---- Full report endpoint ----
print("\n--- Full Report ---")
st, body = req("GET", f"/api/scan/report/{scan_id}")
check(st == 200, f"Full report returns 200 (got {st})")
check("scan_id" in body, "Report has scan_id")
check("product_name" in body, "Report has product_name")
check("brand" in body, "Report has brand")
check("images" in body, "Report has images")
check("language" in body, "Report has language")

# Report for non-existent scan
st, body = req("GET", "/api/scan/report/nonexistent")
check(st == 404, "Report for non-existent scan returns 404")

# ---- Translate report endpoint ----
print("\n--- Translate Report ---")
st, body = req("POST", f"/api/scan/translate/report?scan_id={scan_id}&target_language=hi")
check(st == 200, f"Translate report returns 200 (got {st})")
check(body.get("language") == "hi", "Translated report has Hindi language")
check("warnings" in body, "Translated report has warnings")

# Translate report to English (no-op)
st, body = req("POST", f"/api/scan/translate/report?scan_id={scan_id}&target_language=en")
check(st == 200, "Translate report to English returns 200")

# Translate report non-existent scan
st, body = req("POST", "/api/scan/translate/report?scan_id=nonexistent&target_language=hi")
check(st == 404, "Translate report for non-existent scan returns 404")

# ---- Scan image endpoints ----
print("\n--- Scan Sub-resources ---")
# Ingredients
st, body = req("GET", f"/api/scan/{scan_id}/ingredients")
check(st == 200, "Scan ingredients endpoint returns 200")
check(isinstance(body, list), "Scan ingredients returns a list")

# Nutrition
st, body = req("GET", f"/api/scan/{scan_id}/nutrition")
check(st == 200, "Scan nutrition endpoint returns 200")
check(isinstance(body, list), "Scan nutrition returns a list")

# Allergens
st, body = req("GET", f"/api/scan/{scan_id}/allergens")
check(st == 200, "Scan allergens endpoint returns 200")
check(isinstance(body, list), "Scan allergens returns a list")

# Claims
st, body = req("GET", f"/api/scan/{scan_id}/claims")
check(st == 200, "Scan claims endpoint returns 200")
check(isinstance(body, list), "Scan claims returns a list")

# ---- Error handling tests ----
print("\n--- Error Handling ---")

# Malformed JSON
r = urllib.request.Request(BASE + "/api/scan/process", data=b"not json", headers={"Content-Type": "application/json"}, method="POST")
try:
    resp = urllib.request.urlopen(r)
    check(resp.status == 200, "Malformed JSON handled gracefully")
except urllib.error.HTTPError as e:
    check(e.code in (400, 422), f"Malformed JSON returns error status (got {e.code})")

# Missing required fields
st, body = req("POST", "/api/scan/process", {"language": "en"})
check(st in (400, 422), "Process without scan_id returns error")

st, body = req("POST", "/api/translate", {"text": "Hello"})
check(st in (400, 422), "Translate without target_language returns error")

# Unknown endpoint
st, body = req("GET", "/api/unknown")
check(st == 404, "Unknown endpoint returns 404")

# OCR endpoint for scan
st, body = req("GET", f"/api/scan/{scan_id}/ocr")
check(st == 200, "OCR endpoint returns 200")
check(isinstance(body, list), "OCR endpoint returns a list")

print()
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL PHASE 6 REPORT & TRANSLATION TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    exit(1)
