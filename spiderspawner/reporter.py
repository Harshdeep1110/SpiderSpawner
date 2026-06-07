import json
from datetime import datetime, timezone

def write_json_report(filepath: str, target: str, sources: dict, total_words: int):
    report = {
        "target": target,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_words": total_words,
        "sources": sources
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
