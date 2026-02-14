"""HWP to PDF 변환기 - pywebview 기반 경량 데스크톱 앱"""
import webview
import sys
import os
import json
import shutil
import tempfile
import multiprocessing
from pathlib import Path

from src.hwp_converter.core import HwpToPdfConverter


def get_app_data_dir():
    """앱 데이터 디렉터리 반환"""
    app_data = Path(os.environ.get("APPDATA", Path.home())) / "HwpToPdfConverter"
    app_data.mkdir(parents=True, exist_ok=True)
    return app_data


def get_static_dir():
    """static 디렉터리 경로 반환 (개발/PyInstaller 모두 지원)"""
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    return base / "static"


def _calculate_timeout_seconds(file_path: Path) -> int:
    """Scale conversion timeout by input file size."""
    try:
        size_mb = file_path.stat().st_size / (1024 * 1024)
    except Exception:
        return 90

    if size_mb < 5:
        return 90
    if size_mb < 20:
        return 180
    if size_mb < 50:
        return 300
    return 600


class Api:
    def __init__(self):
        self._window = None
        self._settings_path = get_app_data_dir() / "settings.json"

    def set_window(self, window):
        self._window = window

    def _load_settings(self):
        if self._settings_path.exists():
            try:
                return json.loads(self._settings_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_settings(self, settings):
        self._settings_path.write_text(
            json.dumps(settings, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def get_terms_accepted(self):
        """이전 이용약관 동의 여부 확인"""
        settings = self._load_settings()
        return settings.get("terms_accepted", False)

    def accept_terms(self):
        """이용약관 동의 상태 저장"""
        settings = self._load_settings()
        settings["terms_accepted"] = True
        self._save_settings(settings)
        return True

    def check_hwp_installed(self):
        """한글 설치 여부 확인 (레지스트리에서 COM 등록 확인)"""
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CLASSES_ROOT,
                "HWPFrame.HwpObject"
            )
            winreg.CloseKey(key)
            return True
        except Exception:
            return False

    def select_files(self):
        """파일 선택 다이얼로그 열기"""
        file_types = ('HWP 파일 (*.hwp;*.hwpx)',)
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=file_types
        )
        if result:
            return list(result)
        return []

    def convert_file(self, file_path):
        """단일 파일 변환 - 파일 경로를 받아 PDF로 변환"""
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return {"success": False, "error": "파일을 찾을 수 없습니다."}

            ext = file_path.suffix.lower()
            if ext not in ('.hwp', '.hwpx'):
                return {"success": False, "error": "지원하지 않는 파일 형식입니다."}

            temp_dir = Path(tempfile.mkdtemp(prefix="hwppdf_"))
            output_path = temp_dir / (file_path.stem + ".pdf")

            timeout_sec = _calculate_timeout_seconds(file_path)
            with HwpToPdfConverter(timeout=timeout_sec) as converter:
                converter.convert(str(file_path), str(output_path))

            if output_path.exists():
                return {
                    "success": True,
                    "pdf_path": str(output_path),
                    "filename": file_path.stem + ".pdf"
                }
            else:
                return {"success": False, "error": "PDF 파일이 생성되지 않았습니다."}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def save_file(self, source_pdf, suggested_name):
        """변환된 PDF 저장 다이얼로그"""
        source_path = Path(source_pdf)
        if not source_path.exists():
            return {"success": False, "error": "변환된 파일을 찾을 수 없습니다."}

        file_path = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            directory=str(Path.home() / "Downloads"),
            save_filename=suggested_name,
            file_types=('PDF 파일 (*.pdf)', '모든 파일 (*.*)')
        )

        if file_path:
            try:
                if isinstance(file_path, (list, tuple)):
                    file_path = file_path[0]
                shutil.copy2(source_path, file_path)
                return {"success": True, "path": file_path}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "cancelled"}


if __name__ == "__main__":
    multiprocessing.freeze_support()

    api = Api()

    static_dir = get_static_dir()
    index_path = static_dir / "index.html"

    window = webview.create_window(
        "HWP to PDF 변환기",
        str(index_path),
        width=800,
        height=650,
        resizable=True,
        js_api=api
    )

    api.set_window(window)

    webview.start()
    sys.exit()
