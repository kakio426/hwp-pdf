
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.odt_converter.core import OdtToPdfConverter

def reproduction():
    converter = OdtToPdfConverter()
    try:
        # We don't actually need a file if we just want to see it fail finding the executable
        # But convert checks for file existence usually? 
        # looking at core.py: input_file = Path(input_path); ... subprocess.run
        # It doesn't explicitly check if input exists before running subprocess, but subprocess might error.
        # However, subprocess will fail FIRST if executable is missing.
        converter.convert("dummy.odt", "dummy.pdf")
        print("Success (Unexpected)")
    except Exception as e:
        print(f"Caught expected error: {e}")

if __name__ == "__main__":
    reproduction()
