#!/usr/bin/env python3
from __future__ import annotations
import argparse, math
from pathlib import Path
from typing import Tuple, List
from PIL import Image, ImageDraw, ImageOps

# ---------------------------------------------
# Misure carta (mm)
# ---------------------------------------------
PAPER_SIZES_MM = {
    "A4": (210, 297),
    "A3": (297, 420),
    "A5": (148, 210),
    "LETTER": (216, 279),
}


def mm_to_px(mm: float, dpi: int) -> int:
    return int(round(mm * dpi / 25.4))


def resolve_paper_px(paper: str, dpi: int) -> Tuple[int, int]:
    wmm, hmm = PAPER_SIZES_MM[paper.upper()]
    return mm_to_px(wmm, dpi), mm_to_px(hmm, dpi)


def load_pngs(folder: Path) -> List[Path]:
    files = sorted(folder.glob("*.png"))
    if not files:
        raise FileNotFoundError(f"Nessun PNG trovato in {folder}")
    return files


def place_grid(
    canvas_size: Tuple[int, int],
    cols: int,
    rows: int,
    margin_px: int,
    gutter_px: int,
) -> List[Tuple[int, int, int, int]]:
    """Restituisce i box (left, top, right, bottom) per ciascuna cella della griglia."""
    W, H = canvas_size
    grid_w = W - 2 * margin_px - gutter_px * (cols - 1)
    grid_h = H - 2 * margin_px - gutter_px * (rows - 1)
    cell_w = grid_w // cols
    cell_h = grid_h // rows
    # Forziamo quadrato per i QR
    side = min(cell_w, cell_h)
    boxes = []
    for r in range(rows):
        for c in range(cols):
            left = margin_px + c * (side + gutter_px)
            top = margin_px + r * (side + gutter_px)
            boxes.append((left, top, left + side, top + side))
    return boxes


def paste_center_square(
    dst: Image.Image,
    src: Image.Image,
    box: Tuple[int, int, int, int],
    bg=(255, 255, 255, 0),
):
    """Ridimensiona src per contenere nel quadrato 'box' e la incolla centrata."""
    l, t, r, b = box
    side = r - l
    # Convertiamo in RGBA per preservare eventuale trasparenza
    src = src.convert("RGBA")
    # Ridimensiona mantenendo proporzioni dentro il quadrato
    src = ImageOps.contain(src, (side, side), Image.Resampling.LANCZOS)
    # Calcola offset centrato
    x = l + (side - src.width) // 2
    y = t + (side - src.height) // 2
    # Se vogliamo garantire fondo bianco anche per QR trasparenti:
    if dst.mode != "RGBA":
        dst = dst.convert("RGBA")
    # Pulisce lo sfondo nella cella (utile se vuoi “quadretti” bianchi perfetti)
    cell_bg = Image.new("RGBA", (side, side), bg)
    dst.alpha_composite(cell_bg, (l, t))
    # Incolla il QR
    dst.alpha_composite(src, (x, y))
    return dst


def draw_crop_marks(
    img: Image.Image,
    margin_px: int,
    mark_len_px: int = 30,
    stroke: int = 2,
    color=(0, 0, 0, 255),
):
    """Disegna crocini di taglio negli angoli a ridosso dei margini."""
    W, H = img.size
    d = ImageDraw.Draw(img)
    m = margin_px
    L = mark_len_px
    # alto-sx
    d.line([(m, m - L), (m, m + L)], fill=color, width=stroke)
    d.line([(m - L, m), (m + L, m)], fill=color, width=stroke)
    # alto-dx
    d.line([(W - m, m - L), (W - m, m + L)], fill=color, width=stroke)
    d.line([(W - m - L, m), (W - m + L, m)], fill=color, width=stroke)
    # basso-sx
    d.line([(m, H - m - L), (m, H - m + L)], fill=color, width=stroke)
    d.line([(m - L, H - m), (m + L, H - m)], fill=color, width=stroke)
    # basso-dx
    d.line([(W - m, H - m - L), (W - m, H - m + L)], fill=color, width=stroke)
    d.line([(W - m - L, H - m), (W - m + L, H - m)], fill=color, width=stroke)


