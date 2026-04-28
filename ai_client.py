import hashlib
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import google.generativeai as genai


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model_name: str = "gemini-flash-lite-latest"
    transport: Optional[str] = None
    timeout_s: float = 20.0
    temperature: float = 0.0
    max_output_tokens_cap: int = 1024


class SqliteCache:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()

        db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS responses (
                    cache_key TEXT PRIMARY KEY,
                    mode TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    input_sha256 TEXT NOT NULL,
                    input_len INTEGER NOT NULL,
                    output_text TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    latency_ms REAL
                );
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_responses_created_at ON responses(created_at);"
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=2.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def get(self, cache_key: str) -> Optional[str]:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT output_text FROM responses WHERE cache_key = ?;", (cache_key,)
            ).fetchone()
        return None if row is None else str(row[0])

    def set(
        self,
        cache_key: str,
        mode: str,
        model_name: str,
        input_sha256: str,
        input_len: int,
        output_text: str,
        latency_ms: Optional[float],
    ) -> None:
        now = time.time()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO responses (
                    cache_key, mode, model_name, input_sha256, input_len,
                    output_text, created_at, latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    cache_key,
                    mode,
                    model_name,
                    input_sha256,
                    int(input_len),
                    output_text,
                    float(now),
                    None if latency_ms is None else float(latency_ms),
                ),
            )


class GeminiService:
    def __init__(self, config: GeminiConfig, cache: Optional[SqliteCache] = None) -> None:
        self._config = config

        genai.configure(
            api_key=config.api_key,
            transport=config.transport,
        )

        self._model = genai.GenerativeModel(
            model_name=config.model_name,
            generation_config={
                "temperature": config.temperature,
                "max_output_tokens": config.max_output_tokens_cap,
            },
        )

        self._cache = cache

    @staticmethod
    def _normalize_text(text: str) -> str:
        # Keep semantics identical while stabilizing cache keys across apps.
        return str(text).replace("\r\n", "\n").replace("\r", "\n").strip()

    def _make_cache_key(self, mode: str, text: str) -> Tuple[str, str]:
        normalized = self._normalize_text(text)
        raw_key = f"{mode}\0{self._config.model_name}\0{normalized}".encode("utf-8")
        sha = hashlib.sha256(raw_key).hexdigest()
        cache_key = f"v1:{sha}"
        input_sha = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return cache_key, input_sha

    def _dynamic_max_tokens(self, mode: str, text: str) -> int:
        # Rough heuristic: tokens ~= chars/4. Keep a floor for short replies.
        n_chars = max(1, len(text))
        approx = int(n_chars / 4) + 96
        if mode == "translate":
            approx += 64
        return max(128, min(self._config.max_output_tokens_cap, approx))

    def generate(self, mode: str, selected_text: str) -> Tuple[str, bool, float]:
        normalized = self._normalize_text(selected_text)
        if not normalized:
            return "", False, 0.0

        cache_key, input_sha = self._make_cache_key(mode, normalized)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached, True, 0.0

        if mode == "translate":
            prompt = (
                "Translate to English. Return ONLY the translation, no extra text.\n\n"
                + normalized
            )
        else:
            prompt = (
                "Fix grammar and clarity. Return ONLY the corrected text, no extra text.\n\n"
                + normalized
            )

        max_tokens = self._dynamic_max_tokens(mode, normalized)
        start = time.perf_counter()
        response = self._model.generate_content(
            prompt,
            generation_config={
                "temperature": self._config.temperature,
                "max_output_tokens": max_tokens,
            },
            request_options={"timeout": self._config.timeout_s},
        )
        latency_ms = (time.perf_counter() - start) * 1000.0

        output = (response.text or "").strip()
        if self._cache is not None and output:
            self._cache.set(
                cache_key=cache_key,
                mode=mode,
                model_name=self._config.model_name,
                input_sha256=input_sha,
                input_len=len(normalized),
                output_text=output,
                latency_ms=latency_ms,
            )

        return output, False, latency_ms


def build_default_service() -> Optional[GeminiService]:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        return None

    model_name = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest").strip() or "gemini-flash-lite-latest"
    transport = os.environ.get("GEMINI_TRANSPORT")
    transport = (transport.strip() if transport else None) or None

    timeout_s = float(os.environ.get("GEMINI_TIMEOUT_S", "60"))

    cache_path = Path(os.environ.get("AI_REWRITE_CACHE_PATH", str(Path(".cache") / "ai_cache.sqlite")))

    cache = SqliteCache(cache_path)

    # If user didn't specify a transport, prefer REST first (often lower latency / fewer gRPC issues on Windows).
    if transport is None:
        try:
            config = GeminiConfig(
                api_key=api_key,
                model_name=model_name,
                transport="rest",
                timeout_s=timeout_s,
            )
            return GeminiService(config=config, cache=cache)
        except Exception:
            pass

    config = GeminiConfig(
        api_key=api_key,
        model_name=model_name,
        transport=transport,
        timeout_s=timeout_s,
    )
    return GeminiService(config=config, cache=cache)
