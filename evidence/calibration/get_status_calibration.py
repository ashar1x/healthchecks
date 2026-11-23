"""Calibration copy of Check.get_status from hc/api/models.py (Phase 3).

VERBATIM copy of the function body from hc/api/models.py lines 355-380,
dedented to module level so that SonarQube's file-level `complexity` measure
for this one-function project IS the complexity of get_status alone.

This is needed because SonarQube 26.11 community exposes complexity only at
file/folder/project granularity (see evidence/raw/sonar-qualifier-probe.txt).

Not production code. Not part of the application. Kept only as raw input for
the calibration scan (see docs/02-static-analysis.md).
"""


def get_status(self, *, with_started: bool = False) -> str:
    """Return current status for display."""
    frozen_now = now()

    if self.last_start:
        if frozen_now >= self.last_start + self.grace:
            return "down"
        elif with_started:
            return "started"

    if self.status in ("new", "paused", "down"):
        return self.status

    grace_start = self.get_grace_start(with_started=False)
    if grace_start is None:
        # next elapse is "never", so this check will stay up indefinitely
        return "up"

    grace_end = grace_start + self.grace
    if frozen_now >= grace_end:
        return "down"

    if frozen_now >= grace_start:
        return "grace"

    return "up"
