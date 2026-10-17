# Local verification — 2026-10-16

63 Python tests passed. The retained log includes exact test names.
9 legacy JavaScript and 10 schema-v2 annotation-core checks passed.
13 Chromium interaction checks passed, with no page JavaScript errors.

Browser tests used fresh isolated DOMs and a simulated Storage implementation
because navigation was administratively blocked. They are not proof of actual
localStorage persistence, live GitHub submission, cross-device behavior or iPad
Safari text selection. See browser-results.json and STATUS.md.

The example report was generated through the workbench and accepted by the Python
revision/anchor validator. It describes only the synthetic fixture.

The normal build was checked to exclude all synthetic snapshots and to retain an
empty reader catalogue. The opt-in demo build generated English/Japanese HTML and
EPUB, and legacy preview output. EPUB ZIP/XML and navigation tests passed; EPUBCheck
and actual Kindle rendering were unavailable. Workflow YAML syntax/permission
structure and local Markdown links were checked. The publishing helper was syntax
and no-change-plan checked; no GitHub account mutation or live workflow occurred.
