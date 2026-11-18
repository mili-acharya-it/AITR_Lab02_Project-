"""Over-trust detection and trust-calibration-cue (TCC) firing rule.

Re-implementation of the detection logic described in
Okamura & Yamada (2020), "Adaptive trust calibration for human-AI collaboration",
PLOS ONE 15(2): e0229132.  As described in the paper:

* trust is inferred from choice behaviour (choosing Auto => trust > self-confidence);
* a checkpoint is flagged as over-trust when the user chooses Auto while
  P_man > P_auto (manual would have been the better option);
* a TCC fires only if the current checkpoint is flagged AND at least one of the
  two preceding checkpoints was also flagged (three-checkpoint window).

Under-trust is defined symmetrically in the paper but was not tested there; we
implement it for completeness but it is OFF by default to stay faithful.
"""
from __future__ import annotations

from collections import deque


def is_over_trust(chose_auto: bool, p_man_est: float, p_auto_est: float) -> bool:
    return bool(chose_auto and p_man_est > p_auto_est)


def is_under_trust(chose_auto: bool, p_man_est: float, p_auto_est: float) -> bool:
    return bool((not chose_auto) and p_auto_est > p_man_est)


class TCCDetector:
    """Stateful three-checkpoint window detector."""

    def __init__(self, window: int = 3, detect_under_trust: bool = False):
        if window < 1:
            raise ValueError("window must be >= 1")
        self.window = window
        self.detect_under_trust = detect_under_trust
        self._history: deque[bool] = deque(maxlen=window - 1)

    def step(self, chose_auto: bool, p_man_est: float, p_auto_est: float) -> bool:
        """Register one checkpoint; return True if a TCC should be shown now."""
        flagged = is_over_trust(chose_auto, p_man_est, p_auto_est)
        if self.detect_under_trust:
            flagged = flagged or is_under_trust(chose_auto, p_man_est, p_auto_est)
        if self.window == 1:
            fire = flagged
        else:
            fire = flagged and any(self._history)
        self._history.append(flagged)
        return fire
