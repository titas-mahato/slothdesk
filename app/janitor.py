"""
Janitor engine for SlothDesk.
Coordinates sandbox mock generation, real filesystem organization,
sloth metrics calculation, and undo history.
"""

import json
import os
import shutil
import uuid
from typing import Dict, List, Optional
from datetime import datetime

from app.models import (
    DrawerType,
    FileDescriptor,
    ClassificationResult,
    OrganizationPlan,
    SlothMetrics,
    DRAWER_METADATA,
)
from app.classifier import get_classifier


# Built-in realistic chaotic files for web sandbox simulation
CHAOTIC_SANDBOX_FILES: List[FileDescriptor] = [
    FileDescriptor(
        id="f-01",
        original_name="Screenshot 2026-10-24 at 11.23.41 PM.png",
        extension="png",
        size_bytes=428900,
        mime_type="image/png",
        preview_text="AWS Console AccessDenied IAM assume role session token expired error 403",
        is_image=True,
        is_mock=True,
    ),
    FileDescriptor(
        id="f-02",
        original_name="statement (2).pdf",
        extension="pdf",
        size_bytes=184200,
        mime_type="application/pdf",
        preview_text="Chase Sapphire Banking Monthly Statement Account Ending 4912 Total Balance $3,420.15 Transactions Oct 2026",
        is_mock=True,
    ),
    FileDescriptor(
        id="f-03",
        original_name="uber_trip_e83912.pdf",
        extension="pdf",
        size_bytes=98100,
        mime_type="application/pdf",
        preview_text="Uber Technologies Trip Receipt Downtown to SFO Airport Fare USD $42.50 Payment Method Stripe",
        is_mock=True,
    ),
    FileDescriptor(
        id="f-04",
        original_name="final_thesis_draft_v3_reallyfinal.docx",
        extension="docx",
        size_bytes=1420000,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        preview_text="Autonomous Multi-Agent Consensus in Distributed Systems abstract thesis lecture syllabus bibliography",
        is_mock=True,
    ),
    FileDescriptor(
        id="f-05",
        original_name="customers_dump_2026_raw.csv",
        extension="csv",
        size_bytes=3200100,
        mime_type="text/csv",
        preview_text="user_id,email,stripe_customer_id,signup_timestamp,auth_provider\n1,dev@zenith.ai,cus_91238,2026-10-24,github",
        is_mock=True,
    ),
    FileDescriptor(
        id="f-06",
        original_name="Screen Shot 2026-10-23 at 08.15.12 AM.png",
        extension="png",
        size_bytes=612400,
        mime_type="image/png",
        preview_text="Figma CSS flexbox grid alignment issue visual bug crop layout",
        is_image=True,
        is_mock=True,
    ),
    FileDescriptor(
        id="f-07",
        original_name="docker-compose.staging.yml",
        extension="yml",
        size_bytes=2400,
        mime_type="text/yaml",
        preview_text="version: '3.8'\nservices:\n  redis:\n    image: redis:alpine\n  postgres:\n    image: postgres:16\n    environment:\n      POSTGRES_DB: app",
        is_mock=True,
    ),
    FileDescriptor(
        id="f-08",
        original_name="node-v22.1.0-x64.msi",
        extension="msi",
        size_bytes=34500000,
        mime_type="application/x-msi",
        preview_text="Node.js 64-bit Windows installer setup bundle",
        is_mock=True,
    ),
    FileDescriptor(
        id="f-09",
        original_name="w2_wage_and_tax_2026.pdf",
        extension="pdf",
        size_bytes=210400,
        mime_type="application/pdf",
        preview_text="Internal Revenue Service Form W-2 Wage and Tax Statement Employer Identification Number Wages Tips Federal Income Tax Withheld",
        is_mock=True,
    ),
    FileDescriptor(
        id="f-10",
        original_name="archive_backup_october.zip",
        extension="zip",
        size_bytes=18400000,
        mime_type="application/zip",
        preview_text="Zip compressed release archive backup files",
        is_mock=True,
    ),
]


