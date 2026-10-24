"""
Local-first open-source semantic classifier for SlothDesk.
Combines scikit-learn TF-IDF semantic embeddings, domain anchor spaces,
heuristics, and optional local Ollama open-weight LLM inference.
100% offline, zero data sent to external cloud APIs.
"""

import os
import re
from typing import Dict, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import DrawerType, DRAWER_METADATA, ClassificationResult, FileDescriptor
from app.renamer import generate_smart_name


# Semantic Anchor Corpora for zero-shot drawer mapping
DRAWER_ANCHORS: Dict[DrawerType, str] = {
    DrawerType.FINANCE: (
        "invoice receipt statement bill tax payment w2 1099 stripe chase paypal banking wire "
        "salary payslip expense transaction total subtotal usd credit debit balance due amount "
        "order confirmation vendor accounting audit refund"
    ),
    DrawerType.DEVELOPMENT: (
        "python javascript typescript code git diff pull request commit bug crash log traceback "
        "error exception json yaml csv sql database query api endpoint docker container bash "
        "terminal script build release repository unit test schema rust golang"
    ),
    DrawerType.MEDIA: (
        "screenshot display screen shot capture snip image photo picture wallpaper meme "
        "camera graphic asset banner icon illustration visual preview render recording"
    ),
    DrawerType.DOCUMENTS: (
        "research paper thesis syllabus assignment lecture slide deck presentation curriculum "
        "vitae resume contract agreement nda handbook report essay proposal academic draft book"
    ),
    DrawerType.ARCHIVES: (
        "zip tar gzip tgz rar 7z compressed archive installer setup dmg pkg deb rpm iso "
        "bin bundle package backup dump release executable"
    ),
}

# Strong extension biases
EXTENSION_MAP: Dict[str, DrawerType] = {
    # Development
    "py": DrawerType.DEVELOPMENT,
    "js": DrawerType.DEVELOPMENT,
    "ts": DrawerType.DEVELOPMENT,
    "jsx": DrawerType.DEVELOPMENT,
    "tsx": DrawerType.DEVELOPMENT,
    "html": DrawerType.DEVELOPMENT,
    "css": DrawerType.DEVELOPMENT,
    "json": DrawerType.DEVELOPMENT,
    "yaml": DrawerType.DEVELOPMENT,
    "yml": DrawerType.DEVELOPMENT,
    "sql": DrawerType.DEVELOPMENT,
    "sh": DrawerType.DEVELOPMENT,
    "bat": DrawerType.DEVELOPMENT,
    "patch": DrawerType.DEVELOPMENT,
    "diff": DrawerType.DEVELOPMENT,
    "log": DrawerType.DEVELOPMENT,
    "csv": DrawerType.DEVELOPMENT,
    "env": DrawerType.DEVELOPMENT,
    "rs": DrawerType.DEVELOPMENT,
    "go": DrawerType.DEVELOPMENT,
    # Media
    "png": DrawerType.MEDIA,
    "jpg": DrawerType.MEDIA,
    "jpeg": DrawerType.MEDIA,
    "webp": DrawerType.MEDIA,
    "gif": DrawerType.MEDIA,
    "svg": DrawerType.MEDIA,
    "mp4": DrawerType.MEDIA,
    "mov": DrawerType.MEDIA,
    # Documents
    "docx": DrawerType.DOCUMENTS,
    "pptx": DrawerType.DOCUMENTS,
    "xlsx": DrawerType.FINANCE,  # Default spreadsheets often finance, subject to text content
    "epub": DrawerType.DOCUMENTS,
    # Archives
    "zip": DrawerType.ARCHIVES,
    "tar": DrawerType.ARCHIVES,
    "gz": DrawerType.ARCHIVES,
    "tgz": DrawerType.ARCHIVES,
    "rar": DrawerType.ARCHIVES,
    "7z": DrawerType.ARCHIVES,
    "dmg": DrawerType.ARCHIVES,
    "iso": DrawerType.ARCHIVES,
    "pkg": DrawerType.ARCHIVES,
    "deb": DrawerType.ARCHIVES,
    "exe": DrawerType.ARCHIVES,
    "msi": DrawerType.ARCHIVES,
}


