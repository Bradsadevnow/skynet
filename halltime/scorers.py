from __future__ import annotations

from typing import Any, Dict, List


def _avg(values: List[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def score_movie(movie: Dict[str, Any]) -> Dict[str, float]:
    cast = movie.get("cast", [])
    beats = movie.get("beat_sheet", [])
    props = movie.get("props", [])
    contradictions = movie.get("contradiction_ledger", [])
    wine_mentions = sum(1 for beat in beats if "wine" in beat["text"].lower())
    basement_mentions = sum(1 for beat in beats if "basement" in beat["text"].lower())
    menace_scores = [float(person.get("threat_aura", 0.0)) for person in cast]
    plausibility_scores = [float(person.get("domestic_plausibility", 0.0)) for person in cast]

    slop_elegance = min(1.0, 0.32 + 0.06 * len(contradictions) + 0.03 * len(props))
    basement_gravity = min(1.0, 0.2 + 0.14 * basement_mentions + 0.08 * sum(1 for c in cast if c.get("basement_implication")))
    wine_saturation = min(1.0, 0.18 + 0.12 * wine_mentions + _avg([float(c.get("wine_scene_compatibility", 0.0)) for c in cast]))
    canon_drift = min(1.0, 0.25 + 0.09 * len(contradictions))
    kitchen_lighting_truth_index = min(1.0, 0.3 + 0.08 * sum(1 for beat in beats if "kitchen" in beat["text"].lower()))
    male_cardigan_threat_score = min(1.0, _avg(menace_scores) * 0.75 + (1.0 - _avg(plausibility_scores)) * 0.25)
    maternal_dread_persistence = min(1.0, 0.35 + 0.07 * sum(1 for beat in beats if "daughter" in beat["text"].lower() or "mother" in beat["text"].lower()))
    commercial_break_violence_potential = min(1.0, 0.2 + 0.07 * sum(1 for beat in beats if beat.get("cliffhanger")))

    return {
        "slop_elegance": round(slop_elegance, 4),
        "basement_gravity": round(basement_gravity, 4),
        "wine_saturation": round(wine_saturation, 4),
        "canon_drift": round(canon_drift, 4),
        "kitchen_lighting_truth_index": round(kitchen_lighting_truth_index, 4),
        "male_cardigan_threat_score": round(male_cardigan_threat_score, 4),
        "maternal_dread_persistence": round(maternal_dread_persistence, 4),
        "commercial_break_violence_potential": round(commercial_break_violence_potential, 4),
    }
