from __future__ import annotations

import argparse
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Optional
import segno
from PIL import Image, ImageOps, ImageDraw, ImageColor

# ---------------------------------------------------------------------------
# Utility colori
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"^[0-9a-fA-F]{3}$|^[0-9a-fA-F]{6}$")


def normalize_color(col: str) -> Optional[str]:
    """Normalizza il colore in un formato accettato da Pillow/Segno.

    - Permette nomi CSS standard (via ``ImageColor.getrgb``)
    - Gestisce stringhe esadecimali con o senza «#» (3 o 6 cifre)
    - Accetta "transparent"/"none" (restituisce "transparent")
    """
    col = col.strip()
    if not col:
        raise argparse.ArgumentTypeError("Il colore non può essere vuoto")

    low = col.lower()
    if low in {"transparent", "none"}:  # sfondo trasparente
        return None

    if _HEX_RE.match(col):
        return f"#{col.lower()}"
    if col.startswith("#") and _HEX_RE.match(col[1:]):
        return f"#{col[1:].lower()}"

    try:
        ImageColor.getrgb(col)
        return col
    except ValueError as exc:  # pragma: no cover
        raise argparse.ArgumentTypeError(f"Colore non valido: {col}") from exc


# ---------------------------------------------------------------------------
# Utility path/output
# ---------------------------------------------------------------------------


def ensure_path_with_suffix(p: str, suffix: str, default_stem: str = "qr_logo") -> str:
    """
    Restituisce un percorso che termina con l'estensione `suffix`.
    - Se `p` è una cartella o termina con '/' o '\\', usa `default_stem` come nome file.
    - Se `p` non ha estensione, aggiunge `suffix`.
    - Se `p` ha un'altra estensione, la sostituisce con `suffix`.
    """
    path = Path(p)

    # Caso: path passato come directory (es. "output/" o "output\\")
    if str(p).endswith(("/", "\\")) or path.name == "":
        path = path / default_stem

    # Aggiunge o sostituisce l'estensione
    if path.suffix.lower() != suffix.lower():
        path = path.with_suffix(suffix)

    return str(path)


# ---------------------------------------------------------------------------
# Funzione principale di generazione
# ---------------------------------------------------------------------------


def generate_qr(
    url: str,
    logo_path: str | None,
    out_png: str,
    out_svg: Optional[str],
    *,
    scale: int = 10,
    dark: Optional[str] = "#000000",
    light: Optional[str] = "white",
    logo_scale: float = 0.25,
    logo_border: int = 10,
) -> None:
    """Crea un QR code con eventuale logo inserito."""
    qr = segno.make(url, error="h")

    buf = BytesIO()
    qr.save(buf, kind="png", scale=scale, dark=dark, light=light)
    buf.seek(0)
    qr_img = Image.open(buf).convert("RGBA")

    if light is None:
        datas = qr_img.getdata()
        new_data = []
        dark_rgb = ImageColor.getrgb(dark or "#000")
        for pixel in datas:
            if pixel[:3] == dark_rgb:
                new_data.append(pixel)
            else:
                new_data.append((0, 0, 0, 0))
        qr_img.putdata(new_data)

    if logo_path:
        logo_file = Path(logo_path)
        if not logo_file.is_file():
            raise FileNotFoundError(f"Logo non trovato: {logo_file}")

        logo = Image.open(logo_file).convert("RGBA")
        target_size = int(qr_img.size[0] * logo_scale)
        logo.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

        if logo_border > 0:
            border_fill = (0, 0, 0, 0) if light is None else light
            logo = ImageOps.expand(logo, border=logo_border, fill=border_fill)

        pos = (
            (qr_img.size[0] - logo.size[0]) // 2,
            (qr_img.size[1] - logo.size[1]) // 2,
        )

        draw = ImageDraw.Draw(qr_img)
        rect = [pos[0], pos[1], pos[0] + logo.size[0], pos[1] + logo.size[1]]
        bg_fill = (0, 0, 0, 0) if light is None else light
        draw.rectangle(rect, fill=bg_fill)
        qr_img.paste(logo, pos, mask=logo)

    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    if out_svg:
        Path(out_svg).parent.mkdir(parents=True, exist_ok=True)

    qr_img.save(out_png, format="PNG")
    if out_svg:
        qr.save(out_svg, scale=scale, dark=dark, light=light)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse CLI arguments and genera il QR."""

    parser = argparse.ArgumentParser(
        description="Genera un QR code con logo opzionale e colori personalizzabili.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "url",
        nargs="?",
        default="https://github.com/",
        help="URL o testo da codificare nel QR.",
    )
    parser.add_argument(
        "--dark",
        default="#000000",
        type=normalize_color,
        help="Colore dei moduli (dark).",
    )
    parser.add_argument(
        "--light",
        default="white",
        type=normalize_color,
        help="Colore dello sfondo (light).",
    )
    parser.add_argument(
        "--logo",
        default="",
        help="Percorso al logo PNG/trasparente (imposta '' per nessun logo).",
    )
    parser.add_argument(
        "--out-png",
        default="output/qr_logo.png",
        help="File PNG di output.",
    )
    parser.add_argument("--out-svg", default=None, help="File SVG di output.")
    parser.add_argument("--scale", type=int, default=10, help="Scala del QR (1-40).")
    parser.add_argument(
        "--logo-scale",
        type=float,
        default=0.25,
        help="Proporzione del logo rispetto al lato del QR (0-1).",
    )
    parser.add_argument(
        "--logo-border",
        type=int,
        default=10,
        help="Spessore del bordo intorno al logo (pixel).",
    )

    args = parser.parse_args()

    # Normalizza i path di output: aggiungi .png/.svg se mancanti, accetta cartelle
    out_png = ensure_path_with_suffix(args.out_png, ".png", default_stem="qr_logo")
    out_svg = (
        ensure_path_with_suffix(
            args.out_svg, ".svg", default_stem=Path(out_png).with_suffix("").name
        )
        if args.out_svg
        else None
    )

    # Converti logo vuoto in None
    logo_path = None if args.logo == "" else args.logo

    try:
        generate_qr(
            args.url,
            logo_path,
            out_png,
            out_svg,
            scale=args.scale,
            dark=args.dark,
            light=args.light,
            logo_scale=args.logo_scale,
            logo_border=args.logo_border,
        )
        created = [out_png] + ([out_svg] if out_svg else [])
        print("QR generato con successo! → " + " | ".join(created))
    except Exception as exc:  # pragma: no cover
        print("Errore durante la generazione del QR:", exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
