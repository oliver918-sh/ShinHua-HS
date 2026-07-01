from __future__ import annotations

import html
import json
import re
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path.home() / "Desktop" / "\u65b0\u5316\u9ad8\u4e2d"
OUT = ROOT / "assets" / "moments"
GALLERY = ROOT / "gallery.html"
INDEX = ROOT / "index.html"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG", ".WEBP"}


def slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or fallback


def web_image(src: Path, dest: Path) -> tuple[int, int]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
        image.save(dest, "JPEG", quality=78, optimize=True, progressive=True)
        return image.size


def collect_albums() -> list[dict]:
    OUT.mkdir(parents=True, exist_ok=True)
    albums: dict[str, dict] = {}
    for src in sorted(SOURCE.rglob("*")):
        if not src.is_file() or src.suffix not in IMAGE_EXTS:
            continue
        album_name = src.parent.name
        album = albums.setdefault(
            album_name,
            {
                "title": album_name,
                "slug": slugify(album_name, f"album-{len(albums) + 1}"),
                "items": [],
            },
        )
        dest = OUT / album["slug"] / f"{src.stem}.jpg"
        width, height = web_image(src, dest)
        album["items"].append(
            {
                "src": dest.relative_to(ROOT).as_posix(),
                "alt": f"{album_name} {src.stem}",
                "width": width,
                "height": height,
            }
        )
    return list(albums.values())


def build_gallery(albums: list[dict]) -> None:
    album_nav = "\n".join(
        f'<a href="#{html.escape(album["slug"])}">{html.escape(album["title"])} <span>{len(album["items"])}</span></a>'
        for album in albums
    )
    album_sections = []
    for album in albums:
        items = "\n".join(
            f'''<figure class="gallery-card">
              <img loading="lazy" src="{html.escape(item["src"])}" alt="{html.escape(item["alt"])}" />
            </figure>'''
            for item in album["items"]
        )
        album_sections.append(
            f'''<section class="gallery-section" id="{html.escape(album["slug"])}">
          <div class="gallery-heading">
            <p>{len(album["items"])} 张照片</p>
            <h2>{html.escape(album["title"])}</h2>
          </div>
          <div class="gallery-grid">
            {items}
          </div>
        </section>'''
        )

    GALLERY.write_text(
        f'''<!doctype html>
<html lang="zh-Hans">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>生活点滴照片墙 · 新化高中65年级</title>
    <meta name="description" content="新化高中65年级同学生活点滴照片墙。" />
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body class="gallery-page">
    <header class="site-header gallery-header" aria-label="照片墙菜单">
      <a class="brand" href="index.html">新化高中 65年级</a>
      <nav>
        <a href="index.html#moments">生活点滴</a>
        <a href="index.html#contact">联系</a>
      </nav>
    </header>
    <main>
      <section class="gallery-hero">
        <p class="eyebrow">Moments</p>
        <h1>生活点滴照片墙</h1>
        <p>这里整理桌面「新化高中」文件夹里的照片，方便同学按相册慢慢查看。</p>
        <div class="album-nav">
          {album_nav}
        </div>
      </section>
      {"".join(album_sections)}
    </main>
    <footer>
      <p>新化高中 65年级 · 生活点滴照片墙</p>
    </footer>
  </body>
</html>
''',
        encoding="utf-8",
    )


def update_index(albums: list[dict]) -> None:
    total = sum(len(album["items"]) for album in albums)
    cards = "\n".join(
        f'''<article class="moment-album-card">
              <img src="{html.escape(album["items"][0]["src"])}" alt="{html.escape(album["title"])}" />
              <div>
                <span class="label">{len(album["items"])} 张照片</span>
                <strong>{html.escape(album["title"])}</strong>
              </div>
            </article>'''
        for album in albums[:6]
        if album["items"]
    )
    text = INDEX.read_text(encoding="utf-8")
    replacement = f'''<section class="section campus" id="moments">
        <div class="section-heading">
          <p class="eyebrow">Moments</p>
          <h2>生活点滴</h2>
        </div>
        <div class="moments-intro">
          <p>
            已整理桌面「新化高中」文件夹里的照片，共 {total} 张。点开照片墙，可以按照相册查看这些年的聚会、春酒、老照片与同学近况。
          </p>
          <a class="button primary" href="gallery.html">查看全部照片</a>
        </div>
        <div class="moment-albums">
          {cards}
        </div>
      </section>'''
    text = re.sub(
        r'<section class="section campus" id="moments">.*?</section>\s*\n\s*<section class="visit"',
        replacement + "\n\n      <section class=\"visit\"",
        text,
        flags=re.S,
    )
    INDEX.write_text(text, encoding="utf-8")


def main() -> None:
    albums = collect_albums()
    (ROOT / "assets" / "moments.json").write_text(
        json.dumps(albums, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    build_gallery(albums)
    update_index(albums)
    print(f"albums={len(albums)} photos={sum(len(album['items']) for album in albums)}")


if __name__ == "__main__":
    main()
