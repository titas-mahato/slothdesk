"""
Smart semantic renamer for SlothDesk.
Extracts entities, vendors, dates, and context tags to turn cryptic filenames into clean, searchable names.
"""

import re
from datetime import datetime
from typing import List, Optional
from app.models import DrawerType


KNOWN_VENDORS = {
    "uber": "uber",
    "lyft": "lyft",
    "aws": "aws",
    "amazon": "amazon",
    "amzn": "amazon",
    "chase": "chase_bank",
    "stripe": "stripe",
    "paypal": "paypal",
    "github": "github",
    "google": "google",
    "apple": "apple",
    "microsoft": "microsoft",
    "doordash": "doordash",
    "starbucks": "starbucks",
    "netflix": "netflix",
    "spotify": "spotify",
    "cloudflare": "cloudflare",
    "digitalocean": "digitalocean",
    "render": "render",
    "heroku": "heroku",
    "supabase": "supabase",
}

FINANCE_KEYWORDS = {
    "invoice": "invoice",
    "receipt": "receipt",
    "statement": "statement",
    "tax": "tax_doc",
    "w2": "w2",
    "1099": "1099",
    "bill": "bill",
    "payslip": "payslip",
    "salary": "salary",
}

DEV_KEYWORDS = {
    "diff": "git_diff",
    "patch": "git_patch",
    "log": "system_log",
    "error": "error_log",
    "dump": "data_dump",
    "schema": "db_schema",
    "migration": "db_migration",
    "dataset": "dataset",
    "benchmark": "benchmark",
    "trace": "stacktrace",
    "config": "configuration",
}

DOC_KEYWORDS = {
    "resume": "resume",
    "cv": "cv",
    "thesis": "thesis",
    "paper": "research_paper",
    "contract": "legal_contract",
    "nda": "nda",
    "lecture": "lecture_notes",
    "syllabus": "syllabus",
    "slide": "slides",
    "handbook": "handbook",
}


def extract_date(text: str) -> Optional[str]:
    """
    Tries to find a date in formats:
    - YYYY-MM-DD
    - YYYY_MM_DD
    - YYYYMMDD
    - YYYY-MM
    - Month YYYY (e.g. October 2026)
    """
    # YYYY-MM-DD or YYYY_MM_DD (avoid \b because _ is a \w character)
    m = re.search(r"(?<![0-9a-zA-Z])(20[2-3][0-9])[-_](0[1-9]|1[0-2])[-_](0[1-9]|[12][0-9]|3[01])(?![0-9a-zA-Z])", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # YYYYMMDD
    m = re.search(r"(?<![0-9a-zA-Z])(20[2-3][0-9])(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])(?![0-9a-zA-Z])", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # YYYY-MM
    m = re.search(r"(?<![0-9a-zA-Z])(20[2-3][0-9])[-_](0[1-9]|1[0-2])(?![0-9a-zA-Z])", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    # Check for month names: Oct 2026 or October 2026
    months = {
        "jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
        "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }
    month_pattern = r"(?<![0-9a-zA-Z])(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*[-_\s]+(20[2-3][0-9])(?![0-9a-zA-Z])"
    m = re.search(month_pattern, text, re.IGNORECASE)
    if m:
        m_str = m.group(1).lower()[:3]
        year = m.group(2)
        month_num = months.get(m_str, "01")
        return f"{year}-{month_num}"

    return None


def sanitize_slug(name: str) -> str:
    """Cleans up strings into safe, standard snake_case tokens."""
    name = re.sub(r"[^\w\-]", "_", name.lower())
    name = re.sub(r"_+", "_", name)
    return name.strip("_")


def generate_smart_name(
    original_name: str,
    drawer: DrawerType,
    preview_text: Optional[str] = None,
    detected_tags: Optional[List[str]] = None,
) -> str:
    """
    Generates a descriptive, normalized filename.
    Removes annoying duplicate clutter tags like '(1)', 'Copy of', 'Screenshot 202...'.
    """
    if "." in original_name:
        base_name, ext = original_name.rsplit(".", 1)
        ext = ext.lower()
    else:
        base_name = original_name
        ext = ""

    combined_text = f"{base_name} {preview_text or ''} {' '.join(detected_tags or [])}".lower()

    # Extract date
    detected_date = extract_date(combined_text)
    if not detected_date:
        # Default to today's date format YYYY-MM
        detected_date = datetime.now().strftime("%Y-%m-%d")

    tokens = []

    # Check for vendors
    found_vendor = None
    for pattern, slug in KNOWN_VENDORS.items():
        if re.search(rf"\b{pattern}\b", combined_text):
            found_vendor = slug
            break
    if found_vendor:
        tokens.append(found_vendor)

    # Check for category-specific keywords
    if drawer == DrawerType.FINANCE:
        for kw, slug in FINANCE_KEYWORDS.items():
            if re.search(rf"\b{kw}\b", combined_text):
                tokens.append(slug)
                break
        if not tokens:
            tokens.append("financial_record")

    elif drawer == DrawerType.DEVELOPMENT:
        for kw, slug in DEV_KEYWORDS.items():
            if re.search(rf"\b{kw}\b", combined_text):
                tokens.append(slug)
                break
        if not tokens:
            if detected_tags:
                tokens.append(sanitize_slug(detected_tags[0]))
            else:
                tokens.append("dev_artifact")

    elif drawer == DrawerType.MEDIA:
        is_screenshot = any(s in base_name.lower() for s in ["screenshot", "screen shot", "snip", "capture"])
        if is_screenshot:
            tokens.append("screenshot")
            for tag in (detected_tags or []):
                if tag not in ["image", "media", "screenshot"]:
                    tokens.append(sanitize_slug(tag))
                    break
        elif "meme" in combined_text:
            tokens.append("meme")
        else:
            tokens.append("media_capture")

    elif drawer == DrawerType.DOCUMENTS:
        for kw, slug in DOC_KEYWORDS.items():
            if re.search(rf"\b{kw}\b", combined_text):
                tokens.append(slug)
                break
        if not tokens:
            tokens.append("document")

    elif drawer == DrawerType.ARCHIVES:
        cleaned_base = re.sub(r"[\(\[\{].*?[\)\]\}]", "", base_name)
        cleaned_base = re.sub(r"\b(copy|v\d+|final|archive|new)\b", "", cleaned_base, flags=re.IGNORECASE)
        slug_base = sanitize_slug(cleaned_base)
        if slug_base:
            tokens.append(slug_base)
        else:
            tokens.append("bundle_archive")

    # Add date
    if detected_date:
        tokens.append(detected_date)

    # Join tokens
    new_base = "_".join(tokens)
    new_base = re.sub(r"_+", "_", new_base).strip("_")

    if not new_base:
        new_base = f"sloth_tidy_{detected_date}"

    return f"{new_base}.{ext}" if ext else new_base
