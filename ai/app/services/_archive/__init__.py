"""
Archived service modules — kept here for git history and emergency reference.

Do NOT import from this package in production code. The active replacements:

- `politeness_service`           → `speech_analysis_service.analyze_politeness_compat`
- `sophisticated_speech_analyzer`→ `simple_speech_analyzer` (the simple analyzer is now the only active one)
- `speech_level_detector`        → integrated into `simple_speech_analyzer` regex banks

If a regression makes you reach for one of these files, please open an issue
to track the gap rather than re-introducing the import.
"""
