"""Unit tests for HWP converter core module (Mock-based)"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import os

from src.hwp_converter.core import HwpToPdfConverter
from src.hwp_converter.exceptions import HwpConversionError

class TestHwpToPdfConverter:
    """Tests for HwpToPdfConverter class with targeted patching"""

    @pytest.fixture(autouse=True)
    def mock_env(self):
        # 1. HWP OLE 객체 모킹
        self.mock_hwp = MagicMock()
        self.mock_hwp.Open.return_value = True
        self.mock_hwp.HAction.Execute.return_value = True
        self.mock_hwp.XHwpWindows.Item.return_value.Visible = False
        
        # 파일 생성 시뮬레이션
        def side_effect_execute(action, hset):
            if action == "FileSaveAs_S":
                fname = self.mock_hwp.HParameterSet.HFileOpenSave.filename
                if fname:
                    Path(fname).write_text("%PDF-mock")
                return True
            return True
        self.mock_hwp.HAction.Execute.side_effect = side_effect_execute

        # 2. 패치 대상 설정
        # core.py 내부의 win32com.client.gencache.EnsureDispatch를 패치해야 함
        # 하지만 core.py가 import를 함수 안에서 하므로, sys.modules를 패치하는 것이 가장 확실함
        
        import sys
        mock_win32 = MagicMock()
        mock_win32.client.gencache.EnsureDispatch.return_value = self.mock_hwp
        
        mock_pythoncom = MagicMock()

        patches = [
            patch.dict(sys.modules, {
                'win32com': mock_win32,
                'win32com.client': mock_win32.client,
                'win32com.client.gencache': mock_win32.client.gencache,
                'pythoncom': mock_pythoncom
            }),
            patch('src.hwp_converter.registry.ensure_security_module', return_value=None),
            patch('src.hwp_converter.registry.check_security_module_registered', return_value=True)
        ]

        for p in patches:
            p.start()
        
        yield
        
        for p in patches:
            p.stop()

    def test_convert_success(self, tmp_path):
        hwp_file = tmp_path / "test.hwp"
        hwp_file.write_text("content")
        pdf_path = tmp_path / "output.pdf"
        
        converter = HwpToPdfConverter()
        result = converter.convert(str(hwp_file), str(pdf_path))
        
        assert result == str(pdf_path)
        assert Path(pdf_path).exists()
        self.mock_hwp.Open.assert_called_once()
        converter.close()

    def test_convert_open_fails(self, tmp_path):
        hwp_file = tmp_path / "test.hwp"
        hwp_file.write_text("content")
        self.mock_hwp.Open.return_value = False
        
        converter = HwpToPdfConverter()
        with pytest.raises(HwpConversionError, match="Failed to open file"):
            converter.convert(str(hwp_file))
        converter.close()

    def test_close_releases_resources(self, tmp_path):
        hwp_file = tmp_path / "test.hwp"
        hwp_file.write_text("content")
        
        converter = HwpToPdfConverter()
        converter.convert(str(hwp_file))
        converter.close()
        
        self.mock_hwp.Quit.assert_called_once()

    def test_context_manager(self, tmp_path):
        hwp_file = tmp_path / "test.hwp"
        hwp_file.write_text("content")
        
        with HwpToPdfConverter() as converter:
            converter.convert(str(hwp_file))
            assert converter._hwp is not None
        
        assert converter._hwp is None
        self.mock_hwp.Quit.assert_called_once()

    def test_file_not_found(self):
        converter = HwpToPdfConverter()
        with pytest.raises(FileNotFoundError):
            converter.convert("non_existent.hwp")

    def test_invalid_extension(self, tmp_path):
        bad_file = tmp_path / "test.txt"
        bad_file.write_text("bad")
        converter = HwpToPdfConverter()
        with pytest.raises(ValueError, match="Invalid file type"):
            converter.convert(str(bad_file))
