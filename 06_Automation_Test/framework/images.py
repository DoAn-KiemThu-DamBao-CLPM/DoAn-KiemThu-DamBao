"""Generate test files: valid images, oversize images, disguised scripts."""
import io
from PIL import Image


def png(size=(8, 8), color=(255, 120, 160), pad_to=None) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, "PNG")
    data = buf.getvalue()
    if pad_to:
        assert pad_to >= len(data)
        data += b"\0" * (pad_to - len(data))      # trailing bytes: still a PNG for finfo (magic number based)
    return data


def jpg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (10, 200, 90)).save(buf, "JPEG")
    return buf.getvalue()


PHP_SCRIPT = b"<?php echo 'pwned'; system($_GET['c']); ?>"
HTML_SCRIPT = b"<html><script>alert(1)</script></html>"
GIF_POLYGLOT = b"GIF89a" + b"<?php echo 'polyglot'; ?>"
