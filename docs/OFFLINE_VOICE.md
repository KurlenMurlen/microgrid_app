# Offline voice (Vosk) and hotword

The app supports voice control in Portuguese using either the browser engine (online) or an offline engine (Vosk WASM).

- When selecting the Offline (Vosk) engine in the UI, the browser will download a compact PT‑BR model (~50MB) from the same origin via `/api/vosk/model`.
- The server caches the ZIP on first request at `models/vosk-model-small-pt-0.3.zip` and serves it with `Cache-Control: public, max-age=2592000, immutable` so subsequent loads are instant for up to 30 days.
- Status endpoint: `/api/vosk/status` (used by the UI to show whether the model is cached and its size/mtime).
- The server uses retries, chunked streaming, and atomic writes to make the initial download robust. If the first attempt fails (network/timeout), reopening the voice overlay retries.
- Tip: To pre-warm the cache after deploy, request `/api/vosk/model` once (e.g., open in a browser tab).
- Hotword “ok microrrede” is available only with the browser (online) engine for security reasons; toggle it in the voice overlay.

Troubleshooting:
- If the overlay shows a failure when loading the model, check server logs; ensure outbound internet for the server to reach the default model URL or set `VOSK_MODEL_PT_URL` to a mirror you control.
- If the browser blocks the mic, grant permission in site settings and select a working input device.
- Brave/strict browsers: use the offline engine or switch off Shields for the site if online engine is blocked.
