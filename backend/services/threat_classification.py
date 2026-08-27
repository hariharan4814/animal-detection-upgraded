"""
Threat Classification Engine for FarmSync.
Provides authoritative mapping of animal species to threat tiers (HIGH, MEDIUM, LOW),
cached database rule lookups with dynamic invalidation, and fallback handling.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from django.db import models

logger = logging.getLogger(__name__)


class ThreatLevel(models.TextChoices):
    HIGH = "HIGH", "High Threat"
    MEDIUM = "MEDIUM", "Medium Threat"
    LOW = "LOW", "Low Threat"


# Hierarchy scoring for overall multi-detection severity comparison
THREAT_HIERARCHY = {
    ThreatLevel.HIGH.value: 3,
    ThreatLevel.MEDIUM.value: 2,
    ThreatLevel.LOW.value: 1,
}

# Display metadata for UI and logs
THREAT_DISPLAY_LABELS = {
    ThreatLevel.HIGH.value: "High Threat",
    ThreatLevel.MEDIUM.value: "Medium Threat",
    ThreatLevel.LOW.value: "Low Threat",
}

# Default threat classification mapping for all verified COCO and legacy supported animal species
DEFAULT_ANIMAL_THREAT_RULES: Dict[str, str] = {
    # High Threat Species (Dangerous predators, large aggressive wildlife, venomous animals)
    "bear": ThreatLevel.HIGH.value,
    "elephant": ThreatLevel.HIGH.value,
    "lion": ThreatLevel.HIGH.value,
    "tiger": ThreatLevel.HIGH.value,
    "cheetah": ThreatLevel.HIGH.value,
    "leopard": ThreatLevel.HIGH.value,
    "wolf": ThreatLevel.HIGH.value,
    "hyena": ThreatLevel.HIGH.value,
    "crocodile": ThreatLevel.HIGH.value,
    "snake": ThreatLevel.HIGH.value,
    "hippo": ThreatLevel.HIGH.value,

    # Medium Threat Species (Livestock, crop-disruptive, property-damaging or mid-size animals)
    "dog": ThreatLevel.MEDIUM.value,
    "cow": ThreatLevel.MEDIUM.value,
    "horse": ThreatLevel.MEDIUM.value,
    "sheep": ThreatLevel.MEDIUM.value,
    "zebra": ThreatLevel.MEDIUM.value,
    "giraffe": ThreatLevel.MEDIUM.value,
    "monkey": ThreatLevel.MEDIUM.value,
    "fox": ThreatLevel.MEDIUM.value,
    "deer": ThreatLevel.MEDIUM.value,
    "jackal": ThreatLevel.MEDIUM.value,
    "kangaroo": ThreatLevel.MEDIUM.value,
    "wild boar": ThreatLevel.MEDIUM.value,
    "boar": ThreatLevel.MEDIUM.value,

    # Low Threat Species (Harmless, small, or low-risk animals)
    "bird": ThreatLevel.LOW.value,
    "cat": ThreatLevel.LOW.value,
    "squirrel": ThreatLevel.LOW.value,
    "penguin": ThreatLevel.LOW.value,
    "eagle": ThreatLevel.LOW.value,
    "owl": ThreatLevel.LOW.value,
    "mouse": ThreatLevel.LOW.value,
    "rat": ThreatLevel.LOW.value,
}

# Conservative default fallback for unexpected or uncataloged species
DEFAULT_FALLBACK_THREAT = ThreatLevel.MEDIUM.value

# Thread-safe in-memory cache of active threat rules: {normalized_species_name: threat_tier_str}
_cached_rules: Optional[Dict[str, str]] = None


def invalidate_threat_cache() -> None:
    """Invalidates the in-memory threat classification cache when settings or rules change."""
    global _cached_rules
    _cached_rules = None
    logger.debug("Threat classification rule cache invalidated.")


def get_default_threat_rules() -> Dict[str, str]:
    """Returns a copy of the default species-to-threat mapping."""
    return dict(DEFAULT_ANIMAL_THREAT_RULES)


def get_active_threat_rules() -> Dict[str, str]:
    """
    Retrieves the consolidated active threat classification mapping.
    Merges defaults with dynamic database rules and ProjectSettings overrides.
    Caches results in memory for high-performance video frame processing.
    """
    global _cached_rules
    if _cached_rules is not None:
        return _cached_rules

    rules = dict(DEFAULT_ANIMAL_THREAT_RULES)

    try:
        from apps.settings_app.models import AnimalThreatRule, ProjectSettings
        
        # 1. Overlay persistent AnimalThreatRule records
        db_rules = AnimalThreatRule.objects.filter(is_active=True)
        for rule in db_rules:
            norm_name = rule.animal_name.strip().lower()
            if norm_name and rule.threat_level in THREAT_HIERARCHY:
                rules[norm_name] = rule.threat_level.upper()

        # 2. Overlay legacy ProjectSettings threat_level_overrides for backward compatibility
        project_settings = ProjectSettings.objects.first()
        if project_settings and isinstance(project_settings.threat_level_overrides, dict):
            for species, tier in project_settings.threat_level_overrides.items():
                if isinstance(species, str) and isinstance(tier, str):
                    norm_tier = tier.strip().upper()
                    if norm_tier in THREAT_HIERARCHY:
                        rules[species.strip().lower()] = norm_tier

    except Exception as e:
        # Fallback gracefully during migrations, test setup, or before table initialization
        logger.debug(f"Unable to read DB threat rules; using defaults: {e}")

    _cached_rules = rules
    return _cached_rules


def classify_animal(
    animal_name: Optional[str],
    confidence: Optional[float] = None,
    custom_overrides: Optional[Dict[str, str]] = None
) -> str:
    """
    Authoritatively classifies a detected animal species into HIGH, MEDIUM, or LOW threat.

    :param animal_name: Name/label of the detected animal species.
    :param confidence: Optional detection confidence score.
    :param custom_overrides: Optional dictionary of species -> threat tier overrides.
    :return: Normalized uppercase string: 'HIGH', 'MEDIUM', or 'LOW'.
    """
    if not animal_name or not isinstance(animal_name, str):
        return DEFAULT_FALLBACK_THREAT

    normalized_name = animal_name.strip().lower()

    # 1. Check custom overrides if explicitly supplied
    if custom_overrides and isinstance(custom_overrides, dict):
        custom_tier = custom_overrides.get(normalized_name)
        if custom_tier and isinstance(custom_tier, str):
            tier_upper = custom_tier.strip().upper()
            if tier_upper in THREAT_HIERARCHY:
                return tier_upper

    # 2. Check active system rules (defaults + DB rules)
    active_rules = get_active_threat_rules()
    if normalized_name in active_rules:
        return active_rules[normalized_name]

    # 3. Fallback for unlisted animals
    return DEFAULT_FALLBACK_THREAT


def get_threat_score(threat_level: Optional[str]) -> int:
    """Returns numeric priority (3=HIGH, 2=MEDIUM, 1=LOW, 0=None)."""
    if not threat_level:
        return 0
    return THREAT_HIERARCHY.get(threat_level.strip().upper(), 1)


def calculate_highest_threat(
    detections: List[Dict[str, Any]]
) -> Tuple[Optional[str], Optional[str], float]:
    """
    Calculates overall highest threat animal, highest threat level, and highest confidence
    across multiple detected animals in a single frame/image.

    :param detections: List of detection dictionaries containing 'label'/'animal' and 'confidence'.
    :return: (highest_threat_animal, highest_threat_level, highest_confidence)
    """
    if not detections:
        return None, None, 0.0

    highest_animal: Optional[str] = None
    highest_level: Optional[str] = None
    highest_score = 0
    highest_conf = 0.0

    for det in detections:
        label = det.get('label') or det.get('animal') or det.get('animal_type')
        conf = float(det.get('confidence', 0.0))
        threat = det.get('threat_level') or classify_animal(label, conf)
        
        # Ensure uppercase normalized threat level
        threat_upper = threat.upper() if isinstance(threat, str) else DEFAULT_FALLBACK_THREAT
        score = get_threat_score(threat_upper)

        if score > highest_score or (score == highest_score and conf > highest_conf):
            highest_animal = label
            highest_level = threat_upper
            highest_score = score
            highest_conf = conf

    return highest_animal, highest_level, highest_conf
