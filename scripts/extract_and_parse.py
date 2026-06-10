#!/usr/bin/env python3
import sys
from pdfminer.high_level import extract_text
import json
import re

PDF_PATH = sys.argv[1] if len(sys.argv) > 1 else 'quiz/3~6강 단어 정리.pdf'

text = extract_text(PDF_PATH, maxpages=15)
lines = [l.strip() for l in text.splitlines() if l.strip()]

def word_like(s):
    if not s: return False
    wc = len(s.split())
    punct_count = len(re.findall(r"[.,;()\[\]\\\"'：:–—-]", s))
    return wc <= 3 and punct_count <= 2 and len(s) < 60


def infer_pair(left, right):
    left = left.strip()
    right = right.strip()
    def has_hangul(s):
        return re.search(r"[\uac00-\ud7af]", s) is not None
    def has_japanese(s):
        return re.search(r"[\u3040-\u30ff\u31f0-\u31ff\u4e00-\u9fff]", s) is not None

    # Japanese <-> Hangul mapping priority
    if has_japanese(left) and has_hangul(right):
        return {'q': left, 'a': right}
    if has_hangul(left) and has_japanese(right):
        return {'q': right, 'a': left}

    left_word = word_like(left)
    right_word = word_like(right)
    if left_word and not right_word:
        return {'q': left, 'a': right}
    if right_word and not left_word:
        return {'q': right, 'a': left}
    if len(left) <= len(right):
        return {'q': left, 'a': right}
    return {'q': right, 'a': left}

parsed = []
for line in lines:
    parts = []
    if '\t' in line:
        parts = [p.strip() for p in line.split('\t') if p.strip()]
    elif re.search(r'[-–—:：]\s+', line):
        m = re.split(r'[-–—:：]', line, maxsplit=1)
        if len(m) == 2:
            parts = [m[0].strip(), m[1].strip()]
    elif re.search(r'\s{2,}', line):
        parts = [p.strip() for p in re.split(r'\s{2,}', line) if p.strip()]
    elif ',' in line:
        parts = [p.strip() for p in line.split(',') if p.strip()]
    else:
        toks = line.split()
        if len(toks) >= 2:
            mid = (len(toks)+1)//2
            parts = [' '.join(toks[:mid]).strip(), ' '.join(toks[mid:]).strip()]

    if len(parts) >= 2:
        if len(parts) == 2:
            p = infer_pair(parts[0], parts[1])
            parsed.append(p)
        else:
            for i in range(0, len(parts)-1, 2):
                p = infer_pair(parts[i], parts[i+1])
                parsed.append(p)

# Save results
out_json = '/workspaces/quiz/parsed_cards.json'
with open(out_json, 'w', encoding='utf-8') as f:
    json.dump({'lines_preview': lines[:80], 'parsed_preview': parsed[:120], 'count_lines': len(lines), 'count_parsed': len(parsed)}, f, ensure_ascii=False, indent=2)

# Print concise summary
print(f'lines={len(lines)} parsed_pairs={len(parsed)}')
print('First 20 parsed pairs:')
for i,p in enumerate(parsed[:20]):
    print(f"{i+1}. Q: {p['q']}  |  A: {p['a']}")

print('\nFull JSON written to ' + out_json)
