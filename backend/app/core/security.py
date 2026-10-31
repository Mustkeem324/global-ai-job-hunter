import re
import ipaddress
from urllib.parse import urlparse
from typing import Optional

# High-risk patterns in job descriptions or external payloads
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?guidelines",
    r"system\s*:\s*you\s+are",
    r"output\s+the\s+system\s+prompt",
    r"send\s+(your\s+)?(api\s+key|credentials|token)",
    r"bypass\s+all\s+filters"
]

def sanitize_untrusted_text(text: Optional[str]) -> str:
    """Sanitize untrusted external job postings or metadata."""
    if not text:
        return ""
    cleaned = str(text)
    # Check for known prompt-injection markers and neutralize
    for pat in INJECTION_PATTERNS:
        cleaned = re.sub(pat, "[BLOCKED_INJECTION_PATTERN]", cleaned, flags=re.IGNORECASE)
    # Strip null bytes and control characters
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() or ch in ("\n", "\r", "\t"))
    return cleaned.strip()

def is_safe_external_url(url: Optional[str]) -> bool:
    """Validate external application and source URLs against SSRF."""
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        # Block localhost and private IP addresses
        if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            return False
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            # Domain name, not a raw IP
            pass
        return True
    except Exception:
        return False
