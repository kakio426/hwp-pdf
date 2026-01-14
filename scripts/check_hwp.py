
import sys
import os

try:
    import win32com.client
    print("win32com imported successfully")
except ImportError:
    print("win32com not found")
    sys.exit(0)

def check_hwp():
    try:
        hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
        print("HWP Object created successfully")
        hwp.Quit()
    except Exception as e:
        print(f"Failed to create HWP Object: {e}")

if __name__ == "__main__":
    check_hwp()
