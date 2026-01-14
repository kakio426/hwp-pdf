# Feature Plan: Frontend UI Implementation

## Overview & Objectives
**Goal**: Create a modern, premium-feeling Drag & Drop web interface for HWP to PDF conversion.
**Stack**: Vanilla HTML/CSS/JS (No heavy frameworks), Jest for testing logic.
**Aesthetics**: Glassmorphism, animations, responsive design.

## User Review Required
> [!NOTE]
> This plan introduces `npm` usage for running frontend tests (Jest).
> The UI will be served directly by FastAPI from the `static/` directory.

---

## Phase Breakdown

### Phase 5: Static UI Foundation
**Goal**: Create the visual structure and styling without logic.
**Test Strategy**: Visual verification + DOM Structure tests (Node script).
**Tasks**:
1.  **[RED]** Create test script `tests/test_ui_structure.js` checking for ID presence (`drop-zone`, `progress-bar`, etc.).
2.  **[GREEN]** Implement `static/index.html` and `static/style.css` with premium design variables.
3.  **[REFACTOR]** Optimize CSS using variables for theming.
**Quality Gate**:
- [ ] `node tests/test_ui_structure.js` passes
- [ ] UI looks correct in browser (manual check)
**Coverage Target**: 100% of required IDs present.

### Phase 6: Frontend Logic (TDD)
**Goal**: Implement file upload, polling, and download logic in isolation.
**Test Strategy**: Unit tests using `jest` for `api.js` and `ui.js`.
**Tasks**:
1.  **[RED]** Initialize npm and install `jest`. Write failing tests for `uploadFile` and `pollStatus`.
2.  **[GREEN]** Implement `static/js/api.js` (API wrapper) and `static/js/ui.js` (DOM manipulation).
3.  **[REFACTOR]** Extract configuration (API URLs) to a config object.
**Quality Gate**:
- [ ] `npm test` passes
**Coverage Target**: >90% branch coverage for `api.js`.

### Phase 7: Integration & Polish
**Goal**: Connect UI to Backend and add "Wow" factors (animations).
**Test Strategy**: End-to-End manual verification.
**Tasks**:
1.  **[RED]** Update FastAPI `main.py` to serve static files. Test that `/` returns 404 (initially).
2.  **[GREEN]** Mount `StaticFiles`. Add "confetti" or success animation on completion.
3.  **[REFACTOR]** Ensure error states look "premium" (toast notifications).
**Quality Gate**:
- [ ] Full flow: Drag file -> Progress bar -> Success -> Download works
- [ ] Aesthetics meet "Premium" standard

## Risk Assessment
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CORS issues | Low | High | API handles CORS (already configured) |
| Large file uploads | Medium | Medium | Add client-side size check (e.g. 50MB limit) |
| UI freezes | Low | Medium | Use async/await properly, show loading states |

## Verification Protocol
1. **Unit**: `npm test`
2. **Structure**: `node tests/test_ui_structure.js`
3. **Manual**: Open `http://localhost:8000` and convert a file.
