"""Error alerting via Discord webhook.

Installs a Python logging handler that fires on ERROR/CRITICAL records and
sends a Discord message. Rate-limited to one alert per unique message per
5 minutes so a crash loop doesn't flood the channel.

Usage (called once at startup in main.py):
    from app.services.error_reporter import install_error_handler
    install_error_handler()
"""
import logging
import threading
import time
import traceback
from datetime import datetime, timezone

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Minimum seconds between alerts for the same error fingerprint
_RATE_LIMIT_SECONDS = 300  # 5 minutes


class DiscordErrorHandler(logging.Handler):
    """Logging handler that POSTs ERROR+ records to a Discord webhook."""

    def __init__(self, webhook_url: str):
        super().__init__(level=logging.ERROR)
        self.webhook_url = webhook_url
        self._last_sent: dict[str, float] = {}
        self._lock = threading.Lock()

    def _fingerprint(self, record: logging.LogRecord) -> str:
        """Deduplicate by logger name + first line of message."""
        first_line = record.getMessage().split("\n")[0][:120]
        return f"{record.name}:{first_line}"

    def _is_rate_limited(self, fingerprint: str) -> bool:
        now = time.monotonic()
        with self._lock:
            last = self._last_sent.get(fingerprint, 0)
            if now - last < _RATE_LIMIT_SECONDS:
                return True
            self._last_sent[fingerprint] = now
            return False

    def emit(self, record: logging.LogRecord) -> None:
        fingerprint = self._fingerprint(record)
        if self._is_rate_limited(fingerprint):
            return

        try:
            self._send(record)
        except Exception:
            # Never let error reporting crash the app
            pass

    def _send(self, record: logging.LogRecord) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        level_emoji = "🔴" if record.levelno >= logging.CRITICAL else "🟠"

        # Build message
        lines = [
            f"{level_emoji} **{record.levelname}** — `{record.name}`",
            f"**Time:** {ts}",
            f"**Env:** {settings.ENVIRONMENT}",
            f"```",
            record.getMessage()[:1000],
        ]

        if record.exc_info:
            tb = "".join(traceback.format_exception(*record.exc_info))
            lines.append(tb[-1500:])  # last 1500 chars of traceback

        lines.append("```")
        content = "\n".join(lines)

        # Discord message cap is 2000 chars
        if len(content) > 1990:
            content = content[:1987] + "```"

        httpx.post(
            self.webhook_url,
            json={"content": content},
            timeout=8.0,
        )


def install_error_handler() -> None:
    """Attach the Discord error handler to the root logger.

    No-op if ERROR_WEBHOOK_URL is not configured.
    """
    url = settings.ERROR_WEBHOOK_URL
    if not url:
        return

    # Basic URL validation — must be a Discord webhook
    if "discord.com/api/webhooks" not in url and "discordapp.com/api/webhooks" not in url:
        logger.warning("ERROR_WEBHOOK_URL is set but does not look like a Discord webhook — skipping")
        return

    handler = DiscordErrorHandler(url)
    handler.setFormatter(logging.Formatter("%(message)s"))

    # Attach to root logger so all ERROR+ records are captured
    root = logging.getLogger()
    root.addHandler(handler)
    logger.info("Discord error alerting enabled")