def make_sheets(
    input_dir: Path,
    out_path: Path,
    paper: str = "A4",
    dpi: int = 300,
    cols: int = 4,
    rows: int = 5,
    margin_mm: float = 8.0,
    gutter_mm: float = 6.0,
    background: str = "white",
    crop_marks: bool = False,
    output_png_pages: bool = False,
):
    paper = paper.upper()
    if paper not in PAPER_SIZES_MM:
        raise ValueError(f"Formato carta non supportato: {paper}")
    W, H = resolve_paper_px(paper, dpi)
    margin_px = mm_to_px(margin_mm, dpi)
    gutter_px = mm_to_px(gutter_mm, dpi)

    files = load_pngs(input_dir)
    per_page = cols * rows
    pages = math.ceil(len(files) / per_page)

    made_images: List[Image.Image] = []
    for p in range(pages):
        page = Image.new(
            "RGBA",
            (W, H),
            (255, 255, 255, 0) if background == "transparent" else background,
        )
        boxes = place_grid((W, H), cols, rows, margin_px, gutter_px)
        chunk = files[p * per_page : (p + 1) * per_page]
        for img_path, box in zip(chunk, boxes):
            qr = Image.open(img_path)
            page = paste_center_square(
                page,
                qr,
                box,
                bg=(255, 255, 255, 0) if background == "transparent" else background,
            )
        if crop_marks and background != "transparent":
            draw_crop_marks(page, margin_px)
        # Convertiamo per PDF (niente alpha)
        made_images.append(page.convert("RGB"))

    if output_png_pages:
        # Salva pagine singole PNG
        out_dir = out_path if out_path.suffix == "" else out_path.with_suffix("")
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, im in enumerate(made_images, 1):
            im.save(out_dir / f"sheet_{i:02d}.png", dpi=(dpi, dpi))
    else:
        # Salva PDF multipagina
        out_path.parent.mkdir(parents=True, exist_ok=True)
        made_images[0].save(
            out_path,
            save_all=True,
            append_images=made_images[1:],
            resolution=dpi,
        )
    return len(files), pages


def main():
    ap = argparse.ArgumentParser(
        description="Impagina QR in griglia per stampa (PDF multipagina)."
    )
    ap.add_argument("--input-dir", default="output", help="Cartella con i PNG dei QR.")
    ap.add_argument(
        "--out",
        default="output/qr_sheets.pdf",
        help="Percorso PDF (o cartella se --png-pages).",
    )
    ap.add_argument(
        "--paper", default="A4", choices=PAPER_SIZES_MM.keys(), help="Formato carta."
    )
    ap.add_argument("--dpi", type=int, default=300, help="DPI di esportazione.")
    ap.add_argument("--cols", type=int, default=4, help="Colonne per pagina.")
    ap.add_argument("--rows", type=int, default=5, help="Righe per pagina.")
    ap.add_argument("--margin-mm", type=float, default=8.0, help="Margine pagina (mm).")
    ap.add_argument(
        "--gutter-mm", type=float, default=6.0, help="Spazio tra celle (mm)."
    )
    ap.add_argument(
        "--transparent",
        action="store_true",
        help="Sfondo trasparente (no PDF con alpha).",
    )
    ap.add_argument(
        "--crop-marks", action="store_true", help="Disegna crocini di taglio."
    )
    ap.add_argument(
        "--png-pages", action="store_true", help="Esporta pagine PNG invece del PDF."
    )
    args = ap.parse_args()

    bg = "transparent" if args.transparent else "white"
    n_imgs, n_pages = make_sheets(
        input_dir=Path(args.input_dir),
        out_path=Path(args.out),
        paper=args.paper,
        dpi=args.dpi,
        cols=args.cols,
        rows=args.rows,
        margin_mm=args.margin_mm,
        gutter_mm=args.gutter_mm,
        background=bg,
        crop_marks=args.crop_marks,
        output_png_pages=(
            args.png - pages if hasattr(args, "png-pages") else args.png_pages
        ),
    )
    print(f"Impaginati {n_imgs} QR su {n_pages} pagina/e → {args.out}")


if __name__ == "__main__":
    main()
