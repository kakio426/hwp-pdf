"""Core HWP to PDF converter using Windows OLE Automation"""
import os
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

from .exceptions import HwpInitializationError, HwpConversionError, HwpTimeoutError
from .registry import ensure_security_module

logger = logging.getLogger(__name__)

PDF_FORMAT = "PDF"


class HwpToPdfConverter:
    """
    Converts HWP files to PDF using Hancom Office OLE Automation.
    """

    def __init__(self, timeout: int = 30, visible: bool = False):
        self.timeout = timeout
        self.visible = visible
        self._hwp = None
        self._initialized = False

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        import win32com.client
        import pythoncom

        pythoncom.CoInitialize()
        ensure_security_module()

        max_retries = 2
        for attempt in range(max_retries):
            try:
                self._hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
                self._hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
                self._hwp.XHwpWindows.Item(0).Visible = self.visible
                self._initialized = True
                logger.info("HWP automation object initialized successfully")
                return
            except Exception as e:
                logger.warning(f"HWP initialization attempt {attempt + 1} failed: {e}")
                self.kill_hwp_process()
                if attempt == max_retries - 1:
                    error_msg = str(e)
                    if "Class not registered" in error_msg:
                        raise HwpInitializationError(
                            "HWP is not installed or not registered for automation. "
                            "Please install Hancom Office 2020 or later."
                        ) from e
                    raise HwpInitializationError(f"Failed to initialize HWP: {error_msg}") from e

    def _wait_for_output_pdf(self, output_path: Path) -> None:
        """Wait until PDF exists and file size is stable."""
        start = time.time()
        last_size = -1
        stable_count = 0

        while time.time() - start <= self.timeout:
            if output_path.exists():
                try:
                    current_size = output_path.stat().st_size
                except OSError:
                    current_size = -1

                if current_size > 0 and current_size == last_size:
                    stable_count += 1
                    if stable_count >= 2:
                        return
                else:
                    stable_count = 0
                    last_size = current_size

            time.sleep(0.5)

        raise HwpTimeoutError(
            f"Timed out while waiting for PDF output (timeout={self.timeout}s): {output_path}"
        )

    def convert(self, input_path: str, output_path: Optional[str] = None) -> str:
        input_path = Path(input_path).resolve()

        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if input_path.suffix.lower() not in ('.hwp', '.hwpx'):
            raise ValueError(f"Invalid file type: {input_path.suffix}. Expected .hwp or .hwpx")

        if output_path is None:
            output_path = input_path.with_suffix('.pdf')
        else:
            output_path = Path(output_path).resolve()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_initialized()

        try:
            logger.info(f"Opening file: {input_path}")

            fmt = "HWPX" if str(input_path).lower().endswith('.hwpx') else "HWP"
            if not self._hwp.Open(str(input_path), fmt, "forceopen:true"):
                logger.warning(f"Failed to open with format '{fmt}', trying auto-detect")
                if not self._hwp.Open(str(input_path), "", "forceopen:true"):
                    raise HwpConversionError(f"Failed to open file: {input_path}")

            logger.info(f"Saving as PDF: {output_path}")
            self._hwp.HAction.GetDefault("FileSaveAs_S", self._hwp.HParameterSet.HFileOpenSave.HSet)
            self._hwp.HParameterSet.HFileOpenSave.filename = str(output_path)
            self._hwp.HParameterSet.HFileOpenSave.Format = PDF_FORMAT

            if not self._hwp.HAction.Execute("FileSaveAs_S", self._hwp.HParameterSet.HFileOpenSave.HSet):
                raise HwpConversionError("Failed to save PDF")

            self._wait_for_output_pdf(output_path)

            try:
                self._hwp.Clear(1)
            except Exception as clear_err:
                logger.warning(f"Clear() failed after save: {clear_err}")

            logger.info(f"Conversion successful: {output_path}")
            return str(output_path)

        except (HwpConversionError, HwpTimeoutError):
            raise
        except Exception as e:
            raise HwpConversionError(f"Conversion failed: {e}") from e

    def close(self) -> None:
        if self._hwp is not None:
            try:
                self._hwp.Quit()
            except Exception as e:
                logger.warning(f"Error while closing HWP: {e}")
            finally:
                self._hwp = None
                self._initialized = False
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
                logger.info("HWP resources released")

    def kill_hwp_process(self) -> None:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", "hwp.exe"],
                capture_output=True,
                timeout=5
            )
            logger.info("Killed hwp.exe process")
        except Exception as e:
            logger.warning(f"Failed to kill hwp.exe: {e}")

    def __enter__(self) -> "HwpToPdfConverter":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
        if exc_type is not None:
            self.kill_hwp_process()
