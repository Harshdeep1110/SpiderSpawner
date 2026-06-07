import asyncio
import aiohttp
import requests
import json
import sys

HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/120"}

def fetch_html(url: str, cookies: str = None, extra_headers: dict = None, timeout: int = 10) -> str:
    s = requests.Session()
    s.headers.update(HEADERS)
    if extra_headers:
        s.headers.update(extra_headers)
    if cookies:
        s.headers["Cookie"] = cookies
    r = s.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

async def _fetch_one(session: aiohttp.ClientSession, url: str):
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
            return url, await r.text()
    except Exception as e:
        print(f"[!] JS fetch failed: {url} — {e}", file=sys.stderr)
        return url, ""

async def _fetch_all_async(urls: list[str], concurrency: int = 10) -> dict[str, str]:
    sem = asyncio.Semaphore(concurrency)
    
    async def bounded(url):
        async with sem:
            return await _fetch_one(session, url)
            
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        results = await asyncio.gather(*[bounded(u) for u in urls])
        return {url: text for url, text in results if text}

def fetch_all_js(urls: list[str], concurrency: int = 10) -> dict[str, str]:
    """Blocking wrapper — call from sync code."""
    if not urls:
        return {}
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(_fetch_all_async(urls, concurrency))

def probe_sourcemap(js_url: str, cookies: str = None, extra_headers: dict = None) -> str:
    map_url = js_url + ".map"
    try:
        raw = fetch_html(map_url, cookies, extra_headers, timeout=5)
        data = json.loads(raw)
        sources = data.get("sourcesContent", [])
        return "\n".join(s for s in sources if s)
    except Exception:
        return None
