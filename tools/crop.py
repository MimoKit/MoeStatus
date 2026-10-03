r"""按 1:1 从出图里裁一块，专门用来看字缘锐不锐。

被缩放过的预览看不出真实清晰度，评审时只看裁剪块。

    & <core-venv>\Scripts\python.exe tools\crop.py <in.png> <out.png> <x> <y> <w> <h>
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image


def main() -> int:
    if len(sys.argv) < 7:
        print("usage: crop.py <in.png> <out.png> <x> <y> <w> <h>")
        return 2
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    x, y, width, height = (int(value) for value in sys.argv[3:7])

    with Image.open(src) as img:
        size = img.size
        box = (x, y, min(x + width, size[0]), min(y + height, size[1]))
        img.crop(box).save(dst)
        print(f"[ok] {dst.name}  crop={box}  source={size}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
