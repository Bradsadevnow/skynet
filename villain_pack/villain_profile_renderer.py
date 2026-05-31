from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


HERE = Path(__file__).resolve().parent
PROFILE_DIR = HERE / "professional_profiles"


def load_card(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def infer_open_to_work(card: Dict[str, Any]) -> str:
    family = card["villain_family"]
    modifier = card["modifier"]
    if family in {"corporate_predator", "mastermind"}:
        return "Open to board seats, strategic advisory work, and ethically negotiable leadership opportunities."
    if family in {"institutional_enforcer", "rogue_ai"}:
        return "Open to governance, containment, optimization, and strategic compliance roles."
    if modifier in {"performance_genius", "inherited_heir"}:
        return "Open to founder-adjacent, legacy-sensitive, and high-visibility repositioning work."
    return "Open to select opportunities where accountability remains pleasantly negotiable."


def infer_ecosystem_tone(card: Dict[str, Any]) -> str:
    family = card["villain_family"]
    sidekick = card["sidekick"]["role_label"]
    if family in {"corporate_predator", "institutional_enforcer"}:
        return f"workplace with escalating HR incident energy; sidekick lane: {sidekick}"
    if family in {"rogue_ai", "hubristic_creator"}:
        return f"blacksite startup with governance theater; sidekick lane: {sidekick}"
    if family in {"seductive_deceiver", "inherited_heir"}:
        return f"household empire with reputational seepage; sidekick lane: {sidekick}"
    return f"cult-adjacent ecosystem with unstable logistics; sidekick lane: {sidekick}"


def build_headline(card: Dict[str, Any]) -> str:
    family = card["villain_family"].replace("_", " ").title()
    competencies = card["core_competencies"]["items"][:2]
    competency_bits = [item.title() for item in competencies]
    return f"{family} | {' | '.join(competency_bits)}"


def render_profile(card: Dict[str, Any]) -> str:
    institution = card["institution"]
    sidekick = card["sidekick"]
    exposure = card["institutional_exposure"]
    competencies = card["core_competencies"]
    rot = card.get("petty_atrocity_profile", [card["petty_atrocity"]])
    moral_texture = card["moral_texture"]
    lines = [
        f"# {card['title']} Professional Profile",
        "",
        f"**Headline:** {build_headline(card)}",
        f"**Open To Work:** {infer_open_to_work(card)}",
        f"**Ecosystem Tone:** {infer_ecosystem_tone(card)}",
        f"**Credentialed By:** {institution['institution_name']}",
        "",
        "## About",
        (
            f"Currently operating at the intersection of {card['dramatic_function']} and "
            f"{card['failure_mode']}. Known for {competencies['items'][0]}, {competencies['items'][1]}, "
            f"and a broader civilian rot signature that begins with {card['petty_atrocity']['label']}."
        ),
        "",
        "## Moral Texture",
        f"- primary: {moral_texture['primary']}",
        f"- secondary: {', '.join(moral_texture['secondary'])}",
        f"- commons targeted: {moral_texture['commons_targeted']['type']} / {moral_texture['commons_targeted']['scope']}",
        f"- confrontation risk: {moral_texture['sanction_profile']['confrontation_risk']}",
        "",
        "## Institutional Exposure",
        f"- {exposure['label']}",
        f"- operational: {exposure['operational']}",
        f"- legal: {exposure['legal']}",
        f"- predatory: {exposure['predatory']}",
        "",
        "## Core Competencies",
    ]
    lines.extend(f"- {item}" for item in competencies["items"])
    lines.extend([
        "",
        "## Rot Profile",
    ])
    lines.extend(f"- {item['label']}" for item in rot)
    lines.extend([
        "",
        "## Sidekick Ecosystem",
        f"- role: {sidekick['role_label']}",
        f"- why they stay: {sidekick['loyalty_label']}",
        f"- what they handle: {sidekick['task_label']}",
        f"- competence: {sidekick['competence_label']}",
        f"- fold risk: {sidekick['fold_label']}",
        "",
        "## Education",
        f"- {institution['institution_name']}",
        f"- field of study: {institution['field_of_study']}",
        f"- accreditation: {institution['accreditation_body']}",
        f"- motto: {institution['motto']}",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a villain professional profile from an existing villain card JSON.")
    parser.add_argument("card_json", type=str)
    args = parser.parse_args()
    path = Path(args.card_json)
    card = load_card(path)
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    out = PROFILE_DIR / path.with_suffix(".md").name
    out.write_text(render_profile(card), encoding="utf-8")
    print(json.dumps({"input": str(path), "output": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
