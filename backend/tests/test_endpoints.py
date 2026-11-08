"""Phase 6: Comprehensive API endpoint tests."""

import io
import json
import urllib.request
import urllib.error
from PIL import Image, ImageDraw

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


def make_label_image(text_lines):
    """Create a simple test label image."""
    img = Image.new("RGB", (400, 600), color="white")
    d = ImageDraw.Draw(img)
    y = 20
    for line in text_lines:
        d.text((20, y), line, fill="black")
        y += 30
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


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
print("PHASE 6: API ENDPOINT TESTS")
print("=" * 60)

# ---- Health ----
print("\n--- Health ---")
st, body = req("GET", "/api/health")
check(st == 200, "Health returns 200")
check(body.get("status") == "ok", "Health status is ok")

# ---- Upload ----
print("\n--- Upload ---")
img_bytes = make_label_image(["Test Product", "Brand: TestCo"])
st, body = req("POST", "/api/scan/upload", files=[{"name": "test.jpg", "type": "image/jpeg", "data": img_bytes}])
check(st == 200, f"Upload returns 200 (got {st})")
check("id" in body, "Upload returns scan id")
scan_id = body.get("id")
check("images" in body and len(body["images"]) == 1, "Upload returns 1 image")
check(body["status"] == "idle", "Upload status is idle")

# Upload no files
st, body = req("POST", "/api/scan/upload")
check(st in (400, 422), "Upload with no files returns error")

# ---- Process ----
print("\n--- Process ---")
st, body = req("POST", "/api/scan/process", {"scan_id": scan_id, "language": "en"})
check(st == 200, f"Process returns 200 (got {st})")
check(body.get("status") == "completed", "Process status is completed")
check("report_id" in body, "Process returns report_id")

# Process non-existent scan
st, body = req("POST", "/api/scan/process", {"scan_id": "nonexistent-id", "language": "en"})
check(st == 404, "Process non-existent scan returns 404")

# ---- Get scan ----
print("\n--- Get Scan ---")
st, body = req("GET", f"/api/scan/{scan_id}")
check(st == 200, f"Get scan returns 200 (got {st})")
check(body.get("id") == scan_id, "Get scan returns correct id")
check("images" in body, "Get scan returns images")
check(len(body["images"]) == 1, "Get scan has 1 image")

# Get non-existent scan
st, body = req("GET", "/api/scan/nonexistent")
check(st == 404, "Get non-existent scan returns 404")

# ---- History ----
print("\n--- History ---")
st, body = req("GET", "/api/scan/history")
check(st == 200, "History returns 200")
check(isinstance(body, list), "History returns a list")
check(len(body) >= 1, "History has at least 1 scan")

# ---- Translate ----
print("\n--- Translate ---")
st, body = req("POST", "/api/translate", {"text": "Hello world", "target_language": "hi", "source_language": "en"})
check(st == 200, "Translate returns 200")
check("translated_text" in body, "Translate returns translated_text")
check("target_language" in body, "Translate returns target_language")

# Translate same language
st, body = req("POST", "/api/translate", {"text": "Hello", "target_language": "en", "source_language": "en"})
check(st == 200, "Translate same language returns 200")
check(body.get("translated_text") == "Hello", "Same language returns original text")

# ---- Ingredient lookup ----
print("\n--- Ingredient Lookup ---")
st, body = req("GET", "/api/ingredients/sodium_benzoate")
check(st == 200, "Ingredient lookup returns 200")
check(body.get("name") == "Sodium Benzoate", "Ingredient lookup returns correct name")
check(body.get("ins_number") == "211", "Ingredient lookup returns INS number")

# Ingredient not found
st, body = req("GET", "/api/ingredients/nonexistent_ingredient")
check(st == 404, "Ingredient lookup not found returns 404")

# ---- Compare ----
print("\n--- Compare ---")
# Upload second scan for comparison
img_bytes_b = make_label_image(["Product B", "Brand: BrandB"])
st, body_b = req("POST", "/api/scan/upload", files=[{"name": "b.jpg", "type": "image/jpeg", "data": img_bytes_b}])
scan_b = body_b.get("id")
st, body = req("POST", "/api/scan/process", {"scan_id": scan_b, "language": "en"})
check(st == 200, "Process second scan returns 200")

st, body = req("POST", "/api/compare", {"scan_id_a": scan_id, "scan_id_b": scan_b})
check(st == 200, f"Compare returns 200 (got {st})")
check("comparison" in body, "Compare returns comparison data")
check("scan_id_a" in body, "Compare returns scan_id_a")
check("scan_id_b" in body, "Compare returns scan_id_b")

# Compare non-existent
st, body = req("POST", "/api/compare", {"scan_id_a": "nonexistent", "scan_id_b": scan_b})
check(st == 404, "Compare non-existent scan returns 404")

# ---- Delete scan ----
print("\n--- Delete Scan ---")
st, body = req("DELETE", f"/api/scan/{scan_b}")
check(st == 200, f"Delete scan returns 200 (got {st})")
check(body.get("detail") == "Scan deleted", "Delete returns success detail")

# Verify deletion
st, body = req("GET", f"/api/scan/{scan_b}")
check(st == 404, "Deleted scan returns 404")

print()
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("ALL PHASE 6 API TESTS PASSED")
else:
    print("SOME TESTS FAILED")
    exit(1)
