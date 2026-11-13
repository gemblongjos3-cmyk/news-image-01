#!/usr/bin/env python3
"""Deterministic entry for make.fun bounty news-image-01.

The picture (entry.jpg, bundled in this repository) sums up the world news
of Friday 13 November 2026 in one editorial illustration: a chip glowing
above an empty chief executive's chair with a leather jacket on it, a peace
table handshake over a world map, a tanker passing a naval mine in a narrow
strait, and a night skyline of office screens. This program validates the
picture and writes its bytes, unchanged, to /output/entry.png.
Standard library only; deterministic.
"""
import hashlib
import os
import struct
import sys

MAX_BYTES = 1048576
MAX_SIDE = 1024
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"
PNG_SIG = b"\x89PNG\r\n\x1a\n"
ASSET = "entry.jpg"


def find_asset():
    """Locate the bundled picture next to this program or in /bot."""
    here = os.path.dirname(os.path.abspath(__file__))
    for path in (os.path.join(here, ASSET), os.path.join("/bot", ASSET), ASSET):
        if os.path.isfile(path):
            return path
    raise FileNotFoundError(ASSET + " not found beside the program or in /bot")


def image_dimensions(data):
    """(width, height) parsed with the standard library only."""
    if data.startswith(PNG_SIG):
        if len(data) < 24 or data[12:16] != b"IHDR":
            raise ValueError("PNG without an IHDR chunk")
        return struct.unpack(">II", data[16:24])
    if data.startswith(JPEG_SOI):
        i = 2
        while i + 9 < len(data):
            if data[i] != 0xFF:
                raise ValueError("JPEG segment out of alignment")
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                height, width = struct.unpack(">HH", data[i + 5 : i + 9])
                return width, height
            i += 2 + struct.unpack(">H", data[i + 2 : i + 4])[0]
        raise ValueError("JPEG without a start-of-frame segment")
    raise ValueError("not a PNG or a JPEG")


def main():
    src = find_asset()
    with open(src, "rb") as fh:
        data = fh.read()
    if len(data) > MAX_BYTES:
        raise ValueError("picture exceeds the 1 MiB cap: %d bytes" % len(data))
    if data.startswith(JPEG_SOI) and not data.endswith(JPEG_EOI):
        raise ValueError("truncated JPEG (no end-of-image marker)")
    width, height = image_dimensions(data)
    if width > MAX_SIDE or height > MAX_SIDE:
        raise ValueError("picture exceeds 1024x1024: %dx%d" % (width, height))
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    with open(out_path, "wb") as fh:
        fh.write(data)
    digest = hashlib.sha256(data).hexdigest()
    with open(out_path, "rb") as fh:
        if hashlib.sha256(fh.read()).hexdigest() != digest:
            raise ValueError("written file does not match the bundled picture")
    print("news-image-01: wrote %s (%d bytes, %dx%d, sha256 %s)" % (out_path, len(data), width, height, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())

