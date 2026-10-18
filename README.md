# printer-term

Print files on a Bluetooth LE thermal printer from the command line or a web page.
Tuned for an MX10 with 57 mm paper (384 px per line).

## Credit

This is a derivative of [NaitLee/Cat-Printer](https://github.com/NaitLee/Cat-Printer),
which does all the hard work: the Bluetooth protocol, the printer models and the
server. The full upstream history is kept in this repository, and the original
readme is at [README.upstream.md](./README.upstream.md).

Licensed GPL-3.0, same as upstream. See [LICENSE](./LICENSE).

## Install

```sh
uv venv
uv pip install -r requirements.txt pillow pypdfium2
```

## Command line

```sh
uv run python imprimir.py FILE
```

`FILE` is a path or an `http(s)` URL. Accepted: `.txt .md .png .jpg .jpeg .gif
.webp .bmp .pdf`. Text is wrapped to the paper width, images are scaled to 384 px
and dithered, PDF pages are rendered and stacked.

| Option | Meaning |
| --- | --- |
| `--energy 0.0-1.0` | thermal strength, default `0.5` |
| `--quality 1-4` | `1` prints most evenly on this MX10, default |
| `--speed N` | raw speed value, overrides `--quality` |
| `--size N` | font size for `.txt` and `.md` |
| `--font NAME` | `verdana`, `arial`, `georgia` or `consola` |
| `--ascii` | ASCII art: no wrapping, font scaled to fill the width |
| `--dry` | run the print process without using paper |
| `--fake` | convert only, no Bluetooth |

Self check:

```sh
uv run python imprimir.py --demo
```

## Web interface

```sh
uv run python server.py
```

Then open http://127.0.0.1:8095/

## Notes on this printer

- The print head is 384 dots at 203 dpi, so it covers 48 mm. On a 57 mm roll
  about 4.5 mm stays blank on each side. Use 48 mm rolls to avoid it.
- The printer stops advertising for a few seconds after a job. On
  `no-available-devices-found`, wait and run the command again.
- `--quality 1` was measured to band less than `--quality 4` on this unit.
