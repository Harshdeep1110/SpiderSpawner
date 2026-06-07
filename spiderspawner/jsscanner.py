import re
import sys

MINIFIED_THRESHOLD = 0.005  # newlines per char
MAX_JS_BYTES = 2 * 1024 * 1024  # 2MB default
CHUNK_SIZE = 512 * 1024
OVERLAP_BYTES = 200

# Tier 1: minification-safe
T1_PATTERNS = [
    re.compile(r'["\'](\/[\w\/\-_.?=&%]{2,})["\']'),  # path literals
    re.compile(r'["\']([a-zA-Z_][a-zA-Z0-9_]{2,30})["\']:\s'),  # JSON keys
    re.compile(r'path=["\'](\/[^"\' ]{1,120})["\']')  # JSX routes
]

# Tier 2: readable source only
T2_PATTERNS = [
    re.compile(r'(?:var|let|const)\s+(\w*[Uu][Rr][Ll]\w*)'),
    re.compile(r'(?:var|let|const)\s+([a-zA-Z_$][\w$]{2,30})'),
]

def is_minified(js_text: str) -> bool:
    if not js_text:
        return False
    ratio = js_text.count("\n") / max(1, len(js_text))
    return ratio < MINIFIED_THRESHOLD

def scan_js_chunked(js_text: str, max_bytes: int = MAX_JS_BYTES) -> set:
    if len(js_text.encode("utf-8", errors="replace")) > max_bytes:
        print(f"[!] JS file exceeds {max_bytes//1024}KB cap — skipped", file=sys.stderr)
        return set()

    words = set()
    minified = is_minified(js_text)
    patterns = T1_PATTERNS if minified else T1_PATTERNS + T2_PATTERNS

    if minified:
        print("[!] Minified JS detected — variable name extraction skipped", file=sys.stderr)

    encoded = js_text.encode("utf-8", errors="replace")
    i = 0
    while i < len(encoded):
        chunk = encoded[i : i + CHUNK_SIZE + OVERLAP_BYTES].decode("utf-8", errors="replace")
        for pat in patterns:
            words.update(pat.findall(chunk))
        i += CHUNK_SIZE

    return words
