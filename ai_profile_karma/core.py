"""Local scanner for what an AI could know about you, plus privacy request letters."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import date

__all__ = ["Finding", "scan_text", "scan_path", "exposure_score", "request_letter", "luhn_ok"]

PII_PATTERNS = {
    "email": (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), 3),
    "phone": (re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)"), 4),
    "address": (re.compile(r"\b\d{1,5}\s+(?:[A-Z][a-z]+\s){1,3}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b\.?"), 6),
    "date_of_birth": (re.compile(r"\b(?:born on|birthday is|dob[:\s]+|date of birth[:\s]+)\s*[\w ,/-]{4,20}", re.I), 6),
    "ssn": (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), 10),
    "iban": (re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b"), 8),
}
CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")

CATEGORIES = {
    "health": (["diagnosed", "prescription", "therapy", "therapist", "anxiety", "depression", "diabetes", "pregnan", "symptom", "medication", "adhd"], 8),
    "finances": (["salary", "debt", "mortgage", "loan", "credit score", "bankrupt", "my income", "savings account", "net worth"], 6),
    "location": (["i live in", "my address", "moved to", "my neighborhood", "near my house"], 5),
    "employer": (["i work at", "my boss", "my manager", "my employer", "my job at"], 4),
    "family": (["my wife", "my husband", "my partner", "my son", "my daughter", "my kids", "my mom", "my dad", "divorce"], 4),
    "religion": (["my church", "mosque", "synagogue", "i pray", "my faith"], 7),
    "politics": (["i voted", "my party", "democrat", "republican", "protest"], 7),
    "sexuality": (["i'm gay", "i am gay", "lesbian", "bisexual", "my boyfriend", "my girlfriend", "coming out"], 9),
}


@dataclass
class Finding:
    kind: str
    category: str  # "pii" or a sensitive category
    weight: int
    snippet: str
    source: str = ""


def luhn_ok(num: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", num)]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2:
            d *= 2
            d -= 9 if d > 9 else 0
        total += d
    return total % 10 == 0


def _mask(s: str) -> str:
    s = s.strip()
    if len(s) <= 4:
        return "*" * len(s)
    return s[:2] + "*" * (len(s) - 4) + s[-2:]


def _context(text: str, start: int, end: int, width: int = 40) -> str:
    left = text[max(0, start - width):start]
    right = text[end:end + width]
    return re.sub(r"\s+", " ", f"...{left}[{_mask(text[start:end])}]{right}...")


def scan_text(text: str, source: str = "") -> list[Finding]:
    out = []
    for kind, (rx, w) in PII_PATTERNS.items():
        for m in rx.finditer(text):
            out.append(Finding(kind, "pii", w, _context(text, m.start(), m.end()), source))
    for m in CARD_RE.finditer(text):
        if luhn_ok(m.group()):
            out.append(Finding("payment_card", "pii", 10, _context(text, m.start(), m.end()), source))
    low = text.lower()
    for cat, (words, w) in CATEGORIES.items():
        for word in words:
            i = low.find(word)
            if i >= 0:
                snippet = re.sub(r"\s+", " ", text[max(0, i - 30): i + len(word) + 50])
                out.append(Finding(word, cat, w, f"...{snippet}...", source))
    return out


def _iter_texts(path: str):
    if os.path.isfile(path):
        files = [path]
    else:
        files = [os.path.join(r, f) for r, _, fs in os.walk(path) for f in fs]
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext not in {".txt", ".md", ".json", ".jsonl", ".csv", ".html"}:
            continue
        with open(f, encoding="utf-8", errors="ignore") as fh:
            raw = fh.read()
        if ext == ".json":
            try:
                raw = "\n".join(_strings(json.loads(raw)))
            except json.JSONDecodeError:
                pass
        yield f, raw


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def scan_path(path: str) -> list[Finding]:
    findings = []
    for f, text in _iter_texts(path):
        findings.extend(scan_text(text, f))
    return findings


def exposure_score(findings: list[Finding]) -> dict:
    by_cat: dict[str, int] = {}
    kinds = set()
    for f in findings:
        by_cat[f.category] = by_cat.get(f.category, 0) + 1
        kinds.add((f.category, f.kind, f.weight))
    # Each distinct fact counts once; repeated mentions add a little.
    raw = sum(w for _, _, w in kinds) + 0.5 * (len(findings) - len(kinds))
    score = min(100, round(raw * 1.5))
    level = "high" if score >= 60 else "medium" if score >= 25 else "low"
    return {"score": score, "level": level, "by_category": by_cat, "distinct_facts": len(kinds)}


LAWS = {
    "gdpr": {"access": "Article 15", "correct": "Article 16", "delete": "Article 17", "deadline": "one month"},
    "ccpa": {"access": "Cal. Civ. Code 1798.110", "correct": "Cal. Civ. Code 1798.106", "delete": "Cal. Civ. Code 1798.105", "deadline": "45 days"},
}
VERBS = {"access": "provide me with a copy of", "correct": "correct", "delete": "erase"}


def request_letter(vendor: str, law: str, action: str, name: str, email: str, categories: list[str] | None = None, today: date | None = None) -> str:
    law_info = LAWS[law]
    today = today or date.today()
    cats = ", ".join(sorted(set(categories or []))) or "all categories"
    regime = "the EU/UK General Data Protection Regulation" if law == "gdpr" else "the California Consumer Privacy Act (as amended by the CPRA)"
    return f"""{today.isoformat()}

To: Privacy / Data Protection Officer, {vendor}
Subject: {action.title()} request under {law_info[action]} of {regime}

I am writing to exercise my right under {law_info[action]} of {regime}.
Please {VERBS[action]} all personal data you hold about me, including any data
used to personalise or train AI systems, chat histories, stored "memories",
and inferences or profiles derived from them.

This specifically includes data in these categories: {cats}.

{"Please also confirm that the data has been removed from any training datasets and that no derived inferences are retained." if action == "delete" else ""}
Account email: {email}

Please respond within {law_info['deadline']} as required by law. If you need to
verify my identity, contact me at the email above.

Sincerely,
{name}
"""
