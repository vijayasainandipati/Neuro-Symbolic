"""
Feature Extraction Module for Neuro-Symbolic Reasoning.

Before symbolic reasoning, the system extracts contextual features
from detected events and environmental data.

Features extracted:
  - Population density
  - Terrain slope / elevation
  - Distance to border
  - Infrastructure density
  - Wind speed (cyclone)
  - Soil moisture
  - Rainfall intensity
  - Vehicle count (defense)

Algorithm:
  Detected Event → Extract contextual data → Generate feature vector

Example vector: [population, slope, wind_speed, vehicle_count]
"""

import numpy as np


class FeatureExtractor:
    """
    Extracts contextual features from detected events for
    symbolic reasoning input.

    Combines AI detection outputs with environmental/geospatial
    data to build feature vectors for the decision engine.
    """

    # Feature indices for the output vector
    FEATURE_NAMES = [
        "population_density",
        "terrain_slope",
        "elevation",
        "distance_to_border_km",
        "infrastructure_density",
        "wind_speed_kmh",
        "rainfall_mm",
        "soil_moisture",
        "temperature_c",
        "vehicle_count",
        "event_probability",
    ]

    def __init__(self):
        self.feature_cache = {}

    def extract_disaster_features(
        self,
        event_type,
        event_probability,
        population_density=0,
        terrain_slope=0.0,
        elevation=0.0,
        wind_speed_kmh=0.0,
        rainfall_mm=0.0,
        soil_moisture=0.5,
        temperature_c=25.0,
        infrastructure_density=0.0,
    ):
        """
        Extract feature vector for a disaster event.

        Parameters
        ----------
        event_type : str
            One of 'flood', 'landslide', 'cyclone', 'fire'.
        event_probability : float
            AI model detection probability (0-1).
        population_density : int
            Population count per grid cell.
        terrain_slope : float
            Terrain slope in degrees.
        elevation : float
            Elevation in metres above sea level.
        wind_speed_kmh : float
            Wind speed in km/h (relevant for cyclones).
        rainfall_mm : float
            Rainfall in mm over last 24h.
        soil_moisture : float
            Soil moisture index (0-1).
        temperature_c : float
            Temperature in Celsius (relevant for fires).
        infrastructure_density : float
            Infrastructure density index (0-1).

        Returns
        -------
        dict
            Feature dictionary with named features and raw vector.
        """
        features = {
            "event_type": event_type,
            "event_probability": round(event_probability, 4),
            "population_density": population_density,
            "terrain_slope": terrain_slope,
            "elevation": elevation,
            "wind_speed_kmh": wind_speed_kmh,
            "rainfall_mm": rainfall_mm,
            "soil_moisture": soil_moisture,
            "temperature_c": temperature_c,
            "infrastructure_density": infrastructure_density,
        }

        # Compute derived risk amplifiers
        features["risk_amplifiers"] = self._compute_risk_amplifiers(
            event_type, features
        )

        # Build raw feature vector for ML/reasoning input
        features["feature_vector"] = np.array([
            population_density,
            terrain_slope,
            elevation,
            0.0,  # distance_to_border (disaster context)
            infrastructure_density,
            wind_speed_kmh,
            rainfall_mm,
            soil_moisture,
            temperature_c,
            0,  # vehicle_count (disaster context)
            event_probability,
        ], dtype=np.float32)

        return features

    def extract_defense_features(
        self,
        threat_score,
        object_class="civilian",
        vehicle_count=0,
        distance_to_border_km=50.0,
        movement_direction=None,
        region_type="normal",
        population_density=0,
        infrastructure_density=0.0,
    ):
        """
        Extract feature vector for a defense monitoring event.

        Parameters
        ----------
        threat_score : float
            AI model threat probability (0-1).
        object_class : str
            Detected object class.
        vehicle_count : int
            Number of detected vehicles.
        distance_to_border_km : float
            Distance to nearest border.
        movement_direction : str or None
            Direction of detected movement.
        region_type : str
            Zone classification.
        population_density : int
            Population in the area.
        infrastructure_density : float
            Infrastructure density index.

        Returns
        -------
        dict
            Feature dictionary with named features and raw vector.
        """
        features = {
            "event_type": "defense",
            "threat_score": round(threat_score, 4),
            "object_class": object_class,
            "vehicle_count": vehicle_count,
            "distance_to_border_km": distance_to_border_km,
            "movement_direction": movement_direction,
            "region_type": region_type,
            "population_density": population_density,
            "infrastructure_density": infrastructure_density,
        }

        features["feature_vector"] = np.array([
            population_density,
            0.0,  # terrain_slope
            0.0,  # elevation
            distance_to_border_km,
            infrastructure_density,
            0.0,  # wind_speed
            0.0,  # rainfall
            0.0,  # soil_moisture
            0.0,  # temperature
            vehicle_count,
            threat_score,
        ], dtype=np.float32)

        return features

    def _compute_risk_amplifiers(self, event_type, features):
        """
        Compute event-specific risk amplification factors.

        These amplifiers adjust the base AI probability based on
        contextual environmental conditions.
        """
        amplifiers = []

        if event_type == "flood":
            if features["rainfall_mm"] > 100:
                amplifiers.append(
                    f"Heavy rainfall ({features['rainfall_mm']}mm) amplifies flood risk"
                )
            if features["elevation"] < 10:
                amplifiers.append(
                    f"Low elevation ({features['elevation']}m) increases flood vulnerability"
                )
            if features["soil_moisture"] > 0.7:
                amplifiers.append(
                    f"High soil moisture ({features['soil_moisture']:.1f}) reduces absorption"
                )

        elif event_type == "landslide":
            if features["terrain_slope"] > 30:
                amplifiers.append(
                    f"Steep slope ({features['terrain_slope']}°) increases landslide risk"
                )
            if features["rainfall_mm"] > 80:
                amplifiers.append(
                    f"Heavy rainfall ({features['rainfall_mm']}mm) destabilises terrain"
                )
            if features["soil_moisture"] > 0.8:
                amplifiers.append(
                    f"Saturated soil (moisture={features['soil_moisture']:.1f}) triggers slides"
                )

        elif event_type == "cyclone":
            if features["wind_speed_kmh"] > 120:
                amplifiers.append(
                    f"Extreme winds ({features['wind_speed_kmh']}km/h) — Category 3+ cyclone"
                )
            elif features["wind_speed_kmh"] > 60:
                amplifiers.append(
                    f"Strong winds ({features['wind_speed_kmh']}km/h) — tropical storm"
                )
            if features["population_density"] > 1000:
                amplifiers.append(
                    f"Dense population ({features['population_density']}) at high risk"
                )

        elif event_type == "fire":
            if features["temperature_c"] > 40:
                amplifiers.append(
                    f"Extreme heat ({features['temperature_c']}°C) fuels fire spread"
                )
            if features["wind_speed_kmh"] > 30:
                amplifiers.append(
                    f"Wind ({features['wind_speed_kmh']}km/h) accelerates fire spread"
                )
            if features["soil_moisture"] < 0.2:
                amplifiers.append(
                    f"Dry conditions (moisture={features['soil_moisture']:.1f}) increase fire risk"
                )

        return amplifiers

    def get_feature_names(self):
        """Return the ordered list of feature names."""
        return list(self.FEATURE_NAMES)
