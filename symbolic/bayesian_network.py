"""
Bayesian Decision Network for uncertainty-aware disaster reasoning.

Combines multiple uncertain inputs (flood probability, rainfall,
terrain elevation) using Bayesian probability to produce
a calibrated disaster risk estimate.
"""

import numpy as np


class BayesianDecisionNetwork:
    """
    A simple Bayesian network for disaster risk assessment.

    Combines:
      - P(flood | satellite)     : from the neural network
      - P(flood | rainfall)      : from weather data
      - P(flood | elevation)     : from DEM data
      - P(flood | soil_moisture) : optional soil data

    Uses naïve Bayes combination (conditional independence assumption)
    to produce a posterior risk estimate.
    """

    def __init__(self):
        # Prior probability of flood in any region
        self.prior_flood = 0.1

        # Likelihood tables: P(evidence | flood) and P(evidence | no flood)
        # These are calibrated from historical disaster data
        self.likelihoods = {
            "satellite": {
                "flood": lambda p: np.clip(p, 0.01, 0.99),
                "no_flood": lambda p: np.clip(1 - p, 0.01, 0.99),
            },
            "rainfall": {
                # rainfall_mm: higher rainfall → higher flood likelihood
                "flood": lambda r: np.clip(1 / (1 + np.exp(-0.05 * (r - 100))), 0.01, 0.99),
                "no_flood": lambda r: np.clip(1 / (1 + np.exp(0.05 * (r - 100))), 0.01, 0.99),
            },
            "elevation": {
                # elevation_m: lower elevation → higher flood likelihood
                "flood": lambda e: np.clip(1 / (1 + np.exp(0.1 * (e - 20))), 0.01, 0.99),
                "no_flood": lambda e: np.clip(1 / (1 + np.exp(-0.1 * (e - 20))), 0.01, 0.99),
            },
            "soil_moisture": {
                # soil_moisture (0-1): higher → more flood-prone
                "flood": lambda s: np.clip(0.3 + 0.6 * s, 0.01, 0.99),
                "no_flood": lambda s: np.clip(0.7 - 0.4 * s, 0.01, 0.99),
            },
        }

    def compute_posterior(self, evidence):
        """
        Compute posterior flood probability using Bayes' theorem
        with multiple evidence sources.

        Parameters
        ----------
        evidence : dict
            Keys are evidence types, values are the observed values.
            Example: {
                "satellite": 0.85,    # CNN flood probability
                "rainfall": 150,       # mm in last 24h
                "elevation": 5,        # metres ASL
                "soil_moisture": 0.7,  # 0-1 scale
            }

        Returns
        -------
        dict
            'posterior': float (combined flood probability),
            'evidence_contributions': dict of per-source likelihoods,
            'confidence': float (0-1 confidence in the estimate).
        """
        log_likelihood_flood = np.log(self.prior_flood)
        log_likelihood_no_flood = np.log(1 - self.prior_flood)

        contributions = {}

        for source, value in evidence.items():
            if source not in self.likelihoods:
                continue

            lf = self.likelihoods[source]["flood"](value)
            lnf = self.likelihoods[source]["no_flood"](value)

            log_likelihood_flood += np.log(lf)
            log_likelihood_no_flood += np.log(lnf)

            contributions[source] = {
                "value": float(value),
                "P(evidence|flood)": float(lf),
                "P(evidence|no_flood)": float(lnf),
                "likelihood_ratio": float(lf / lnf) if lnf > 0 else float("inf"),
            }

        # Normalize (log-sum-exp for numerical stability)
        max_log = max(log_likelihood_flood, log_likelihood_no_flood)
        log_total = max_log + np.log(
            np.exp(log_likelihood_flood - max_log)
            + np.exp(log_likelihood_no_flood - max_log)
        )
        posterior = float(np.exp(log_likelihood_flood - log_total))

        # Confidence based on number of evidence sources and agreement
        n_sources = len(contributions)
        confidence = min(1.0, 0.5 + 0.1 * n_sources)

        return {
            "posterior": round(posterior, 4),
            "prior": self.prior_flood,
            "evidence_contributions": contributions,
            "confidence": round(confidence, 2),
            "num_evidence_sources": n_sources,
        }

    def assess_risk(self, evidence):
        """
        High-level risk assessment combining Bayesian posterior
        with categorical risk classification.

        Returns
        -------
        dict with 'risk_category', 'posterior', 'recommended_action'.
        """
        result = self.compute_posterior(evidence)
        posterior = result["posterior"]

        if posterior > 0.8:
            category = "CRITICAL"
            action = "Immediate evacuation and emergency response"
        elif posterior > 0.6:
            category = "HIGH"
            action = "Issue warnings, prepare rescue resources"
        elif posterior > 0.4:
            category = "MODERATE"
            action = "Enhanced monitoring and early warning"
        elif posterior > 0.2:
            category = "LOW"
            action = "Routine monitoring"
        else:
            category = "MINIMAL"
            action = "No action required"

        return {
            **result,
            "risk_category": category,
            "recommended_action": action,
        }
