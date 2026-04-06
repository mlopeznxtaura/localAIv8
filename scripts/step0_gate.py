#!/usr/bin/env python3
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
PROMPT_FILE = ROOT / 'bash.md'
INPUT_FILE = ROOT / 'user_prompt.txt'
VALIDATED_FILE = ROOT / 'validated_prompt'
DECISION_FILE = ROOT / 'step0_forced_decision.json'
USER_DECISION_FILE = ROOT / 'step0_user_decision.json'

ANCHORS = [
    'step0_ground.py','step1_compress.py','step2_mockui.py','step3_parse.py',
    'step4_dag.py','step5_tasks.py','step6_build.py','tool_cache','training_data',
    'online_trainer.py','export_student.py','tasks.json','tests.json','output.zip','react','express'
]


def normalize(text: str) -> str:
    text = text.replace('\r\n','\n').replace('\r','\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip() + '\n'


def anchor_ratio(text: str):
    low = text.lower()
    present = [a for a in ANCHORS if a.lower() in low]
    missing = [a for a in ANCHORS if a.lower() not in low]
    ratio = len(present) / len(ANCHORS)
    return ratio, present, missing


def tool_evidence_count():
    queries = [
        'stateless ai orchestration architecture validation',
        'ollama gemma4 prompt reliability and context constraints'
    ]
    count = 0
    calls = []
    for q in queries:
        url = f"https://api.duckduckgo.com/?q={quote_plus(q)}&format=json&no_html=1&skip_disambig=1"
        item = {'tool':'web_search', 'query': q, 'url': url}
        try:
            with urlopen(url, timeout=10) as r:
                data = json.loads(r.read().decode('utf-8', errors='ignore'))
            snippet = (data.get('AbstractText') or data.get('Definition') or '').strip()
            item['ok'] = True
            item['snippet'] = snippet[:260]
            item['evidence_non_empty'] = bool(snippet)
            if snippet:
                count += 1
        except Exception as exc:
            item['ok'] = False
            item['error'] = str(exc)
            item['snippet'] = ''
            item['evidence_non_empty'] = False
        calls.append(item)
    return count, calls


def build_decision(prompt_text: str):
    ratio, _, missing = anchor_ratio(prompt_text)
    tool_non_empty, calls = tool_evidence_count()
    cutoff = '2025-04-01'
    today = datetime.now(timezone.utc).date().isoformat()

    why = [
        f'anchor_coverage={ratio:.2f}',
        f'tool_evidence_non_empty={tool_non_empty}',
        f'cutoff_status={'today_after_cutoff' if today > cutoff else 'today_on_or_before_cutoff'}'
    ]

    blockers = []
    decision = 'GO'
    if ratio < 0.85:
        blockers.append('anchor_coverage_below_threshold')
    if tool_non_empty < 1:
        blockers.append('insufficient_external_evidence')

    if blockers:
        decision = 'NO_GO'
    elif tool_non_empty == 1:
        decision = 'GO_WITH_WARNINGS'

    next_actions = [
        {'id':'A1','label':'Approve and continue to Step 1','action':'step1'},
        {'id':'A2','label':'Run deeper research pass','action':'step0_research_plus'},
        {'id':'A3','label':'Edit prompt before retry','action':'open_user_prompt'},
        {'id':'A4','label':'Stop pipeline','action':'stop'}
    ]

    score = max(0.0, min(1.0, (ratio * 0.7) + (0.3 if tool_non_empty >= 1 else 0.0)))

    return {
        'step': 0,
        'decision_required': True,
        'decision': decision,
        'relevance_score': round(score, 2),
        'why': why,
        'blockers': blockers,
        'missing_anchors': missing,
        'next_actions': next_actions,
        'default_action': 'A2',
        'tool_calls': calls
    }


def run_gate():
    prompt = PROMPT_FILE.read_text(encoding='utf-8', errors='ignore')
    INPUT_FILE.write_text(prompt, encoding='utf-8')
    VALIDATED_FILE.write_text(normalize(prompt), encoding='utf-8')
    decision = build_decision(prompt)
    DECISION_FILE.write_text(json.dumps(decision, indent=2), encoding='utf-8')

    if decision['decision'] != 'GO':
        print('DECISION: NO_GO')
        print('SELECT ACTION: A1/A2/A3/A4')
        return 2

    if not USER_DECISION_FILE.exists():
        print('DECISION: GO')
        print('SELECT ACTION: A1/A2/A3/A4')
        return 2

    user_dec = json.loads(USER_DECISION_FILE.read_text(encoding='utf-8'))
    if user_dec.get('selected_action') != 'A1':
        print('DECISION: NO_GO')
        print('SELECT ACTION: A1/A2/A3/A4')
        return 2

    print('DECISION: GO')
    print('SELECT ACTION: A1/A2/A3/A4')
    return 0


def choose_action(action_id: str):
    payload = {
        'step': 0,
        'selected_action': action_id,
        'selected_at_utc': datetime.now(timezone.utc).isoformat()
    }
    USER_DECISION_FILE.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'choose':
        raise SystemExit(choose_action(sys.argv[2]))
    raise SystemExit(run_gate())