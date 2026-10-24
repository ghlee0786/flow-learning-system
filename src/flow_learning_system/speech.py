"""화면 문장 → TTS가 읽을 문장.

1. ``[[화면 표기|읽는 말]]`` 은 읽는 말로, 백틱과 ``**`` 은 지웁니다.
2. 읽기 규칙(pron_base.json + 코스별 pronunciations)으로 영어·코드 단어를 한글로 바꿉니다.
3. 남은 알파벳 한 글자는 '에이', '비' … 로 읽습니다.
4. 숫자는 문맥에 맞춰 '열일곱 개', '세 번', '이십일억' 처럼 한글로 바꿉니다.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib import resources

_D = '영일이삼사오육칠팔구'
_ONE = ['', '한', '두', '세', '네', '다섯', '여섯', '일곱', '여덟', '아홉']
_TEN = ['', '열', '스물', '서른', '마흔', '쉰', '예순', '일흔', '여든', '아흔']


@lru_cache(maxsize=1)
def _base():
    data = json.loads(resources.files(__package__).joinpath('pron_base.json').read_text(encoding='utf-8'))
    return [(re.compile(p, re.A), r) for p, r in data['rules']], data['letters']


def _compile_extra(extra: dict | None):
    if not extra:
        return []
    out = []
    for word, reading in sorted(extra.items(), key=lambda kv: -len(kv[0])):
        out.append((re.compile(r'\b' + re.escape(word) + r'\b', re.A), reading))
    return out


EN = re.compile(r'\{en\|([^}]+)\}')
MATH = re.compile(r'\{m\|((?:[^{}]|\{[^{}]*\})+)\}')


def say_text(s: str, extra: dict | None = None) -> str:
    """대본 문장을 '읽는 문장'으로 바꿉니다(숫자는 그대로). {en|…} 구간은 손대지 않습니다."""
    keep = []
    s = EN.sub(lambda m: keep.append(m.group(1)) or f'\uE000{len(keep) - 1}\uE001', s)
    t = _say_ko(s, extra)
    return re.sub('\uE000(\\d+)\uE001', lambda m: '{en|' + keep[int(m.group(1))] + '}', t)


def _say_ko(s: str, extra: dict | None = None) -> str:
    rules, letters = _base()
    s = MATH.sub(lambda m: re.sub(r'\\[a-zA-Z]+|[{}^_]', ' ', m.group(1)), s)
    t = re.sub(r'\[\[((?:\{[^}]*\}|\](?!\])|[^|\]])+)\|(.+?)\]\]', r'\2', s)
    t = re.sub(r'`([^`]+)`', r'\1', t).replace('**', '')
    for rx, rep in _compile_extra(extra) + rules:
        t = rx.sub(rep.replace('\\', '\\\\'), t)
    t = re.sub(r'(^|[^A-Za-z])([A-Za-z])(?![A-Za-z])', lambda m: m.group(1) + letters[m.group(2).lower()], t)
    return re.sub(r'\s+', ' ', t).strip()


def _sino4(n: int) -> str:
    s = ''
    for u, v in ((1000, '천'), (100, '백'), (10, '십')):
        q, n = divmod(n, u)
        if q:
            s += ('' if q == 1 else _D[q]) + v
    if n:
        s += _D[n]
    return s


def sino(n: int) -> str:
    """한자어 수: 2147483647 → 이십일억사천칠백사십팔만삼천육백사십칠"""
    if n == 0:
        return '영'
    parts, units, i = [], ['', '만', '억', '조', '경'], 0
    while n:
        n, g = divmod(n, 10000)
        if g:
            parts.append(('' if (g == 1 and units[i] == '만') else _sino4(g)) + units[i])
        i += 1
    return ''.join(reversed(parts))


def native(n: int) -> str:
    """고유어 수(개수 앞): 17 → 열일곱"""
    if n == 20:
        return '스무'
    return _TEN[n // 10] + _ONE[n % 10]


_IDX = r'(?=\s*(?:칸|날|째|의|부터|까지|에서|입니다|이고|이라|으로|로|에|이|은|는|을|과|와|과의|,)(?![가-힣]*\s*(?:옮|움직|건너)))'


def norm(t: str) -> str:
    """숫자와 기호를 한글 읽기로 바꿉니다."""
    t = t.replace('10¹⁰', '10000000000').replace('10⁹', '1000000000').replace('10⁵', '100000')
    t = re.sub(r'(\d),(?=\d{3})', r'\1', t)
    t = re.sub(r'(?<![\w가-힣])-(\d)', r'마이너스 \1', t)
    t = re.sub(r'\d+(?:\.\d+){2,}', lambda m: ' 점 '.join(sino(int(x)) for x in m.group().split('.')), t)
    t = re.sub(r'(\d+)\.(\d+)', lambda m: sino(int(m.group(1))) + ' 점 ' + ' '.join(_D[int(c)] for c in m.group(2)), t)
    t = re.sub(r'(\d+)\s*번' + _IDX, lambda m: sino(int(m.group(1))) + ' 번', t)

    def cnt(m):
        n, c = int(m.group(1)), m.group(2)
        if c == '시':
            return (native(n) if 0 < n <= 24 else sino(n)) + ' 시'
        return (native(n) if 0 < n < 100 else sino(n)) + ' ' + c
    t = re.sub(r'(\d+)\s*(개|가지|장|칸|명|번|시)(?![간각작])', cnt, t)
    t = re.sub(r'\d+', lambda m: sino(int(m.group())), t)
    t = re.sub(r'[\[\](){}<>=|`*#_]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()


def speech_parts(s: str, extra: dict | None = None) -> list[tuple[str, str]]:
    """대본 문장 → [(언어, 읽을 문장), …]. {en|…}는 영어 음성으로 읽습니다."""
    out = []
    for i, part in enumerate(EN.split(say_text(s, extra))):
        part = part.strip()
        if not part:
            continue
        out.append(("en", part) if i % 2 else ("ko", norm(part)))
    return [p for p in out if p[1]]


def speech_text(s: str, extra: dict | None = None) -> str:
    """대본 문장 → TTS 입력을 한 줄로 표현(영어 구간은 ⟪en:…⟫)."""
    return " ".join(t if lang == "ko" else f"⟪en:{t}⟫" for lang, t in speech_parts(s, extra))


def unreadable(spoken: str) -> list[str]:
    """TTS가 제대로 못 읽을 가능성이 큰 조각(영어 단어, 특수 기호). 영어 구간은 제외."""
    spoken = re.sub(r'⟪en:[^⟫]*⟫', ' ', spoken)
    bad = re.findall(r'[A-Za-z]{2,}', spoken)
    bad += [c for c in spoken if not re.match(r'[가-힣\s.,?!:;\'"·…~/%+]', c)]
    return sorted(set(bad))
