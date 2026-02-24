"""Generic webhook notification service for order and inventory alerts."""
import ipaddress
import json
import logging
import socket
from urllib.parse import urlparse
from datetime import datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.settings import AppSettings

logger = logging.getLogger(__name__)


def _is_allowed_webhook_url(webhook_url: str) -> bool:
    """Validate webhook URL: must be HTTPS and must not target private/internal IPs (SSRF prevention)."""
    try:
        parsed = urlparse(webhook_url)
        if parsed.scheme != "https":
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        # Resolve the hostname and reject private/loopback/link-local/reserved ranges
        try:
            ip_str = socket.gethostbyname(hostname)
            ip = ipaddress.ip_address(ip_str)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_unspecified:
                logger.warning("Blocked webhook URL targeting private/reserved IP: %s -> %s", hostname, ip_str)
                return False
        except (socket.gaierror, ValueError) as e:
            logger.warning("Failed to resolve webhook hostname '%s': %s", hostname, e)
            return False
        return True
    except Exception:
        return False


async def _send_webhook(url: str, event: str, content: str, data: dict) -> bool:
    """Send a webhook POST with a generic payload.

    Payload is compatible with Discord webhooks (``content`` field) and also
    includes structured ``event`` / ``data`` fields for custom receivers.
    """
    try:
        if not _is_allowed_webhook_url(url):
            logger.warning("Blocked non-HTTPS webhook URL")
            return False
        payload = {"event": event, "content": content, "data": data}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info("Webhook sent: event=%s", event)
            return True
    except httpx.HTTPError as e:
        logger.error("Failed to send webhook (event=%s): %s", event, e)
        return False
    except Exception as e:
        logger.error("Unexpected error sending webhook (event=%s): %s", event, e)
        return False


async def check_and_notify_overdue_orders(db: Session) -> int:
    """Check for orders due in N days (per settings) with status 'ordered'.

    Called by the scheduler once a day.  Returns the number of notifications sent.
    """
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()

    if not settings or not settings.webhook_enabled:
        logger.info("Webhook notifications disabled, skipping order-due check")
        return 0

    try:
        events = json.loads(settings.webhook_events or "[]")
    except (json.JSONDecodeError, TypeError):
        events = []

    if "order_due" not in events:
        return 0

    if not settings.webhook_url:
        logger.warning("Webhook URL not configured")
        return 0

    days = settings.webhook_order_due_days or 2
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    due_start = today + timedelta(days=days)
    due_end = today + timedelta(days=days + 1)

    orders = (
        db.query(Order)
        .filter(
            Order.status == "ordered",
            Order.due_date >= due_start,
            Order.due_date < due_end,
        )
        .all()
    )

    if not orders:
        logger.info("No orders due in %d days with 'ordered' status", days)
        return 0

    notifications_sent = 0
    for order in orders:
        order_name = order.custom_name if order.custom_name else f"Order #{order.id}"
        customer = order.customer_name if order.customer_name else "Unknown customer"
        due_date_str = order.due_date.strftime("%Y-%m-%d")

        content = (
            f"⚠️ **Order Alert** ⚠️\n"
            f"Order: {order_name}\n"
            f"Customer: {customer}\n"
            f"Due Date: {due_date_str}\n"
            f"Status: {order.status}\n"
            f"\nThis order is due in {days} day(s) and still in 'ordered' status!"
        )

        success = await _send_webhook(
            url=settings.webhook_url,
            event="order_due",
            content=content,
            data={
                "order_id": order.id,
                "order_name": order_name,
                "customer": customer,
                "due_date": due_date_str,
                "status": order.status,
                "days_until_due": days,
            },
        )
        if success:
            notifications_sent += 1

    logger.info("Sent %d order-due webhook notification(s)", notifications_sent)
    return notifications_sent


async def send_order_status_change_webhook(
    url: str, order: Order, old_status: str, new_status: str
) -> bool:
    """Fire an order_status_change webhook event."""
    order_name = order.custom_name if order.custom_name else f"Order #{order.id}"
    customer = order.customer_name if order.customer_name else "Unknown customer"

    content = (
        f"📦 **Order Status Changed**\n"
        f"Order: {order_name}\n"
        f"Customer: {customer}\n"
        f"Status: {old_status} → {new_status}"
    )

    return await _send_webhook(
        url=url,
        event="order_status_change",
        content=content,
        data={
            "order_id": order.id,
            "order_name": order_name,
            "customer": customer,
            "old_status": old_status,
            "new_status": new_status,
        },
    )


async def send_low_stock_webhook(
    url: str,
    spool_id: int,
    label: str,
    remaining_weight_g: float,
    tracking_id: str | None,
) -> bool:
    """Fire a low_stock webhook event for a spool."""
    content = (
        f"⚠️ **Low Stock Alert**\n"
        f"Spool: {label}\n"
        f"Remaining: {remaining_weight_g:.0f}g"
    )

    return await _send_webhook(
        url=url,
        event="low_stock",
        content=content,
        data={
            "spool_id": spool_id,
            "label": label,
            "remaining_weight_g": remaining_weight_g,
            "tracking_id": tracking_id,
        },
    )
