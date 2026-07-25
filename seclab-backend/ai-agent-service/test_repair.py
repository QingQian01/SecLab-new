"""Test if _repair_double_encoded_utf8 corrupts correct UTF-8 text."""
import sys
sys.path.insert(0, '.')
from profile_repository import _repair_double_encoded_utf8

# Test with the EXACT text from the database
test_cases = [
    "知识掌握当前得分 7.78，知识掌握度偏低，优先回补基础理论和题目复习模块。 已匹配真实模块「XSS and CSRF Basic Lab」。",
    "排障能力当前得分 0.00，排障能力偏低，建议围绕排查、修复与实战复盘类资源补强。",
    "知识掌握度偏低，优先回补基础理论和题目复习模块。",
    "已匹配真实模块「XSS and CSRF Basic Lab」。",
]

print("=== Testing _repair_double_encoded_utf8 on correct UTF-8 text ===\n")
for text in test_cases:
    repaired = _repair_double_encoded_utf8(text)
    changed = repaired != text
    print(f"Original:  {text[:80]}")
    print(f"Repaired:  {repaired[:80]}")
    print(f"CHANGED:   {changed}")
    if changed:
        has_kata = any('\u30c0' <= c <= '\u30ff' for c in repaired)
        print(f"  >>> CORRUPTED! Has katakana garble: {has_kata}")
    print()
