from __future__ import annotations

import argparse
import re
import sys
from io import BytesIO
from pathlib import Path

import segno
from PIL import Image, ImageOps, ImageDraw, ImageColor

# ---------------------------------------------------------------------------
# Utility colori
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"^[0-9a-fA-F]{3}$|^[0-9a-fA-F]{6}$")


def normalize_color(col: str) -> str:
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

    # Se è esadecimale senza cancelletto
    if _HEX_RE.match(col):
        return f"#{col.lower()}"
    if col.startswith("#") and _HEX_RE.match(col[1:]):
        return f"#{col[1:].lower()}"

    # Proviamo a farlo interpretare a Pillow (nomi CSS, rgb(a)())
    try:
        ImageColor.getrgb(col)
        return col
    except ValueError as exc:  # pragma: no cover
        raise argparse.ArgumentTypeError(f"Colore non valido: {col}") from exc


# ---------------------------------------------------------------------------
# Funzione principale di generazione
# ---------------------------------------------------------------------------


def generate_qr(
    url: str,
    logo_path: str | None,
    out_png: str,
    out_svg: str,
    *,
    scale: int = 10,
    dark: str = "#000000",
    light: str = "white",
    logo_scale: float = 0.25,
    logo_border: int = 10,
) -> None:
    """Crea un QR code con eventuale logo inserito."""

    # 1) Crea il QR con correzione d'errore alta (H = 30 %)
    qr = segno.make(url, error="h")

    # 2) Ottieni l’immagine
    buf = BytesIO()
    qr.save(buf, kind="png", scale=scale, dark=dark, light=light)
    buf.seek(0)
    qr_img = Image.open(buf).convert("RGBA")

    # 2a) Forza la trasparenza ovunque tranne dove c'è il colore "dark"
    if light is None:
        datas = qr_img.getdata()
        new_data = []
        dark_rgb = ImageColor.getrgb(dark)
        for pixel in datas:
            if pixel[:3] == dark_rgb:
                new_data.append(pixel)
            else:
                new_data.append((0, 0, 0, 0))
        qr_img.putdata(new_data)

    # 3) Inserisci il logo se fornito
    if logo_path:
        logo_file = Path(logo_path)
        if not logo_file.is_file():
            raise FileNotFoundError(f"Logo non trovato: {logo_file}")

        logo = Image.open(logo_file).convert("RGBA")

        # Ridimensiona logo
        target_size = int(qr_img.size[0] * logo_scale)
        logo.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

        # Aggiungi bordo per separare logo e moduli QR
        if logo_border > 0:
            if light is None:
                border_fill = (0, 0, 0, 0)  # trasparente
            else:
                border_fill = light
            logo = ImageOps.expand(logo, border=logo_border, fill=border_fill)

        # Calcola posizione centrale
        pos = (
            (qr_img.size[0] - logo.size[0]) // 2,
            (qr_img.size[1] - logo.size[1]) // 2,
        )

        # 3a) Cancella l'area sottostante (niente moduli dietro il logo!)
        draw = ImageDraw.Draw(qr_img)
        rect = [pos[0], pos[1], pos[0] + logo.size[0], pos[1] + logo.size[1]]
        if light is None:  # sfondo trasparente → riempi con alpha 0
            bg_fill = (0, 0, 0, 0)
        else:  # colore pieno (white, #f0f0f0, …)
            bg_fill = light
        draw.rectangle(rect, fill=bg_fill)

        # 3b) Incolla il logo con la maschera alfa
        qr_img.paste(logo, pos, mask=logo)

    # 4) Prepara cartelle di output
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    Path(out_svg).parent.mkdir(parents=True, exist_ok=True)

    # 5) Salva file
    qr_img.save(out_png, format="PNG")
    qr.save(out_svg, scale=scale, dark=dark, light=light)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:  # noqa: D401
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
        default="logo/logo.png",
        help="Percorso al logo PNG/trasparente (imposta '' per nessun logo).",
    )
    parser.add_argument(
        "--out-png",
        default="output/qr_logo.png",
        help="File PNG di output.",
    )
    parser.add_argument(
        "--out-svg",
        default="output/qr_logo.svg",
        help="File SVG di output.",
    )
    parser.add_argument("--scale", type=int, default=10, help="Scala del QR (1–40).")
    parser.add_argument(
        "--logo-scale",
        type=float,
        default=0.25,
        help="Proporzione del logo rispetto al lato del QR (0–1).",
    )
    parser.add_argument(
        "--logo-border",
        type=int,
        default=10,
        help="Spessore del bordo intorno al logo (pixel).",
    )

    args = parser.parse_args()

    # Converti logo vuoto in None per semplicità
    logo_path = None if args.logo == "" else args.logo

    try:
        generate_qr(
            args.url,
            logo_path,
            args.out_png,
            args.out_svg,
            scale=args.scale,
            dark=args.dark,
            light=args.light,
            logo_scale=args.logo_scale,
            logo_border=args.logo_border,
        )
        print(f"QR generato con successo! → {args.out_png} | {args.out_svg}")
    except Exception as exc:  # pragma: no cover
        print("Errore durante la generazione del QR:", exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
