#!/usr/bin/env python3
import json
import re
from pathlib import Path
from urllib import request
from bs4 import BeautifulSoup

root = Path(__file__).resolve().parent.parent
prompt = (root / 'bash.md').read_text(encoding='utf-8', errors='ignore')

sys_msg = (
    "Execute NOcron Step 2 (Mock UI). Return JSON only with keys html, components, rationale_short. "
    "html must be complete single-page HTML/CSS/JS representing the architecture from user input."
)

payload = {
    'model': 'gemma4:26b',
    'messages': [
        {'role': 'system', 'content': sys_msg},
        {'role': 'user', 'content': prompt},
    ],
    'format': 'json',
    'stream': False,
    'options': {'temperature': 0.1, 'num_predict': 4096},
}

req = request.Request(
    'http://localhost:11434/api/chat',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST',
)
resp = request.urlopen(req, timeout=240)
raw = json.loads(resp.read().decode('utf-8'))['message']['content']
(root / 'step2_raw.txt').write_text(raw, encoding='utf-8')

# strict parse
obj = json.loads(raw)

html = obj.get('html') or '<!doctype html><html><body><h1>No html returned</h1></body></html>'
(root / 'mock.html').write_text(html, encoding='utf-8')
(root / 'step2.json').write_text(json.dumps(obj, indent=2), encoding='utf-8')

# Step 3 realignment parse
soup = BeautifulSoup(html, 'html.parser')
buttons = [x.get_text(strip=True) for x in soup.find_all('button') if x.get_text(strip=True)]
inputs = [x.get('placeholder', '').strip() for x in soup.find_all(['input', 'textarea']) if (x.get('placeholder') or '').strip()]
headings = [x.get_text(strip=True) for x in soup.find_all(['h1', 'h2', 'h3']) if x.get_text(strip=True)]
labels = [x.get_text(strip=True) for x in soup.find_all('label') if x.get_text(strip=True)]

features = []
seen = set()
for txt in headings + buttons + labels + inputs:
    t = re.sub(r'\s+', ' ', txt).strip()
    if t and t.lower() not in seen:
        seen.add(t.lower())
        features.append(t)

source_l = prompt.lower()
def token_hit(feature: str) -> bool:
    toks = [t for t in re.split(r'[^a-z0-9]+', feature.lower()) if len(t) > 4]
    return any(t in source_l for t in toks)

aligned = [f for f in features if token_hit(f)]
unaligned = [f for f in features if f not in aligned]

step3 = {
    'step': 3,
    'step_name': 'html_parse_and_source_realignment',
    'features': features,
    'counts': {
        'headings': len(headings),
        'buttons': len(buttons),
        'labels': len(labels),
        'inputs': len(inputs),
        'features_total': len(features),
    },
    'alignment': {
        'source_file': 'bash.md',
        'aligned_features': aligned,
        'unaligned_features': unaligned,
        'alignment_ratio': (len(aligned) / len(features)) if features else 0,
    },
}
(root / 'step3.json').write_text(json.dumps(step3, indent=2), encoding='utf-8')

print(json.dumps({
    'ok': True,
    'step2_file': str(root / 'step2.json'),
    'mock_html': str(root / 'mock.html'),
    'step3_file': str(root / 'step3.json'),
    'features': len(features),
    'alignment_ratio': step3['alignment']['alignment_ratio']
}, indent=2))