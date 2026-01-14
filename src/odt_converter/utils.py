import shutil
import os
from pathlib import Path
from typing import Optional

def get_libreoffice_path() -> Optional[str]:
    """
    Find the LibreOffice executable (soffice).
    Checks PATH first, then common Windows installation directories.
    """
    # 1. Check PATH
    # 'libreoffice' is common on Linux, 'soffice' on Windows/Mac
    for cmd in ["libreoffice", "soffice"]:
        path = shutil.which(cmd)
        if path:
            return path

    # 2. Check common Windows paths
    common_paths = [
        Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "LibreOffice" / "program" / "soffice.exe",
        Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "LibreOffice" / "program" / "soffice.exe",
    ]
    
    for path in common_paths:
        if path.exists():
            return str(path)
            
    return None
