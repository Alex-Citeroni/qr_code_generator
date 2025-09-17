# QR Code Generator

Genera QR code personalizzati (PNG + SVG) con colori e logo centrale tramite linea di comando.

## Caratteristiche

* Colori `--dark` e `--light` in formato nome CSS, HEX 3/6 cifre o trasparente.
* Logo PNG con canale alpha, ridimensionamento proporzionale e bordo opzionale.
* Correzione d'errore livello **H** (30 %) per preservare i dati anche con logo.
* Esporta contemporaneamente PNG (bitmap) e SVG (vettoriale).
* Nessuna dipendenza nativa: solo **Segno** e **Pillow**.

## Installazione rapida

```bash
git clone https://github.com/Alex-Citeroni/qr_code_generator
cd qr-logo
python -m venv .venv
source .venv/bin/activate  # su Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python.exe -m pip install --upgrade pip
```

## Utilizzo base

```bash
python app.py "https://example.com"
```

Genera `output/qr_logo.png` e `output/qr_logo.svg` con QR nero su sfondo bianco e logo di default.

### Opzioni CLI

| Flag                         | Default              | Descrizione                                                     |
| ---------------------------- | -------------------- | --------------------------------------------------------------- |
| `--dark COLOR`               | `#000000`            | Colore dei moduli QR                                            |
| `--light COLOR\|transparent` | `white`              | Colore di sfondo (usare `transparent` per PNG con alpha)        |
| `--logo PATH`                | `logo/logo.png`      | Logo PNG con trasparenza; passare stringa vuota per nessun logo |
| `--scale INT`                | `10`                 | Fattore di scala (1–40)                                         |
| `--logo-scale FLOAT`         | `0.25`               | Proporzione del logo rispetto al QR (0–1)                       |
| `--logo-border INT`          | `10`                 | Spessore bordo attorno al logo, in pixel                        |
| `--out-png PATH`             | `output/qr_logo.png` | Percorso di output PNG                                          |
| `--out-svg PATH`             | `output/qr_logo.svg` | Percorso di output SVG                                          |

### Esempio avanzato

```bash
python app.py \
  --url "https://openai.com" \
  --dark "navy" \
  --light "#f0f0f0" \
  --logo assets/openai.png \
  --scale 12 \
  --logo-scale 0.3 \
  --logo-border 12
```

## Impaginazione per stampa (nuova funzionalità)

Puoi unire i QR generati in fogli pronti per la stampa, ridimensionati e disposti a griglia su pagine A4 (o altro formato). Viene generato un PDF multipagina o, se preferisci, una serie di PNG.

### Installazione aggiuntiva

```bash
pip install pillow
```

### Utilizzo

```bash
python make_sheets.py --input-dir output --out output/qr_sheets.pdf --paper A4 --dpi 300 --cols 4 --rows 5 --margin-mm 8 --gutter-mm 6
```

#### Opzioni principali

| Flag              | Default                | Descrizione                                         |
| ----------------- | ---------------------- | --------------------------------------------------- |
| `--input-dir DIR` | `output`               | Cartella con i PNG dei QR                           |
| `--out PATH`      | `output/qr_sheets.pdf` | PDF multipagina di output (o cartella se PNG)       |
| `--paper`         | `A4`                   | Formato pagina (`A4`, `A3`, `A5`, `LETTER`)         |
| `--dpi INT`       | `300`                  | Risoluzione di esportazione                         |
| `--cols INT`      | `4`                    | Numero di colonne per pagina                        |
| `--rows INT`      | `5`                    | Numero di righe per pagina                          |
| `--margin-mm`     | `8`                    | Margine pagina in millimetri                        |
| `--gutter-mm`     | `6`                    | Spazio tra i QR in millimetri                       |
| `--crop-marks`    | *off*                  | Aggiunge crocini di taglio agli angoli della pagina |
| `--png-pages`     | *off*                  | Esporta singole pagine PNG invece del PDF           |

### Esempi

* PDF A4 con 20 QR per pagina (4x5):

```bash
python make_sheets.py --input-dir output --out output/qr_sheets.pdf
```

* Pagine PNG invece del PDF:

```bash
python make_sheets.py --input-dir output --png-pages --out output/sheets_png
```

* Con crocini di taglio:

```bash
python make_sheets.py --input-dir output --out output/qr_sheets.pdf --crop-marks
```

## Dipendenze

* [Segno](https://pypi.org/project/segno/) ≥ 1.6 (`pip install segno`)
* [Pillow](https://pypi.org/project/Pillow/) ≥ 10.0

Versione testata: **Python 3.10+**.

## Contribuire

Le PR sono benvenute! Apri prima una *Issue* per discutere il cambiamento.

## Licenza

Distribuito con licenza **MIT**. Vedi `LICENSE` per i dettagli.

## Crediti

Creato con ❤️ da Alex Citeroni.
