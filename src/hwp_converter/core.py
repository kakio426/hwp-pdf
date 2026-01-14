"""Core HWP to PDF converter using Windows OLE Automation"""
import os
import logging
import subprocess
from pathlib import Path
from typing import Optional

from .exceptions import HwpInitializationError, HwpConversionError, HwpTimeoutError
from .registry import ensure_security_module

logger = logging.getLogger(__name__)

# PDF export format identifier for HWP
PDF_FORMAT = "PDF"


class HwpToPdfConverter:
    """
    Converts HWP files to PDF using Hancom Office OLE Automation.
    
    This class manages the HWP COM object lifecycle and provides
    a simple interface for file conversion.
    
    Usage:
        with HwpToPdfConverter() as converter:
            converter.convert("input.hwp", "output.pdf")
    
    Or manually:
        converter = HwpToPdfConverter()
        try:
            converter.convert("input.hwp", "output.pdf")
        finally:
            converter.close()
    """
    
    def __init__(self, timeout: int = 30, visible: bool = False):
        """
        Initialize the HWP converter.
        
        Args:
            timeout: Maximum seconds to wait for conversion (default: 30)
            visible: If True, show HWP window during conversion (default: False)
        """
        self.timeout = timeout
        self.visible = visible
        self._hwp = None
        self._initialized = False
        
    def _ensure_initialized(self) -> None:
        """Lazily initialize the HWP COM object."""
        if self._initialized:
            return
            
        import win32com.client
        import pythoncom
        
        # Initialize COM for this thread
        pythoncom.CoInitialize()
        
        # Ensure security module is registered
        ensure_security_module()
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Use Dispatch instead of EnsureDispatch to avoid gencache issues
                # HWPFrame.HwpObject is theProgID
                self._hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
                
                # Register security module with HWP instance
                self._hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
                
                # Set visibility
                self._hwp.XHwpWindows.Item(0).Visible = self.visible
                
                self._initialized = True
                logger.info("HWP automation object initialized successfully")
                return
                
            except Exception as e:
                logger.warning(f"HWP initialization attempt {attempt + 1} failed: {e}")
                self.kill_hwp_process() # Kill any zombie process before retry
                if attempt == max_retries - 1:
                    error_msg = str(e)
                    if "Class not registered" in error_msg:
                        raise HwpInitializationError(
                            "HWP is not installed or not registered for automation. "
                            "Please install Hancom Office 2020 or later."
                        ) from e
                    raise HwpInitializationError(f"Failed to initialize HWP: {error_msg}") from e

    
    def convert(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Convert an HWP file to PDF.
        
        Args:
            input_path: Path to the source HWP file
            output_path: Path for the output PDF (optional, defaults to same name with .pdf)
        
        Returns:
            Path to the created PDF file
        
        Raises:
            FileNotFoundError: If input file doesn't exist
            HwpConversionError: If conversion fails
            HwpTimeoutError: If conversion exceeds timeout
        """
        input_path = Path(input_path).resolve()
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if not input_path.suffix.lower() in ('.hwp', '.hwpx'):
            raise ValueError(f"Invalid file type: {input_path.suffix}. Expected .hwp or .hwpx")
        
        if output_path is None:
            output_path = input_path.with_suffix('.pdf')
        else:
            output_path = Path(output_path).resolve()
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._ensure_initialized()
        
        try:
            logger.info(f"Opening file: {input_path}")
            
            # Open the HWP file
            # Determine format based on extension
            fmt = "HWP"
            if str(input_path).lower().endswith('.hwpx'):
                fmt = "HWPX"

            if not self._hwp.Open(str(input_path), fmt, "forceopen:true"):
                # If specific format failed, try auto-detect (empty string)
                logger.warning(f"Failed to open with format '{fmt}', trying auto-detect")
                if not self._hwp.Open(str(input_path), "", "forceopen:true"):
                     raise HwpConversionError(f"Failed to open file: {input_path}")
            
            logger.info(f"Saving as PDF: {output_path}")
            
            # Configure PDF export parameters
            self._hwp.HAction.GetDefault("FileSaveAs_S", self._hwp.HParameterSet.HFileOpenSave.HSet)
            self._hwp.HParameterSet.HFileOpenSave.filename = str(output_path)
            self._hwp.HParameterSet.HFileOpenSave.Format = PDF_FORMAT
            
            # Execute save
            if not self._hwp.HAction.Execute("FileSaveAs_S", self._hwp.HParameterSet.HFileOpenSave.HSet):
                raise HwpConversionError("Failed to save PDF")
            
            # Close document without saving HWP changes
            self._hwp.Clear(1)  # 1 = don't save
            
            if not output_path.exists():
                raise HwpConversionError(f"PDF file was not created: {output_path}")
            
            logger.info(f"Conversion successful: {output_path}")
            return str(output_path)
            
        except HwpConversionError:
            raise
        except Exception as e:
            raise HwpConversionError(f"Conversion failed: {e}") from e
    
    def close(self) -> None:
        """Release HWP COM resources."""
        if self._hwp is not None:
            try:
                self._hwp.Quit()
            except Exception as e:
                logger.warning(f"Error while closing HWP: {e}")
            finally:
                self._hwp = None
                self._initialized = False
                
                # Uninitialize COM
                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
                
                logger.info("HWP resources released")
    
    def kill_hwp_process(self) -> None:
        """Force kill any running hwp.exe processes."""
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
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self.close()
        
        # If there was an error, also try to kill zombie processes
        if exc_type is not None:
            self.kill_hwp_process()
