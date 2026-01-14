#!/usr/bin/env python
"""
Setup script to register HWP security module in Windows registry.

This script must be run once before using the HWP converter to prevent
security popups from blocking automation.

Usage:
    python scripts/setup_registry.py
"""
import sys
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hwp_converter.registry import (
    check_security_module_registered,
    register_security_module,
)


def main() -> int:
    """Main entry point."""
    print("HWP Security Module Setup")
    print("=" * 40)
    
    if check_security_module_registered():
        print("✓ Security module is already registered.")
        print("  No action needed.")
        return 0
    
    print("Security module is NOT registered.")
    print("Attempting to register...")
    
    if register_security_module():
        print("✓ Security module registered successfully!")
        print("  HWP automation should now work without popups.")
        return 0
    else:
        print("✗ Failed to register security module.")
        print("  Try running this script as Administrator.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