class SemanticJanitorClassifier:
    """
    Open-source semantic classifier running scikit-learn TF-IDF vectorization
    over domain anchor spaces. Works completely locally with zero cloud dependencies.
    """

    def __init__(self):
        self.drawers = list(DRAWER_ANCHORS.keys())
        self.anchor_texts = [DRAWER_ANCHORS[d] for d in self.drawers]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
        # Fit vectorizer on domain anchors
        self.anchor_matrix = self.vectorizer.fit_transform(self.anchor_texts)

    def extract_text_from_file(self, file_path: str, max_chars: int = 4000) -> Tuple[str, List[str]]:
        """
        Safely extracts text preview and keywords from local file.
        Uses pypdf for PDFs if available, falls back gracefully.
        """
        if not os.path.exists(file_path):
            return "", []

        ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        extracted = ""

        try:
            if ext in ["txt", "csv", "log", "md", "json", "py", "sh", "sql", "yaml", "yml", "diff", "patch"]:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    extracted = f.read(max_chars)

            elif ext == "pdf":
                try:
                    import pypdf
                    reader = pypdf.PdfReader(file_path)
                    text_parts = []
                    for page in reader.pages[:3]:  # Read first 3 pages
                        text_parts.append(page.extract_text() or "")
                    extracted = " ".join(text_parts)[:max_chars]
                except Exception:
                    extracted = ""

        except Exception:
            extracted = ""

        tags = self._extract_key_tokens(extracted)
        return extracted, tags

    def _extract_key_tokens(self, text: str) -> List[str]:
        """Extracts top domain tokens from text."""
        words = re.findall(r"\b[a-zA-Z]{3,15}\b", text.lower())
        stopwords = {"the", "and", "for", "with", "from", "that", "this", "have", "were", "been"}
        counts: Dict[str, int] = {}
        for w in words:
            if w not in stopwords:
                counts[w] = counts.get(w, 0) + 1
        sorted_tokens = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_tokens[:6]]

    def classify(self, descriptor: FileDescriptor) -> ClassificationResult:
        """
        Predicts target drawer and proposed name for a given file descriptor.
        """
        original_name = descriptor.original_name
        ext = descriptor.extension.lower()
        preview = descriptor.preview_text or ""

        # Construct combined query vector from filename, tags, and preview text
        query_text = f"{original_name.replace('_', ' ').replace('-', ' ')} {preview}".strip()

        # 1. Base extension bias
        ext_bias_drawer = EXTENSION_MAP.get(ext)

        # 2. Vector semantic matching
        detected_tags = self._extract_key_tokens(query_text)
        confidence = 0.50
        predicted_drawer = DrawerType.DOCUMENTS
        reason = "Matched by semantic similarity."

        if ext_bias_drawer in [DrawerType.DEVELOPMENT, DrawerType.ARCHIVES]:
            # Code, config, scripts, datasets, and archives have strict extension precedence
            predicted_drawer = ext_bias_drawer
            confidence = 0.94
            reason = f"Classified by developer/system format specification (.{ext})."
        elif query_text:
            query_vec = self.vectorizer.transform([query_text])
            similarities = cosine_similarity(query_vec, self.anchor_matrix)[0]
            best_idx = int(np.argmax(similarities))
            sim_score = float(similarities[best_idx])

            if sim_score > 0.15:
                predicted_drawer = self.drawers[best_idx]
                confidence = min(0.98, max(0.68, sim_score * 2.2))
                reason = f"Identified {predicted_drawer.value} keywords via local TF-IDF semantic matching."
            elif ext_bias_drawer:
                predicted_drawer = ext_bias_drawer
                confidence = 0.85
                reason = f"Categorized via standard file format specification (.{ext})."
        elif ext_bias_drawer:
            predicted_drawer = ext_bias_drawer
            confidence = 0.88
            reason = f"Classified by file extension .{ext}."

        # 3. Special Context Rules (Heuristic Refinement)
        lower_name = original_name.lower()

        # Rule A: Financial documents in PDF/Image form (e.g. Receipt.png, Invoice.pdf)
        if any(w in lower_name or w in preview.lower() for w in ["invoice", "receipt", "tax", "1099", "w2", "billing", "payslip"]):
            predicted_drawer = DrawerType.FINANCE
            confidence = 0.96
            reason = "Detected financial transaction/tax entity tokens in document header."

        # Rule B: Screenshots / Screen snips
        elif any(w in lower_name for w in ["screenshot", "screen shot", "snip", "capture"]) and ext in ["png", "jpg", "jpeg", "webp"]:
            # If screenshot contains explicit code / terminal error tokens, can still stay in Media or Dev
            predicted_drawer = DrawerType.MEDIA
            confidence = 0.95
            reason = "Identified desktop screen capture format and filename signature."

        # Rule C: Installers & Archives
        elif ext in ["zip", "tar", "gz", "tgz", "rar", "7z", "dmg", "iso", "pkg", "deb", "exe", "msi"]:
            predicted_drawer = DrawerType.ARCHIVES
            confidence = 0.99
            reason = "Identified compressed archive/installer binary package."

        # Generate smart normalized name
        proposed_name = generate_smart_name(
            original_name=original_name,
            drawer=predicted_drawer,
            preview_text=preview,
            detected_tags=detected_tags,
        )

        return ClassificationResult(
            file_id=descriptor.id,
            original_name=original_name,
            proposed_name=proposed_name,
            target_drawer=predicted_drawer,
            confidence=round(confidence, 2),
            detected_tags=detected_tags,
            reason=reason,
            drawer_metadata=DRAWER_METADATA.get(predicted_drawer),
        )


# Global singleton instance
_classifier_instance: Optional[SemanticJanitorClassifier] = None


def get_classifier() -> SemanticJanitorClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SemanticJanitorClassifier()
    return _classifier_instance
