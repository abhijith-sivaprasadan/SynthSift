from __future__ import annotations
import re

COUNTRIES = {
    "ireland": "Ireland", "irish": "Ireland", "germany": "Germany", "german": "Germany",
    "united kingdom": "United Kingdom", "uk": "United Kingdom", "u.k.": "United Kingdom",
    "north carolina": "United States", "united states": "United States", "u.s.": "United States",
    "us ": "United States", "oregon": "United States",
}

DESIGN_PATTERNS = [
    ("mixed_methods", ["interviews with industry stakeholders", "interviews"]),
    ("agent_based_model", ["agent-based model", "agent-based modeling"]),
    ("survey_experiment", ["survey experiment", "pre-registered survey experiment"]),
    ("household_survey", ["house owners", "household survey", "written survey"]),
    ("questionnaire_survey", ["structured questionnaire", "questionnaire"]),
    ("evidence_synthesis", ["evidence synthesis"]),
    ("pilot_evaluation", ["pilot", "pilot evaluation"]),
    ("policy_evaluation", ["rebate program", "loan program", "incentive"]),
    ("review", ["we review", "critical review", "literature review"]),
]

def extract_country(text: str):
    low = f" {text.lower()} "
    for key, canonical in COUNTRIES.items():
        if key in low:
            return canonical
    return ""


def extract_study_design(text: str):
    low=text.lower()
    for label, pats in DESIGN_PATTERNS:
        if any(p in low for p in pats): return label
    return ""


def extract_sample_size(text: str):
    pats=[r"\bn\s*=\s*([0-9,]+)\b", r"\b([0-9,]+) respondents\b", r"\b([0-9,]+) providers\b", r"installed\s+([0-9,]+) heat pumps"]
    for p in pats:
        m=re.search(p,text,flags=re.I)
        if m: return int(m.group(1).replace(',',''))
    return None
