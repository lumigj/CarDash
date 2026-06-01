# Add Runner And Startup Workflow Notes

## Goal

Update Raspberry Pi automation docs and scripts so startup workflows recover from early networking issues and can refresh the repo before launching the dashboard.

## Requirements

* Extend the existing README Service Workflow Note.
* Document a systemd override that waits for `network-online.target`.
* Document automatic restart behavior so the runner recovers if Wi-Fi or DNS is still unavailable when the service first starts.
* Include commands to identify the runner service, edit the override, reload systemd, restart the runner, and enable the appropriate wait-online service.
* Add a startup wrapper script that updates the Raspberry Pi checkout from `origin/main` before launching `scripts/obd_interface.py`.
* Update the README desktop autostart example to run the startup wrapper instead of calling Python directly.

## Acceptance Criteria

* [x] `README.md` includes the RPi GitHub Actions runner service fix under Service Workflow Note.
* [x] The note stays clear that the repo itself does not currently include the old `svc.sh` helper.
* [x] The commands are copyable and use placeholder service names where repo-specific runner names vary.
* [x] `scripts/start_dashboard.sh` exists and is executable.
* [x] The README desktop entry uses `Exec=/home/lumi/CarDash/scripts/start_dashboard.sh`.

## Definition of Done

* README updated.
* Markdown structure remains readable.
* Startup script added.

## Technical Approach

Add a concise subsection below the existing Service Workflow Note explaining the network startup race and the systemd override. Add a small Bash wrapper that waits briefly for GitHub connectivity, uses `git fetch origin main` plus `git reset --hard origin/main`, then `exec`s the existing dashboard Python entry point.

## Out of Scope

* Adding or changing service files in this repository.
* Verifying behavior directly on the Raspberry Pi.

## Technical Notes

* Existing target section: `README.md` under `## Service Workflow Note`.
* User confirmed the runner setup is external to this repo but wants the note kept in the README.
* Existing desktop autostart entry is documented near the Raspberry Pi setup section in `README.md`.
