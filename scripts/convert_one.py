#!/usr/bin/env python
"""
CLI script for converting a single HWP file to PDF.

Usage:
    python scripts/convert_one.py input.hwp
    python scripts/convert_one.py input.hwp output.pdf
"""
import sys
import argparse
import logging
from pathlib import Path

# Add src to path for local development
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.hwp_converter import HwpToPdfConverter, HwpConverterError


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Convert HWP file to PDF using Hancom Office automation"
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to the input HWP file",
    )
    parser.add_argument(
        "output",
        type=str,
        nargs="?",
        default=None,
        help="Path for the output PDF (optional, defaults to same name with .pdf)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--visible",
        action="store_true",
        help="Show HWP window during conversion (for debugging)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout in seconds (default: 30)",
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    input_path = Path(args.input).resolve()
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    logger.info(f"Converting: {input_path}")
    
    try:
        with HwpToPdfConverter(timeout=args.timeout, visible=args.visible) as converter:
            output_path = converter.convert(str(input_path), args.output)
            logger.info(f"Success! Created: {output_path}")
            return 0
            
    except HwpConverterError as e:
        logger.error(f"Conversion failed: {e}")
        return 1
    except KeyboardInterrupt:
        logger.warning("Conversion interrupted by user")
        return 130
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
