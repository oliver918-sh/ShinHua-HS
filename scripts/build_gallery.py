from __future__ import annotations

import html
import json
import re
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path.home() / "Desktop" / "新化高中"
OUT = ROOT / "assets" / "moments"
INDEX = ROOT / "index.html"
GALLERY = ROOT / "gallery.html"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG", ".WEBP"}
OLD_PHOTO_ALBUMS = {"65級老照片", "65级老照片"}
TITLE_MAP = {"高中同学": "休闲娱乐"}


def display_title(folder_name: str) -> str:
    return TITLE_MAP.get(folder_name, folder_name)


def slug_for(folder_name: str, fallback: str) -> str:
    if folder_name in OLD_PHOTO_ALBUMS:
        return "65"
    if folder_name == "高中同学":
        return "leisure"
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", folder_name).strip("-").lower()
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

        folder_name = src.parent.name
        album = albums.setdefault(
            folder_name,
            {
                "folder": folder_name,
                "title": display_title(folder_name),
                "slug": slug_for(folder_name, f"album-{len(albums) + 1}"),
                "items": [],
            },
        )

        dest = OUT / album["slug"] / f"{src.stem}.jpg"
        width, height = web_image(src, dest)
        album["items"].append(
            {
                "src": dest.relative_to(ROOT).as_posix(),
                "alt": f"{album['title']} {src.stem}",
                "width": width,
                "height": height,
            }
        )
    return list(albums.values())


def image_figures(items: list[dict]) -> str:
    return "\n".join(
        f'''<figure class="gallery-card">
              <img loading="lazy" src="{html.escape(item["src"])}" alt="{html.escape(item["alt"])}" />
            </figure>'''
        for item in items
    )


def album_cards(albums: list[dict]) -> str:
    cards = []
    for album in albums:
        if not album["items"]:
            continue
        cover = album["items"][0]
        cards.append(
            f'''<article class="moment-album-card">
            <img src="{html.escape(cover["src"])}" alt="{html.escape(album["title"])}" />
            <div>
              <span class="label">{len(album["items"])} 张照片</span>
              <strong>{html.escape(album["title"])}</strong>
            </div>
          </article>'''
        )
    return "\n          ".join(cards)


def write_index(old_album: dict, moment_albums: list[dict]) -> None:
    total_moments = sum(len(album["items"]) for album in moment_albums)
    INDEX.write_text(
        f'''<!doctype html>
<html lang="zh-Hans">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>新化高中65年级同学照片</title>
    <meta name="description" content="新化高中65年级同学照片与生活点滴。" />
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <header class="site-header" aria-label="主菜单">
      <a class="brand" href="#top">新化高中 65年级</a>
      <nav>
        <a href="#photos">查看照片</a>
        <a href="#moments">生活点滴</a>
      </nav>
    </header>

    <main id="top">
      <section class="hero" aria-label="新化高中65年级同学照片">
        <img class="hero-image" src="assets/class-photo-65.jpg" alt="新化高中65年级同学老照片" />
        <div class="hero-overlay"></div>
        <div class="hero-content">
          <p class="eyebrow">65年级同学</p>
          <h1>新化高中同学照片与生活点滴</h1>
          <p class="hero-copy">
            把旧照片和这些年的相聚整理在一起，方便同学慢慢查看、回忆，也继续补上更多生活片段。
          </p>
          <div class="hero-actions">
            <a class="button primary" href="#photos">查看照片</a>
            <a class="button secondary" href="#moments">生活点滴</a>
          </div>
        </div>
      </section>

      <section class="section photos" id="photos">
        <div class="section-heading">
          <p class="eyebrow">Photos</p>
          <h2>查看照片</h2>
        </div>
        <div class="moments-intro">
          <p>
            这里显示桌面「新化高中」文件夹中「65级老照片」相册，共 {len(old_album["items"])} 张。
          </p>
        </div>
        <div class="gallery-grid">
          {image_figures(old_album["items"])}
        </div>
      </section>

      <section class="section campus" id="moments">
        <div class="section-heading">
          <p class="eyebrow">Moments</p>
          <h2>生活点滴</h2>
        </div>
        <div class="moments-intro">
          <p>
            这里整理同学聚会、春酒与休闲娱乐照片，共 {total_moments} 张。「65级老照片」已移到上方「查看照片」栏目。
          </p>
          <a class="button primary" href="gallery.html">查看全部生活点滴</a>
        </div>
        <div class="moment-albums">
          {album_cards(moment_albums)}
        </div>
      </section>
    </main>

    <footer>
      <p>新化高中 65年级 · 照片与生活点滴</p>
    </footer>
  </body>
</html>
''',
        encoding="utf-8",
    )


def write_gallery(moment_albums: list[dict]) -> None:
    album_nav = "\n".join(
        f'<a href="#{html.escape(album["slug"])}">{html.escape(album["title"])} <span>{len(album["items"])}</span></a>'
        for album in moment_albums
    )
    sections = []
    for album in moment_albums:
        sections.append(
            f'''<section class="gallery-section" id="{html.escape(album["slug"])}">
          <div class="gallery-heading">
            <p>{len(album["items"])} 张照片</p>
            <h2>{html.escape(album["title"])}</h2>
          </div>
          <div class="gallery-grid">
            {image_figures(album["items"])}
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
        <a href="index.html#photos">查看照片</a>
        <a href="index.html#moments">生活点滴</a>
      </nav>
    </header>
    <main>
      <section class="gallery-hero">
        <p class="eyebrow">Moments</p>
        <h1>生活点滴照片墙</h1>
        <p>这里整理同学聚会、春酒与休闲娱乐照片，方便同学按相册慢慢查看。</p>
        <div class="album-nav">
          {album_nav}
        </div>
      </section>
      {"".join(sections)}
    </main>
    <footer>
      <p>新化高中 65年级 · 生活点滴照片墙</p>
    </footer>
  </body>
</html>
''',
        encoding="utf-8",
    )


def main() -> None:
    albums = collect_albums()
    old_albums = [album for album in albums if album["folder"] in OLD_PHOTO_ALBUMS]
    if not old_albums:
        raise SystemExit("Missing 65级老照片 album")
    old_album = old_albums[0]
    moment_albums = [album for album in albums if album["folder"] not in OLD_PHOTO_ALBUMS]

    (ROOT / "assets" / "moments.json").write_text(
        json.dumps(
            {"photos_album": old_album, "moments_albums": moment_albums},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_index(old_album, moment_albums)
    write_gallery(moment_albums)
    print(
        f"photos={len(old_album['items'])} moments={sum(len(album['items']) for album in moment_albums)} albums={len(moment_albums)}"
    )


if __name__ == "__main__":
    main()
