# PLAN: Fix LibreOffice ODT & HWPX Conversion

**Note**: This plan follows the Feature Planner (SKILL.md) structure.

## Overview
The goal is to resolve the "Failed" status for ODT and HWPX to PDF conversions. The primary cause for ODT failure is that the `soffice.exe` (LibreOffice) executable is not in the system PATH, although it is installed at `C:\Program Files\LibreOffice\program\soffice.exe`. For HWPX, we need to verify if the existing HWP automation handles the `.hwpx` extension correctly.

## Architecture Decisions
- **Path Auto-detection**: Instead of requiring the user to modify system PATH, the application will automatically check common install locations for LibreOffice.
- **Fail-fast**: If LibreOffice is not found, the error message should explicitly state where it looked.

## Phase Breakdown

### Phase 1: Fix ODT Conversion (LibreOffice Path)
- **Goal**: Enable ODT to PDF conversion by correctly locating `soffice.exe`.
- **Test Strategy**: Unit test with mocked subprocess; Integration test with real file.
- **Tasks**:
    - [ ] **RED**: Create test that fails when `libreoffice` command is missing.
    - [ ] **GREEN**: Update `OdtToPdfConverter` to check `C:\Program Files\LibreOffice\program\soffice.exe` if default command fails.
    - [ ] **REFACTOR**: Extract path finding logic to a helper method.
- **Quality Gate**: 
    - [ ] ODT file converts to PDF successfully.

### Phase 2: Verify & Fix HWPX Conversion
- **Goal**: Ensure `.hwpx` files are converted successfully.
- **Test Strategy**: Integration test with sample `.hwpx` file.
- **Tasks**:
    - [ ] **RED**: Create test validation for `.hwpx` conversion capability.
    - [ ] **GREEN**: Inspect `HwpToPdfConverter` behavior with `.hwpx`. If it fails due to file dialogs or association, adjust the `Open` method arguments.
- **Quality Gate**:
    - [ ] HWPX file converts to PDF successfully.

## Verification Plan
1.  **Automated**: Run `tests/test_converters.py` (to be created).
2.  **Manual**: Restart server, upload ODT and HWPX files, verify "Completed" status and download resultant PDF.
