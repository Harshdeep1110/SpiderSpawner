import argparse
import sys
from .fetcher import fetch_html, fetch_all_js, probe_sourcemap
from .extractor import extract_html_data
from .jsscanner import scan_js_chunked, MAX_JS_BYTES
from .normalizer import normalize_urls
from .reporter import write_json_report
from .utils import filter_and_sort_words

def parse_args():
    parser = argparse.ArgumentParser(description="Spider Spawner - Context-Aware Wordlist Generator")
    parser.add_argument("target_url", help="Target URL to scrape")
    parser.add_argument("-o", "--output", default="wordlist.txt", help="Output wordlist path")
    parser.add_argument("-j", "--json", help="Also write JSON extraction report")
    parser.add_argument("-c", "--cookies", help="Cookie header string")
    parser.add_argument("-H", "--header", action="append", help="Additional header KEY:VAL")
    parser.add_argument("-k", "--keywords", action="store_true", help="Include visible text keywords")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Request timeout (sec)")
    parser.add_argument("--no-external-js", action="store_true", help="Skip external JS files")
    parser.add_argument("--min-len", type=int, default=2, help="Minimum word length")
    parser.add_argument("--max-len", type=int, default=80, help="Maximum word length")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--max-js-size", type=int, default=MAX_JS_BYTES, help="Max JS file size in bytes")
    parser.add_argument("--js-concurrency", type=int, default=10, help="Max concurrent JS requests")
    return parser.parse_args()

def main():
    args = parse_args()
    
    extra_headers = {}
    if args.header:
        for h in args.header:
            if ":" in h:
                k, v = h.split(":", 1)
                extra_headers[k.strip()] = v.strip()

    print(f"[*] Fetching HTML from {args.target_url}")
    try:
        html = fetch_html(args.target_url, args.cookies, extra_headers, args.timeout)
    except Exception as e:
        print(f"[!] Failed to fetch target: {e}", file=sys.stderr)
        sys.exit(1)

    print("[*] Extracting HTML data")
    html_data = extract_html_data(html, extract_keywords=args.keywords)
    
    # Inline JS scan
    inline_js_words = set()
    for js_text in html_data["inline_js"]:
        inline_js_words |= scan_js_chunked(js_text, args.max_js_size)

    # External JS fetch and scan
    external_js_words = set()
    if not args.no_external_js and html_data["external_js_urls"]:
        js_urls = list(html_data["external_js_urls"])
        # Resolve to absolute URLs first
        from urllib.parse import urljoin
        abs_js_urls = [urljoin(args.target_url, u) for u in js_urls]
        
        print(f"[*] Fetching {len(abs_js_urls)} external JS files")
        fetched_js = fetch_all_js(abs_js_urls, args.js_concurrency)
        
        for js_url, source in fetched_js.items():
            print(f"[*] Scanning {js_url}")
            # Try sourcemap first
            smap_source = probe_sourcemap(js_url, args.cookies, extra_headers)
            if smap_source:
                print(f"  -> Found sourcemap")
                source = smap_source
                
            external_js_words |= scan_js_chunked(source, args.max_js_size)

    # Normalize URLs
    paths, params = normalize_urls(html_data["links"], args.target_url)

    # Union all words
    all_words = paths | params | html_data["forms"] | inline_js_words | external_js_words | html_data["keywords"]
    
    # Filter and sort
    final_list = filter_and_sort_words(all_words, args.min_len, args.max_len)
    
    print(f"[+] {len(final_list)} words extracted -> {args.output}")
    with open(args.output, "w", encoding="utf-8") as f:
        for w in final_list:
            f.write(w + "\n")
            
    if args.json:
        sources_dict = {
            "hrefs": list(paths),
            "form_fields": list(html_data["forms"] | params),
            "inline_js": list(inline_js_words),
            "external_js": list(external_js_words),
            "keywords": list(html_data["keywords"])
        }
        write_json_report(args.json, args.target_url, sources_dict, len(final_list))
        print(f"[+] Report written to {args.json}")
        
    print(f"\n[+] Run: ffuf -w {args.output} -u {args.target_url.rstrip('/')}/FUZZ -mc 200,301,302,403 -t 40")

if __name__ == "__main__":
    main()
