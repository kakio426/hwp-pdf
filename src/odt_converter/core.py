import subprocess
import os
from pathlib import Path


from .utils import get_libreoffice_path

class OdtConversionError(Exception):
    pass

class OdtToPdfConverter:
    def convert(self, input_path: str, output_path: str) -> str:
        input_file = Path(input_path)
        output_file = Path(output_path)
        output_dir = output_file.parent
        
        libreoffice_cmd = get_libreoffice_path()
        if not libreoffice_cmd:
             raise OdtConversionError("LibreOffice/soffice executable not found in PATH or standard locations")

        # LibreOffice command
        # libreoffice --headless --convert-to pdf --outdir <dir> <input>
        # Note: LibreOffice output filename is determined by input filename.
        # We might need to rename it if output_path has a different name.
        
        cmd = [
            libreoffice_cmd, 
            "--headless", 
            "--convert-to", "pdf", 
            "--outdir", str(output_dir), 
            str(input_file)
        ]
        
        try:
            # On Windows, 'libreoffice' might not be in PATH. 
            # Users often have 'soffice' or full path.
            # We use the detected path.
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Expected output file
            expected_output = output_dir / (input_file.stem + ".pdf")
            
            if not expected_output.exists():
                 # Try 'soffice' if libreoffice failed (though check=True would catch it if command not found?)
                 # Actually subprocess would raise FileNotFoundError if executable is missing.
                 raise OdtConversionError("Output PDF not found after conversion")
                 
            # Rename if necessary (if requested output name is different)
            if expected_output != output_file:
                if output_file.exists():
                    output_file.unlink()
                expected_output.rename(output_file)
                
            return str(output_file)

        except subprocess.CalledProcessError as e:
            raise OdtConversionError(f"LibreOffice conversion failed: {e.stderr.decode()}")
        except FileNotFoundError:
             raise OdtConversionError("LibreOffice/soffice executable not found in PATH")
        except Exception as e:
            raise OdtConversionError(f"Unexpected error: {str(e)}")
