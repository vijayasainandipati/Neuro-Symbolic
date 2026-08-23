"""
Real-time processing algorithms for streaming satellite data.

1. Sliding Window Prediction – continuous model inference on new frames
2. Event-Driven Alert System – threshold-based alert triggering
"""

import time
import logging
from datetime import datetime, timezone
from collections import deque

logger = logging.getLogger(__name__)


class SlidingWindowPredictor:
    """
    Maintains a sliding window of recent predictions and
    produces smoothed flood probability estimates.

    Algorithm
    ─────────
      New image arrives
           ↓
      Model predicts flood probability
           ↓
      Add to sliding window
           ↓
      Compute smoothed estimate (weighted average)
           ↓
      Update decision
           ↓
      Repeat
    """

    def __init__(self, window_size=10, decay_factor=0.9):
        """
        Parameters
        ----------
        window_size : int
            Number of recent predictions to keep.
        decay_factor : float
            Exponential decay weight for older predictions (0-1).
            1.0 = uniform weighting, <1.0 = newer predictions weighted more.
        """
        self.window_size = window_size
        self.decay_factor = decay_factor
        self.predictions = deque(maxlen=window_size)
        self.timestamps = deque(maxlen=window_size)

    def add_prediction(self, flood_prob, timestamp=None):
        """Add a new prediction to the sliding window."""
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        self.predictions.append(flood_prob)
        self.timestamps.append(ts)

    def get_smoothed_probability(self):
        """
        Compute exponentially weighted moving average of predictions.

        Returns
        -------
        float or None
            Smoothed flood probability, or None if window is empty.
        """
        if not self.predictions:
            return None

        n = len(self.predictions)
        weights = [self.decay_factor ** (n - 1 - i) for i in range(n)]
        total_weight = sum(weights)

        smoothed = sum(p * w for p, w in zip(self.predictions, weights)) / total_weight
        return round(smoothed, 4)

    def get_trend(self):
        """
        Determine if flood risk is increasing, stable, or decreasing.

        Returns
        -------
        str
            'increasing', 'decreasing', or 'stable'.
        """
        if len(self.predictions) < 3:
            return "insufficient_data"

        recent = list(self.predictions)
        first_half = sum(recent[: len(recent) // 2]) / (len(recent) // 2)
        second_half = sum(recent[len(recent) // 2 :]) / (len(recent) - len(recent) // 2)

        diff = second_half - first_half
        if diff > 0.05:
            return "increasing"
        elif diff < -0.05:
            return "decreasing"
        else:
            return "stable"

    def get_status(self):
        """Return current window status."""
        return {
            "window_size": self.window_size,
            "current_count": len(self.predictions),
            "smoothed_probability": self.get_smoothed_probability(),
            "trend": self.get_trend(),
            "latest_prediction": self.predictions[-1] if self.predictions else None,
            "latest_timestamp": self.timestamps[-1] if self.timestamps else None,
        }

    def clear(self):
        """Reset the sliding window."""
        self.predictions.clear()
        self.timestamps.clear()


class EventDrivenAlertSystem:
    """
    Event-driven alert system that triggers notifications
    when flood probability thresholds are exceeded.

    Features
    ────────
    - Configurable alert thresholds
    - Cooldown period to avoid alert fatigue
    - Alert history logging
    - Escalation logic
    """

    def __init__(self, cooldown_seconds=300):
        """
        Parameters
        ----------
        cooldown_seconds : int
            Minimum time between repeated alerts for the same region.
        """
        self.cooldown_seconds = cooldown_seconds

        # Threshold configuration
        self.thresholds = {
            "CRITICAL": 0.85,
            "HIGH": 0.65,
            "MODERATE": 0.45,
            "LOW": 0.25,
        }

        # Track last alert time per region to enforce cooldown
        self._last_alert = {}  # region_name → timestamp
        self.alert_history = []

    def check_and_alert(self, region_name, flood_prob, extra_data=None):
        """
        Check if a flood probability triggers an alert.

        Parameters
        ----------
        region_name : str
        flood_prob : float
        extra_data : dict, optional
            Additional context (population, elevation, etc.)

        Returns
        -------
        dict or None
            Alert record if triggered, None if suppressed by cooldown.
        """
        # Determine alert level
        alert_level = None
        for level, threshold in self.thresholds.items():
            if flood_prob >= threshold:
                alert_level = level
                break

        if alert_level is None:
            return None  # Below all thresholds

        # Check cooldown
        now = time.time()
        last = self._last_alert.get(region_name, 0)
        if now - last < self.cooldown_seconds:
            logger.debug(
                "Alert suppressed for %s (cooldown active, %ds remaining)",
                region_name,
                int(self.cooldown_seconds - (now - last)),
            )
            return None

        # Fire alert
        self._last_alert[region_name] = now

        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "region": region_name,
            "flood_probability": round(flood_prob, 4),
            "alert_level": alert_level,
            "threshold_used": self.thresholds[alert_level],
            "extra_data": extra_data or {},
        }

        self.alert_history.append(alert)

        logger.warning(
            "🚨 ALERT [%s] Region: %s | Flood: %.2f%% | Threshold: %.0f%%",
            alert_level,
            region_name,
            flood_prob * 100,
            self.thresholds[alert_level] * 100,
        )

        return alert

    def get_active_alerts(self, max_age_seconds=3600):
        """Return alerts from the last `max_age_seconds`."""
        cutoff = time.time() - max_age_seconds
        active = []
        for alert in reversed(self.alert_history):
            ts = datetime.fromisoformat(alert["timestamp"]).timestamp()
            if ts < cutoff:
                break
            active.append(alert)
        return active

    def get_history(self):
        """Return the full alert history."""
        return list(self.alert_history)

    def reset_cooldown(self, region_name=None):
        """Reset cooldown for a specific region or all regions."""
        if region_name:
            self._last_alert.pop(region_name, None)
        else:
            self._last_alert.clear()
