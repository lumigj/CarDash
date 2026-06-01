# Add Runner Service Workflow Note

## Goal

Update the README Service Workflow Note with guidance for a Raspberry Pi GitHub self-hosted runner that starts under systemd before networking is ready.

## Requirements

* Extend the existing README Service Workflow Note.
* Document a systemd override that waits for `network-online.target`.
* Document automatic restart behavior so the runner recovers if Wi-Fi or DNS is still unavailable when the service first starts.
* Include commands to identify the runner service, edit the override, reload systemd, restart the runner, and enable the appropriate wait-online service.

## Acceptance Criteria

* [ ] `README.md` includes the RPi GitHub Actions runner service fix under Service Workflow Note.
* [ ] The note stays clear that the repo itself does not currently include the old `svc.sh` helper.
* [ ] The commands are copyable and use placeholder service names where repo-specific runner names vary.

## Definition of Done

* README updated.
* Markdown structure remains readable.
* No code changes required.

## Technical Approach

Add a concise subsection below the existing Service Workflow Note explaining the network startup race and the systemd override.

## Out of Scope

* Adding or changing service files in this repository.
* Verifying behavior directly on the Raspberry Pi.
* Changing the documented Raspberry Pi desktop autostart path for this repo.

## Technical Notes

* Existing target section: `README.md` under `## Service Workflow Note`.
* User confirmed the runner setup is external to this repo but wants the note kept in the README.
