import re
from bs4 import BeautifulSoup

def extract_html_data(html_content: str, extract_keywords: bool = False) -> dict:
    """
    Parses HTML to extract links, form fields, inline JS, external JS URLs,
    and optionally visible keywords.
    Returns a dictionary of sets.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    
    data = {
        "links": set(),
        "forms": set(),
        "inline_js": set(),
        "external_js_urls": set(),
        "keywords": set()
    }

    # M1: Link extraction
    for tag in soup.find_all(['a', 'link']):
        href = tag.get('href')
        if href:
            data["links"].add(href)
            
    for tag in soup.find_all(['img', 'script', 'iframe', 'source']):
        src = tag.get('src')
        if src:
            data["links"].add(src)
            if tag.name == 'script':
                data["external_js_urls"].add(src)
                
    for tag in soup.find_all('form'):
        action = tag.get('action')
        if action:
            data["links"].add(action)

    # M2: Form analysis
    for tag in soup.find_all(['input', 'textarea', 'select']):
        name = tag.get('name')
        if name:
            data["forms"].add(name)
        if tag.name == 'input' and tag.get('type') == 'hidden':
            val = tag.get('value')
            if val:
                data["forms"].add(val)

    # M3: Inline JS collection
    for tag in soup.find_all('script'):
        if not tag.get('src') and tag.string:
            data["inline_js"].add(tag.string)

    # M5: Keyword extraction
    if extract_keywords:
        text = soup.get_text(separator=' ')
        # Simple tokenization: alphanumeric words
        words = re.findall(r'[a-zA-Z0-9_]+', text)
        data["keywords"].update(words)

    return data
