# Station interface

The shared design direction is in ../placement/DESIGN.md. Local tokens and IBM Plex fonts are copied from placement/static; preserve the same palette and licence files when updating them.

Camera imagery and the pending smoke-suspicion review have priority. Two active feeds share the observation area; inactive mounting is a quiet line. Pending events are expandable rows; the first opens initially, and subsequent polling never resets an operator’s disclosure or clip. Decided events remain correctable in history. A bounded independently scrolling queue keeps accumulation usable on desktop and phone.

The separate module section consumes /api/status.mcu. It labels the short-range local flame sensor exactly and distinguishes simulated readings. LED state means mcu.led.shown; the requested state is secondary and never substituted as observed. Device identity beside measurements comes from /api/status.measured_on.label. Event confidence is explicitly the latest observation, matching the updating event row. WebM inline playback, legacy AVI fallback and saved decisions are preserved.

Frontend verification: npm test, pytest, then browser checks at 1440 and 390 px including loss and flame-sensor states. No external runtime assets or continuous animations.
