# Roadmap

## Phase 1  Web interface

- [ ] `POST /render` endpoint reusing `imprimir.py` so the web page accepts
      every format the command line does
- [ ] New `www/`: drag and drop, preview of the real bitmap, printer picker,
      energy and quality controls
- [ ] Remove the old interface (`main.js`, `main.css`, `lang/`, `i18n*.js`,
      `accessibility.js`); recoverable from the upstream history

## Phase 2  Print quality

- [ ] Image profiles: photo, text and ASCII, each with its own autocontrast,
      sharpening and threshold before dithering
- [ ] Split long jobs into blocks with a pause, so the head does not build up
      heat and drop lines
- [ ] Calibration sheet: one page with the same image at several energy and
      speed values, pick the best and store it

## Phase 3  Hardware

- [ ] Parse the device replies. `get_device_state` (0xa3) and `get_device_info`
      (0xa8) are sent but the notification handler discards everything that is
      not a flow control byte (`printer.py:351`)
- [ ] Show battery, temperature and firmware in the interface
- [ ] Detect the model from the Bluetooth name and use its `paper_width`
      instead of the hardcoded 384
- [ ] List every nearby BLE device and allow printing to an unknown one
- [ ] Remember the printer address and reconnect without scanning
- [ ] Stop wasting 16 mm per job. `problem_feeding` feeds 128 blank lines at
      the end (`printer.py:467`); `retract_paper` (0xa0) exists and is unused

## Phase 4  Convenience

- [ ] Install as a command with `uv tool install`, so `imprimir file.png` works
      from any directory
- [ ] Windows "Send to" shortcut: right click a file and print it
