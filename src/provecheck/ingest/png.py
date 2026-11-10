"""A small PNG reader and writer, so ``provecheck crop`` works on PNG files with no
dependencies (sandboxes without PyMuPDF). 8-bit, non-interlaced images only."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from provecheck.ingest import IngestError

_MAGIC = b"\x89PNG\r\n\x1a\n"
_CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}


def _chunks(data: bytes):
    pos = len(_MAGIC)
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos : pos + 4])
        yield data[pos + 4 : pos + 8], data[pos + 8 : pos + 8 + length]
        pos += 12 + length


def _read(path: Path):
    data = path.read_bytes()
    if not data.startswith(_MAGIC):
        raise IngestError(f"{path} is not a PNG file")
    header, palette, extra, idat = None, None, [], []
    for kind, body in _chunks(data):
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            palette = body
        elif kind == b"tRNS":
            extra.append((kind, body))
        elif kind == b"IDAT":
            idat.append(body)
    width, height, depth, color, _, _, interlace = header
    if depth != 8 or interlace or color not in _CHANNELS:
        raise IngestError(
            "without PyMuPDF only 8-bit, non-interlaced PNG files can be cropped; "
            'install it with: pip install "provecheck[pdf]"'
        )
    bpp = _CHANNELS[color]
    raw, stride = zlib.decompress(b"".join(idat)), width * bpp
    rows, prev = [], bytearray(stride)
    for y in range(height):
        base = y * (stride + 1)
        ftype, line = raw[base], bytearray(raw[base + 1 : base + 1 + stride])
        for i in range(stride):  # undo the PNG row filter
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], (prev[i - bpp] if i >= bpp else 0)
            if ftype == 1:
                line[i] = (line[i] + a) & 255
            elif ftype == 2:
                line[i] = (line[i] + b) & 255
            elif ftype == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif ftype == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        rows.append(line)
        prev = line
    return width, height, color, bpp, palette, extra, rows


def size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:32]
    if not data.startswith(_MAGIC):
        raise IngestError(f"{path} is not a PNG file")
    return struct.unpack(">II", data[16:24])


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))


def crop(path: Path, box: tuple[int, int, int, int], upscale: int, out: Path) -> None:
    """Cut ``box`` (x0, y0, x1, y1 in pixels) and enlarge by a whole factor."""
    _, _, color, bpp, palette, extra, rows = _read(path)
    x0, y0, x1, y1 = box
    lines = []
    for row in rows[y0:y1]:
        cut = row[x0 * bpp : x1 * bpp]
        wide = b"".join(bytes(cut[i : i + bpp]) * upscale for i in range(0, len(cut), bpp))
        lines.extend([b"\x00" + wide] * upscale)
    header = struct.pack(">IIBBBBB", (x1 - x0) * upscale, (y1 - y0) * upscale, 8, color, 0, 0, 0)
    parts = [_MAGIC, _chunk(b"IHDR", header)]
    if palette is not None:
        parts.append(_chunk(b"PLTE", palette))
    parts.extend(_chunk(kind, body) for kind, body in extra)
    parts.append(_chunk(b"IDAT", zlib.compress(b"".join(lines), 6)))
    parts.append(_chunk(b"IEND", b""))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(b"".join(parts))
