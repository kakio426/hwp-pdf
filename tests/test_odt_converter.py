import os
import pytest
from unittest.mock import patch, MagicMock
from src.odt_converter.core import OdtToPdfConverter, OdtConversionError

class TestOdtToPdfConverter:
    @patch("src.odt_converter.core.Path")
    @patch("subprocess.run")
    def test_convert_success(self, mock_run, mock_path):
        # Arrange
        converter = OdtToPdfConverter()
        input_path = "C:\\test\\input.odt"
        output_path = "C:\\test\\output.pdf"
        
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock creating Path objects
        mock_input_path_obj = MagicMock()
        mock_input_path_obj.stem = "input"
        mock_output_path_obj = MagicMock()
        mock_output_dir_obj = MagicMock()
        mock_output_path_obj.parent = mock_output_dir_obj
        
        # Create persistent mocks
        input_mock = MagicMock()
        input_mock.stem = "input"
        input_mock.__str__.return_value = input_path
        
        output_mock = MagicMock()
        output_mock.parent = mock_output_dir_obj
        output_mock.__str__.return_value = output_path
        
        # Side effect for Path constructor
        def path_side_effect(arg):
            if str(arg) == input_path:
                return input_mock
            if str(arg) == output_path:
                return output_mock
            
            # For other paths (like output dir)
            new_mock = MagicMock()
            new_mock.__str__.return_value = str(arg)
            return new_mock
            
        mock_path.side_effect = path_side_effect
        
        # Determine expected output path logic
        mock_expected_output = MagicMock()
        mock_output_dir_obj.__truediv__.return_value = mock_expected_output
        mock_expected_output.exists.return_value = True # Simulate PDF created
        
        # Configure output_mock existence check
        output_mock.exists.return_value = False 

        # Act
        result = converter.convert(input_path, output_path)

        # Assert
        assert result == output_path
        mock_run.assert_called_once()
        mock_expected_output.rename.assert_called_with(output_mock)

    @patch("subprocess.run")
    def test_convert_failure(self, mock_run):
        # Arrange
        converter = OdtToPdfConverter()
        mock_run.side_effect = Exception("LibreOffice not found")

        # Act & Assert
        with pytest.raises(OdtConversionError):
            converter.convert("input.odt", "output.pdf")
