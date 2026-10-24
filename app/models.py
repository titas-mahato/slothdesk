"""
Pydantic schemas and data models for SlothDesk.
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DrawerType(str, Enum):
    FINANCE = "Finance & Receipts"
    DEVELOPMENT = "Development & Tech"
    MEDIA = "Media & Screenshots"
    DOCUMENTS = "Documents & Reference"
    ARCHIVES = "Installers & Archives"


class DrawerMetadata(BaseModel):
    key: DrawerType
    icon: str
    description: str
    color_hex: str


DRAWER_METADATA: Dict[DrawerType, DrawerMetadata] = {
    DrawerType.FINANCE: DrawerMetadata(
        key=DrawerType.FINANCE,
        icon="receipt",
        description="Bank statements, invoices, tax documents, payslips, and billing records.",
        color_hex="#10b981",  # emerald
    ),
    DrawerType.DEVELOPMENT: DrawerMetadata(
        key=DrawerType.DEVELOPMENT,
        icon="terminal",
        description="Source code, git diffs, server logs, CSV datasets, and environment keys.",
        color_hex="#3b82f6",  # blue
    ),
    DrawerType.MEDIA: DrawerMetadata(
        key=DrawerType.MEDIA,
        icon="image",
        description="UI screenshots, memes, camera roll, wallpapers, and video screen caps.",
        color_hex="#8b5cf6",  # purple
    ),
    DrawerType.DOCUMENTS: DrawerMetadata(
        key=DrawerType.DOCUMENTS,
        icon="file-text",
        description="Research papers, academic PDFs, slide decks, resumes, and study guides.",
        color_hex="#f59e0b",  # amber
    ),
    DrawerType.ARCHIVES: DrawerMetadata(
        key=DrawerType.ARCHIVES,
        icon="archive",
        description="Compressed zip/tarballs, dmg/iso/exe installers, and package bundles.",
        color_hex="#64748b",  # slate
    ),
}


class FileDescriptor(BaseModel):
    id: str
    original_name: str
    extension: str
    size_bytes: int = 0
    mime_type: str = "application/octet-stream"
    preview_text: Optional[str] = None
    is_image: bool = False
    is_mock: bool = False


class ClassificationResult(BaseModel):
    file_id: str
    original_name: str
    proposed_name: str
    target_drawer: DrawerType
    confidence: float = Field(ge=0.0, le=1.0)
    detected_tags: List[str] = Field(default_factory=list)
    reason: str
    drawer_metadata: Optional[DrawerMetadata] = None


class SlothMetrics(BaseModel):
    total_files_analyzed: int
    manual_minutes_saved: float
    cloud_egress_bytes_prevented: int
    laziness_score: int  # 0 to 100
    hoarding_status: str
    privacy_rating: str = "100% Zero-Cloud Air-Gapped"


class OrganizationPlan(BaseModel):
    plan_id: str
    total_files: int
    items: List[ClassificationResult]
    drawers: Dict[str, List[ClassificationResult]]
    metrics: SlothMetrics
