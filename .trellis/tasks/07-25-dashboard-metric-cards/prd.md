# Redesign Dashboard Metric Cards

## Goal

Replace the narrow centered metric column with a full-screen block/card dashboard that uses the available 1280x720 display area and is easier to scan in a vehicle.

## What I Already Know

* The dashboard contains nine metrics: timing advance, throttle position, engine load, coolant temperature, intake pressure, intake temperature, short fuel trim, long fuel trim, and status.
* Four metrics currently use gauge bars; the remaining metrics display text values.
* The current UI fixes every metric to a narrow width and stacks all metrics vertically in the middle of the screen.
* The dashboard and backup camera share a `QStackedWidget`; reverse-camera priority must not change.
* The requested visual direction is one block per metric.
* The target display is 1280x720 with proportional scaling for other 16:9 sizes.

## Requirements

* Arrange all nine metrics in a 3x3 grid.
* Make every card expand evenly to use the dashboard page.
* Keep timing, throttle, engine load, and coolant gauge behavior.
* Present non-gauge values as large, readable metric cards.
* Center each metric value within its card instead of placing values in a corner.
* Make numeric values substantially larger than their card titles.
* Keep the dark dashboard theme with clearer card separation, spacing, and typography.
* Keep the existing metric set, values, polling, mock behavior, and reverse-camera behavior unchanged.

## Acceptance Criteria

* [x] The mock dashboard shows nine distinct cards in three columns and three rows.
* [x] The card grid fills the useful 1280x720 dashboard area without clipping.
* [x] All labels and mock values remain readable.
* [x] Every metric value is visually centered within its card.
* [x] Numeric values remain fully visible at the larger size.
* [x] Gauge bars still reflect timing, throttle, load, and coolant values.
* [x] `R` still switches to the mock backup camera and `N` returns to the card dashboard.
* [x] Live OBD polling code is unchanged.

## Definition of Done

* Python syntax/static checks pass.
* The mock UI is rendered and visually inspected at 1280x720.
* Reverse-camera switching remains connected to the existing stacked pages.

## Out of Scope

* Music playback, lyrics, iPhone remote control, or Bluetooth configuration.
* Adding, removing, or renaming OBD metrics.
* Changing polling intervals or OBD connection behavior.
* Redesigning the backup-camera page.

## Technical Notes

* Primary implementation file: `scripts/obd_interface.py`.
* Replace the fixed-width metric widgets and centered vertical layout with an expanding `QGridLayout`.
* Preserve the current `gauge_metrics` and `info_metrics` update dictionaries.
