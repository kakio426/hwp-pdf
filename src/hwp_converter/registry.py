"""Registry utilities for HWP security module configuration"""
import winreg
import logging

logger = logging.getLogger(__name__)

# Registry path for Hancom security settings
HANCOM_REGISTRY_PATH = r"SOFTWARE\HNC\HwpAutomation\Modules"
SECURITY_MODULE_NAME = "FilePathCheckerModule"


def check_security_module_registered() -> bool:
    """
    Check if the FilePathCheckerModule is registered in the registry.
    
    Returns:
        True if the module is registered, False otherwise.
    """
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, HANCOM_REGISTRY_PATH) as key:
            try:
                winreg.QueryValueEx(key, SECURITY_MODULE_NAME)
                return True
            except FileNotFoundError:
                return False
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.warning(f"Failed to check registry: {e}")
        return False


def register_security_module() -> bool:
    """
    Register the FilePathCheckerModule to bypass security popups.
    
    This allows HWP automation to run without user interaction.
    
    Returns:
        True if registration succeeded, False otherwise.
    """
    try:
        # Create key path if it doesn't exist
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, HANCOM_REGISTRY_PATH) as key:
            winreg.SetValueEx(key, SECURITY_MODULE_NAME, 0, winreg.REG_SZ, "FilePathCheckerModule")
            logger.info("Security module registered successfully")
            return True
    except PermissionError:
        logger.error("Permission denied: Run as administrator to register security module")
        return False
    except Exception as e:
        logger.error(f"Failed to register security module: {e}")
        return False


def ensure_security_module() -> None:
    """
    Ensure the security module is registered. Register if not present.
    """
    if not check_security_module_registered():
        logger.info("Security module not found, attempting to register...")
        if not register_security_module():
            logger.warning(
                "Could not register security module. "
                "HWP may show security popups during automation."
            )
