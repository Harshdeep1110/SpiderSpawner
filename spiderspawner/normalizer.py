from urllib.parse import urlparse, urljoin, parse_qsl

def is_same_domain(base_url: str, target_url: str) -> bool:
    """Check if the target URL is on the same domain as the base URL."""
    base_host = urlparse(base_url).netloc
    target_host = urlparse(target_url).netloc
    return not target_host or base_host == target_host

def normalize_urls(raw_urls: set, base_url: str) -> tuple[set, set]:
    """
    Normalizes extracted URLs.
    Returns a tuple of (paths, params).
    """
    paths = set()
    params = set()

    for raw in raw_urls:
        if not raw:
            continue
            
        # Ignore unsupported schemes
        if raw.lower().startswith(('javascript:', 'mailto:', 'data:')):
            continue
            
        # Strip fragments
        if '#' in raw:
            raw = raw.split('#')[0]
            
        if not raw:
            continue

        # Resolve relative URLs
        full_url = urljoin(base_url, raw)

        # Discard cross-domain URLs
        if not is_same_domain(base_url, full_url):
            continue

        parsed = urlparse(full_url)
        
        # Add path
        path = parsed.path
        if path:
            path = path.strip('/')
            if path:
                paths.add(path)
                
        # Add query parameters
        if parsed.query:
            for k, _ in parse_qsl(parsed.query, keep_blank_values=True):
                if k:
                    params.add(k)

    return paths, params
