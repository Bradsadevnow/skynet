from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from world_derivation import derive_company, derive_property_listing, load_card

HERE = Path(__file__).resolve().parent
OUTPUTS_DIR = HERE / "property_listings"


def render_listing(listing: dict, card: dict) -> str:
    lines = [
        f"# {listing['title']}",
        "",
        f"**Property Type:** {listing['property_type']}",
        f"**Price:** {listing['price']}",
        f"**Maintenance:** {listing['maintenance_cost']}",
        f"**Spatial Footprint:** {listing['spatial_footprint']}",
        f"**Location Vibe:** {listing['location_vibe']}",
        f"**Listed By:** {listing['listed_by']}",
        f"**Hero Infestation Risk:** {listing['hero_infestation_risk']}",
        f"**Superweapon Zoning Status:** {listing['superweapon_zoning_status']}",
        f"**Monologue Chair:** {listing['monologue_chair_status']}",
        f"**Escape Pod Access:** {listing['escape_pod_access']}",
        "",
        "## Description",
        listing['description'],
        "",
        "## Amenities",
    ]
    lines.extend(f"- {item}" for item in listing['amenities'])
    lines.extend([
        "",
        "## Villain MLS Risk Flags",
        f"- lair liability: {listing['lair_liability']}",
        f"- acoustic threat quality: {listing['acoustic_threat_quality']}",
        f"- shark tank maintenance rules: {listing['shark_tank_maintenance_rules']}",
        f"- historical coup density: {listing['historical_coup_density']}",
        f"- nearest extradition-safe airstrip: {listing['nearest_extradition_safe_airstrip']}",
        f"- entry screening protocol: {listing['entry_screening_protocol']}",
        f"- worker morale note: {listing['worker_morale_note']}",
        f"- supply run vulnerability: {listing['supply_run_vulnerability']}",
        "",
        "## Listing Warning",
        listing['listing_warning'],
        "",
        "## Disclosure Exemptions",
    ])
    lines.extend(f"- {item}" for item in listing['disclosure_exemptions'])
    lines.extend([
        "",
        "## Seller Disclosures",
        f"- current operating environment: {card['operating_environment']}",
        f"- favored leverage: {card['favorite_leverage']}",
        f"- sidekick traffic: {card['sidekick']['role_label']} handling {card['sidekick']['task_label']}",
        f"- recurring civilian rot nearby: {card['petty_atrocity']['label']}",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Zillow-style villain property listing from a villain card JSON.")
    parser.add_argument("card_json", type=str)
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    card = load_card(Path(args.card_json))
    company = derive_company(card, rng)
    listing = derive_property_listing(card, company, rng)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    out = OUTPUTS_DIR / (Path(args.card_json).stem + ".md")
    out.write_text(render_listing(listing, card), encoding="utf-8")
    print(json.dumps({"input": args.card_json, "output": str(out), "listing": listing['title']}, ensure_ascii=False))


if __name__ == "__main__":
    main()