class SlothJanitorService:
    """
    Coordinates file organization and metrics calculation.
    """

    def __init__(self):
        self.classifier = get_classifier()

    def calculate_metrics(self, items: List[ClassificationResult], total_bytes: int) -> SlothMetrics:
        count = len(items)
        # Average user spends 45 seconds per file: clicking, reading, creating folders, renaming, moving
        minutes_saved = round((count * 45) / 60, 1)

        # Laziness score: 100 is maximum pure sloth bliss
        laziness_score = min(100, int(50 + (count * 5))) if count > 0 else 0

        # Hoarding assessment
        if count == 0:
            hoarding = "Spotless Zen Minimalist"
        elif count <= 4:
            hoarding = "Casual Weekend Clutterer"
        elif count <= 10:
            hoarding = "Procrastination Monarch"
        else:
            hoarding = "Supreme Digital Landfill Hoarder"

        return SlothMetrics(
            total_files_analyzed=count,
            manual_minutes_saved=minutes_saved,
            cloud_egress_bytes_prevented=total_bytes,
            laziness_score=laziness_score,
            hoarding_status=hoarding,
        )

    def plan_sandbox_organization(self, files: Optional[List[FileDescriptor]] = None) -> OrganizationPlan:
        """
        Runs the full classification and tidying pipeline over simulated or uploaded files.
        """
        targets = files if files is not None else CHAOTIC_SANDBOX_FILES
        items: List[ClassificationResult] = []
        drawers: Dict[str, List[ClassificationResult]] = {d.value: [] for d in DrawerType}
        total_bytes = 0

        for f in targets:
            total_bytes += f.size_bytes
            res = self.classifier.classify(f)
            items.append(res)
            drawers[res.target_drawer.value].append(res)

        metrics = self.calculate_metrics(items, total_bytes)

        return OrganizationPlan(
            plan_id=str(uuid.uuid4())[:8],
            total_files=len(items),
            items=items,
            drawers=drawers,
            metrics=metrics,
        )

    def organize_real_directory(self, target_dir: str, dry_run: bool = True) -> Dict:
        """
        Inspects and organizes a real folder on the user's computer.
        If dry_run is True, returns proposed moves without modifying files.
        If dry_run is False, creates drawer subdirectories and moves/renames files safely.
        """
        target_path = os.path.abspath(target_dir)
        if not os.path.exists(target_path) or not os.path.isdir(target_path):
            raise ValueError(f"Directory not found: {target_dir}")

        entries = [
            os.path.join(target_path, e)
            for e in os.listdir(target_path)
            if os.path.isfile(os.path.join(target_path, e))
        ]

        descriptors: List[FileDescriptor] = []
        for file_path in entries:
            fname = os.path.basename(file_path)
            # Skip hidden files or sloth history files
            if fname.startswith("."):
                continue

            size = os.path.getsize(file_path)
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
            preview, _ = self.classifier.extract_text_from_file(file_path)

            descriptors.append(
                FileDescriptor(
                    id=str(uuid.uuid4())[:8],
                    original_name=fname,
                    extension=ext,
                    size_bytes=size,
                    preview_text=preview,
                )
            )

        plan = self.plan_sandbox_organization(descriptors)

        history_records = []
        if not dry_run:
            # Execute actual moves
            for item in plan.items:
                orig_file = os.path.join(target_path, item.original_name)
                drawer_dir = os.path.join(target_path, item.target_drawer.value)
                os.makedirs(drawer_dir, exist_ok=True)

                dest_file = os.path.join(drawer_dir, item.proposed_name)

                # Avoid overwriting existing files
                counter = 1
                base, ext = os.path.splitext(item.proposed_name)
                while os.path.exists(dest_file):
                    dest_file = os.path.join(drawer_dir, f"{base}_{counter}{ext}")
                    counter += 1

                try:
                    shutil.move(orig_file, dest_file)
                    history_records.append({
                        "from": orig_file,
                        "to": dest_file,
                        "timestamp": datetime.now().isoformat()
                    })
                except Exception as err:
                    pass

            # Write undo history
            history_file = os.path.join(target_path, ".slothdesk_history.json")
            try:
                with open(history_file, "w", encoding="utf-8") as f:
                    json.dump(history_records, f, indent=2)
            except Exception:
                pass

        return {
            "target_dir": target_path,
            "dry_run": dry_run,
            "plan": plan.model_dump(),
            "operations_count": len(history_records) if not dry_run else 0,
        }
