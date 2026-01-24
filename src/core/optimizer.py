"""Optimization helpers for Black Desert Online."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Tuple


def find_bdo_documents_folder() -> Path | None:
    """Return the path to the BDO Documents folder, or None if not found."""
    # Usually: %USERPROFILE%/Documents/Black Desert
    try:
        user_profile = os.environ.get("USERPROFILE")
        if not user_profile:
            return None
        
        candidates = [
            Path(user_profile) / "Documents" / "Black Desert",
            Path(user_profile) / "OneDrive" / "Documents" / "Black Desert",
        ]

        for path in candidates:
            if path.is_dir():
                return path

    except Exception:
        pass
    
    return None


def clear_cache() -> Tuple[bool, str]:
    """
    Clear the 'UserCache' and 'Cache' folders from the BDO documents directory.
    Returns (success, message).
    """
    bdo_dir = find_bdo_documents_folder()
    if not bdo_dir:
        return False, "Could not find 'Black Desert' folder in Documents."

    targets = ["UserCache", "Cache", "xcache"] # xcache sometimes exists too
    deleted_count = 0
    errors = []

    for name in targets:
        target_path = bdo_dir / name
        if target_path.exists():
            try:
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()
                deleted_count += 1
            except Exception as e:
                errors.append(f"{name}: {e}")

    if errors:
        return False, f"Errors: {'; '.join(errors)}"
    
    if deleted_count == 0:
        return True, "Cache already clean."

    return True, f"Successfully cleared {deleted_count} cache folders."
