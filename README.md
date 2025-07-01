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
pip install segno pillow
```

oppure, per clonare il repo:

```bash
git clone https://github.com/Alex-Citeroni/qr_code_generator
cd qr-logo
python -m venv .venv
source .venv/bin/activate  # su Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
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
