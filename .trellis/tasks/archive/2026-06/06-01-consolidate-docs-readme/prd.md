# Consolidate project docs into README

## Goal

Create a single README that explains CarDash as a Raspberry Pi car dashboard project: live OBD-II data display, CSV OBD logging, and backup-camera switching from a reverse-gear GPIO signal.

## What I already know

* The project reads live OBD-II data through an ELM327 adapter and renders a PyQt dashboard.
* The dashboard can switch to a backup-camera view using a Raspberry Pi GPIO reverse signal.
* The backup-camera trigger is active-low on BCM GPIO 17: HIGH means normal dashboard, LOW means reverse camera mode.
* The camera view uses Picamera2 in live mode and has a mock view for local testing.
* The repo currently has four docs files:
  * `docs/README.md`
  * `docs/workflows.md`
  * `docs/reverse_camera_trigger.md`
  * `docs/obd_logger.md`
* The repo currently has no root `README.md`.

## Assumptions

* The README should be edited into a coherent document rather than pasted together with repeated headings.

## Open Questions

* None.

## Requirements

* Combine the information from the four docs files into one root `README.md`.
* Preserve the important setup, Raspberry Pi autostart, OBD dashboard, mock mode, OBD logger, and reverse-camera circuit details.
* Make the README reflect the current code paths and behavior discovered in the repo.
* Keep the document concise enough to be useful from the repo landing page.
* Remove the old `docs/` folder after consolidation.

## Acceptance Criteria

* [x] `README.md` exists at the repo root.
* [x] README covers setup/install, running the dashboard, mock mode, OBD logging, reverse GPIO behavior, and reverse-trigger circuit wiring.
* [x] Existing command examples are preserved or corrected.
* [x] Links and file paths point to current repo paths.
* [x] The old `docs/` markdown files are removed.

## Definition of Done

* Docs are consolidated.
* Markdown renders with clear headings and fenced code blocks.
* No unrelated user changes are reverted.

## Out of Scope

* Changing OBD, GPIO, camera, or dashboard runtime behavior.
* Adding dependency-install automation beyond the existing documented commands.
* Adding hardware diagrams beyond the existing text wiring notes.

## Technical Notes

* `scripts/obd_interface.py` is the main app entrypoint.
* `scripts/obd_logger.py` provides standalone CSV logging and OBD command discovery.
* `scripts/reverse_gpio.py` handles active-low reverse detection with debounce.
* `dashboard/camera_view.py` uses Picamera2 unless mock mode is active.
* `requirements-rpi.txt` currently pins `obd==0.7.3`; PyQt5 is installed through apt per existing docs.
