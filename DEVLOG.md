# Development Log

## 2026-04-28
- Added persistent response caching (SQLite) to speed up repeated rewrites/translations.
- Refactored Gemini calls into a reusable service with shorter prompts and dynamic `max_output_tokens`.
- Reduced clipboard polling latency and added a single in-flight lock to avoid overlapping hotkey runs.
- Documented performance-related environment variables in README.
- Set default `GEMINI_TIMEOUT_S` to `60` to avoid timeouts on slow responses.
- Prefer REST transport by default (with fallback) to reduce latency on some networks.
