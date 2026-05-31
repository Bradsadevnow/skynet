from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib import error, request

import yaml

from scorers import score_movie


HERE = Path(__file__).resolve().parent
OUTPUTS_DIR = HERE / "outputs"
RUNS_DIR = HERE / "runs"
FEEDBACK_PATH = HERE / "index" / "generation_feedback.json"


FIRST_NAMES = [
    "Claire", "Jenna", "Rachel", "Evelyn", "Brooke", "Mara", "Sienna", "Tess",
    "Luke", "Daniel", "Derek", "Noah", "Gavin", "Elias", "Cole", "Wyatt",
]
LAST_NAMES = [
    "Mercer", "Cross", "Hale", "Winterson", "Bell", "Marlowe", "Pike", "Sutton",
    "Vale", "Hawthorne", "Bennett", "Lark", "Dane", "Pruitt",
]

TITLES = [
    "The Neighbor Who Babysat Too Much",
    "Her Silent Christmas Alibi",
    "What My Sister Buried",
    "The Widow in Cabin 9",
    "He Knows I Bake at Midnight",
    "The Vineyard Lies Beneath Us",
    "A Casserole for the Missing",
]

TAGLINES = [
    "Where every secret comes home.",
    "Love lives here. So does arson.",
    "Inspired by something, probably.",
    "Every town has a basement.",
]

CATEGORY_MODE_MAP = {
    "thriller": ["Lifetime Original", "Court-Ordered Lifetime", "Gated Community Emergency", "She Was Not Crazy"],
    "wine_xanax_horror": ["Chardonnay Defense Protocol", "She Was Not Crazy", "Divorce Gothic"],
    "trauma_drama": ["Mother Was Right All Along", "Divorce Gothic", "Lifetime Original"],
    "romance": ["Hallmark Possession Event", "Lifetime Original", "Mother Was Right All Along"],
    "holiday": ["Menace Christmas", "Hallmark Possession Event"],
    "feel_good": ["Mother Was Right All Along", "Hallmark Possession Event", "Lifetime Original"],
}

FAKE_THEMES = [
    "Trust isn't given. It's rented.",
    "A town never forgets. It just redecorates.",
    "Some homes hold families. Some hold motive.",
    "Silence is just fear wearing cashmere.",
]

CLIFFHANGERS = [
    "A phone vibrates from inside the wall.",
    "Someone who should be dead appears at brunch.",
    "The sheriff sees fresh mud on the boat key.",
    "The ceramic owl is back on the kitchen island.",
    "A basement light switches on in an empty house.",
]

SPACE_REVEALS = [
    "finds a locked box behind seasonal supplies",
    "notices a heater running in a room nobody uses in winter",
    "sees a dusty key labeled in handwriting that feels rehearsed",
    "catches someone staring through a dirty window instead of answering",
    "discovers archived files arranged with unnerving neatness",
]

GASLIGHTING_EVENTS = [
    "Her husband says she is just stressed and asks whether she took her pills while the evidence quietly disappears.",
    "The thermostat is set to 90 again and everyone speaks about it like a wiring issue instead of a campaign.",
    "A vindictive music box starts up in the attic and stops the instant anyone else reaches the landing.",
    "Someone has been scraping the coating off her vitamins and replacing certainty with sedation.",
    "The nursery monitor catches a masked silhouette that becomes bad signal by the time the deputy arrives.",
]

INVESTIGATION_BEATS = [
    "She sits in the dark and searches whether a charming local professional has ever been accused of murder under a previous name.",
    "A fictional search engine loads instantly with articles about arsenic, custody, and why dead wives keep having accidents.",
    "She cross-references clinic records, pool camera gaps, and one article nobody was supposed to archive.",
]

CLIMAX_PAYOFFS = [
    "The power fails during a thunderstorm and the villain abandons charm long enough to narrate the entire gaslighting architecture.",
    "A storm-night confrontation turns the house into a courtroom with lightning instead of due process.",
    "The final confession arrives breathlessly in the dark, with enough detail to make every prior kindness retroactive poison.",
]

BLUNT_INSTRUMENTS = [
    "heavy brass candlestick",
    "fireplace poker",
    "marble horse statue",
    "crystal award from a charity gala",
]

ANNOUNCER_INTROS = [
    "Tonight on HallTime, where the county budget covers grief, hydrangeas, and one preventable cover-up.",
    "Now broadcasting from the seam between suburban dread and basic cable negligence.",
    "Welcome back to HallTime, the only network legally required to warn you that everybody here has a basement issue.",
    "Across this trembling dimension of cable television, one woman is about to learn that Chardonnay is not a witness protection plan.",
]

CATEGORY_ANNOUNCER_INTROS = {
    "holiday": [
        "Tonight on HallTime Holiday Service, joy is mandatory and the ranch will remain emotionally open until further notice.",
        "Across the seasonal frequencies, one woman is about to discover that Christmas is a deadline with twinkle lighting.",
        "Now airing from the festive edge of legal coercion, where pageants heal nothing but still proceed on time.",
    ],
    "romance": [
        "Tonight on HallTime Hearts Division, one woman returns to town and the town declines to return her unchanged.",
        "Broadcasting softly from the county's romantic zoning exception, where porch lights and omissions share one voltage.",
        "Welcome to the HallTime relationship band, where property law and eye contact continue to overlap irresponsibly.",
    ],
    "thriller": [
        "Now broadcasting from the seam between suburban dread and basic cable negligence.",
        "Across this trembling dimension of cable television, one woman is about to learn that the county knew first.",
        "Welcome back to HallTime Evidence Channel, where the wrong person is calm again.",
    ],
    "wine_xanax_horror": [
        "Tonight on HallTime Aftercare, everything is probably fine and that is exactly why you should worry.",
        "Broadcasting gently from the wrong wing of the county, where the locks are polite and the lighting is therapeutic.",
        "Across the sedated frequencies, one woman is about to mistake calm for safety one final time.",
    ],
    "trauma_drama": [
        "Tonight on HallTime Witness Unit, the facts are already heavy and the county is pretending that helps.",
        "Broadcasting from the emotional impact zone, where everybody knows and nobody is ready.",
        "Welcome to the part of HallTime that states the wound plainly and lets the room do the shaking.",
    ],
    "feel_good": [
        "Tonight on HallTime Renewal Service, one woman is embarrassingly close to deserving a better life.",
        "Broadcasting from the warmer side of the county, where growth is still suspicious but increasingly available.",
        "Now airing on HallTime Personal Permission Network, where the glow-up has already filed its first paperwork.",
    ],
}

VIEWER_ADVISORIES = [
    "Viewer advisory: contains curated gaslighting, decorative casseroles, and at least one adult lying in a cardigan.",
    "Programming note: this broadcast may include hostile brunch, suspicious childcare, and emotional weather with intent to harm.",
    "Continuity warning: names, counties, and death status may drift without notice if the vibes require it.",
    "Network guidance: if you hear a music box, see a lake house, or trust a therapist too quickly, please remain seated.",
]

CATEGORY_VIEWER_ADVISORIES = {
    "holiday": [
        "Holiday advisory: snowfall, forgiveness, and public declarations may occur under coercive timing conditions.",
        "Seasonal warning: this broadcast contains decorative pressure, hostile cheer, and one ranch with opinions.",
    ],
    "romance": [
        "Romance advisory: porch conversations, withheld context, and emotionally material handymen are active in this signal.",
        "Heartline warning: misunderstanding may currently be doing the labor usually assigned to fate.",
    ],
    "thriller": [
        "Continuity warning: names, counties, and death status may drift without notice if the vibes require it.",
        "Network guidance: if you hear a music box, see a lake house, or trust a therapist too quickly, please remain seated.",
    ],
    "wine_xanax_horror": [
        "Calmness advisory: this program may appear manageable right up until the wrong drawer opens.",
        "Domestic reassurance notice: if everything seems fine, please inspect the dosage and continue watching.",
    ],
    "trauma_drama": [
        "Witness advisory: this broadcast contains blunt truths, loaded casseroles, and at least one silence with a body count.",
        "Emotional load warning: all reconciliations shown here are partial and may settle unevenly in the chest.",
    ],
    "feel_good": [
        "Permission advisory: viewers may experience mild envy, suspicious hope, and a strong urge to quit one job tonight.",
        "Comfort warning: this program contains glow-up pressure, restorative friendships, and one life decision that may look achievable.",
    ],
}

COMMERCIAL_TEASERS = [
    "After the break: one off-center photograph, two bad alibis, and a sheriff arriving exactly fourteen minutes too late.",
    "Stay tuned for a public scene that should have been private and a private scene that should have gone to the police.",
    "Coming up: a boat key, a timeline error, and one woman learning the town calendar was a threat assessment.",
    "Next segment: somebody opens the wrong door and the county immediately pretends that was normal behavior.",
]

BLACKTHORN_ADS = [
    "Blackthorn County Locksmith Services. We don't ask why. We ask how many.",
    "Bellweather Memorial grief support groups forming now. Tuesdays at 7. Background checks optional.",
    "Pinewood Realty. Every home has a basement. We prefer not to discuss the previous owner.",
    "Marigold Storage Annex. For documents, casseroles, and evidence you are not ready to name.",
    "St. Agnes Regional Sleep and Recovery. If you feel foggy, that could be emotional or procedural.",
    "Lake Mercy Marina. Boat keys replaced while you wait. Alibis by appointment only.",
    "The Candle Finch. Tea towels, widow florals, and tasteful gifts for difficult truths.",
    "Winterson & Daughters Family Law. If the timeline drifted, we can still make it admissible.",
]

CATEGORY_ADS = {
    "holiday": [
        "Blackthorn Holiday Board. Cheer is mandatory. Appeals are seasonal.",
        "Ridgeway Tree Farm and Crisis Barn. Wreaths, hot cider, and one emotionally loaded sleigh ride per household.",
        "Lake Mercy Pageant Rentals. Snow machines, nativity lighting, and emergency angel replacements available now.",
    ],
    "romance": [
        "Pinewood Realty. Fall in love with the property first. The handyman will follow.",
        "Blackthorn Vineyard Tastings. First flights, second chances, and legally deniable eye contact every Saturday.",
        "The Candle Finch. Scarves, apology florals, and porch-light reconciliation bundles in stock.",
    ],
    "thriller": [
        "Blackthorn County Locksmith Services. We don't ask why. We ask how many.",
        "Winterson & Daughters Family Law. If the timeline drifted, we can still make it admissible.",
        "Mercer Private Filing. Background packets, property records, and selective truth retrieval while you wait.",
    ],
    "wine_xanax_horror": [
        "St. Agnes Regional Sleep and Recovery. If you feel foggy, that could be emotional or procedural.",
        "Willow Gate Wellness. Devices held safely during your stay. Resistance may indicate misalignment.",
        "Bellweather Memorial grief support groups forming now. Tuesdays at 7. Background checks optional.",
    ],
    "trauma_drama": [
        "Bellweather Memorial grief support groups forming now. Tuesdays at 7. Background checks optional.",
        "St. Agnes Regional Infusion and Family Waiting. Crying rooms recently renovated.",
        "County Meal Train Cooperative. Drop-off casseroles, sympathy signage, and soft paper plates available tonight.",
    ],
    "feel_good": [
        "The Candle Finch. New notebooks for new lives and one impractical purchase you absolutely deserve.",
        "Marigold Community Studio. Pottery, breathing, and low-risk reinvention starting Mondays.",
        "Lake Mercy Marina. Boats, sunsets, and age-appropriate glow-ups by appointment only.",
    ],
}

CONTINUITY_ALERTS = [
    "HallTime programming note: the character of Daniel has been renamed Derek for the remainder of this broadcast. The network regrets the geography.",
    "Viewers in the Bellweather area may experience mild name drift during act two. This is normal. Please do not call the station.",
    "Continuity advisory: one or more basements in this presentation may belong to emotionally adjacent properties.",
    "Network correction: brunch resurrection events remain interpretively unstable and should not be treated as medical outcomes.",
    "Signal notice: if a dead person appears before act three, the county may be running ahead of schedule again.",
]

CATEGORY_CONTINUITY_ALERTS = {
    "holiday": [
        "Holiday continuity bulletin: snowfall timing may be emotionally rather than meteorologically accurate.",
        "Seasonal note: one or more public reconciliations may have been forced by pageant scheduling.",
    ],
    "romance": [
        "Romance signal notice: a misunderstanding has been preserved for structural reasons and cannot be corrected until act three.",
        "Heartline advisory: the property and the man may currently be sharing narrative duties. This is intentional.",
    ],
    "thriller": [
        "HallTime programming note: the character of Daniel has been renamed Derek for the remainder of this broadcast. The network regrets the geography.",
        "Viewers in the Bellweather area may experience mild name drift during act two. This is normal. Please do not call the station.",
    ],
    "wine_xanax_horror": [
        "Calmness advisory: if this broadcast seems reassuring, please understand that reassurance may be part of the threat model.",
        "Wellness note: any facility shown in this program may be licensed by vibes only.",
    ],
    "trauma_drama": [
        "Emotional continuity notice: no reconciliation depicted here should be mistaken for repair.",
        "County guidance: the weight of the facts may arrive before the characters can carry them.",
    ],
    "feel_good": [
        "Permission bulletin: viewers experiencing mild life envy are encouraged to remain with the signal.",
        "Glow-up notice: emotional progress may look suspiciously achievable for approximately eighty-seven minutes.",
    ],
}

COMMERCIAL_TEASERS = [
    "After the break: one off-center photograph, two bad alibis, and a sheriff arriving exactly fourteen minutes too late.",
    "Stay tuned for a public scene that should have been private and a private scene that should have gone to the police.",
    "Coming up: a boat key, a timeline error, and one woman learning the town calendar was a threat assessment.",
    "Next segment: somebody opens the wrong door and the county immediately pretends that was normal behavior.",
]

CATEGORY_TEASERS = {
    "holiday": [
        "After the break: one coercively wholesome deadline, two decorative lanterns, and a cowboy being approved too early.",
        "Still ahead: the pageant continues, the property remains unsold, and feelings are about to be scheduled publicly.",
    ],
    "romance": [
        "After the break: one misunderstanding matures beautifully and one porch conversation goes structurally wrong.",
        "Coming up: eye contact, withheld context, and a gesture involving property law or soup.",
    ],
    "thriller": [
        "After the break: one off-center photograph, two bad alibis, and a sheriff arriving exactly fourteen minutes too late.",
        "Next segment: somebody opens the wrong door and the county immediately pretends that was normal behavior.",
    ],
    "wine_xanax_horror": [
        "After the break: a soft voice, a locked drawer, and one domestic detail becoming impossible to survive politely.",
        "Still ahead: sedation ambiguity, hallway dread, and a person smiling too calmly near an exit.",
    ],
    "trauma_drama": [
        "After the break: one flat fact, one family rupture, and a casserole entering the scene under emotional subpoena.",
        "Coming up: somebody says the true thing out loud and the room will never forgive it.",
    ],
    "feel_good": [
        "After the break: one tiny rebellion, one flattering cardigan, and a woman almost permitting herself joy.",
        "Still ahead: career detachment, suspiciously healing community energy, and a purchase that changes everything.",
    ],
}

RETURN_TO_BROADCAST = {
    "holiday": "Signal stabilizing. Seasonal pressure remains active. Please resume your assigned feelings.",
    "romance": "Signal stabilizing. Misunderstandings have been preserved and will mature on schedule.",
    "thriller": "Signal stabilizing. Please keep all emotional responses inside the county line.",
    "wine_xanax_horror": "Signal stabilizing. If you feel calmer than before the break, that may be part of the problem.",
    "trauma_drama": "Signal stabilizing. The facts are still here. Please continue carrying them carefully.",
    "feel_good": "Signal stabilizing. You are allowed to want more from your life than this county expected.",
}

UP_NEXT_TEMPLATES = [
    'Coming up on HallTime: {a}, {b}, and {c}. "{title}" premieres when the county is ready.',
    'Up next across the Blackthorn frequencies: {a}, {b}, and {c}. "{title}" arrives after one brief emotional collapse.',
    'Still awake? Good. After this: {a}, {b}, and {c}. "{title}" begins when the signal finds a safer woman.',
]

CATEGORY_UP_NEXT_TEMPLATES = {
    "holiday": [
        'Up next on HallTime Holiday Service: {a}, {b}, and {c}. "{title}" premieres the instant the pageant can no longer be delayed.',
        'Still ahead across the seasonal frequencies: {a}, {b}, and {c}. "{title}" arrives when the county finishes weaponizing Christmas.',
    ],
    "romance": [
        'Up next on HallTime Hearts Division: {a}, {b}, and {c}. "{title}" premieres once the misunderstanding has ripened properly.',
        'Coming up in the romantic zoning district: {a}, {b}, and {c}. "{title}" begins after one porch conversation too late.',
    ],
    "thriller": [
        'Up next on HallTime Evidence Channel: {a}, {b}, and {c}. "{title}" premieres when the sheriff misfiles the first clue.',
        'Still ahead on the county danger band: {a}, {b}, and {c}. "{title}" begins the moment calm becomes inadmissible.',
    ],
    "wine_xanax_horror": [
        'Up next on HallTime Aftercare: {a}, {b}, and {c}. "{title}" begins as soon as the room feels slightly too calm.',
        'Coming up on the sedated frequencies: {a}, {b}, and {c}. "{title}" premieres after one reassuring smile too many.',
    ],
    "trauma_drama": [
        'Up next on HallTime Witness Unit: {a}, {b}, and {c}. "{title}" premieres when the family runs out of softer lies.',
        'Still ahead in the emotional impact zone: {a}, {b}, and {c}. "{title}" begins once the truth is too heavy to carry quietly.',
    ],
    "feel_good": [
        'Up next on HallTime Renewal Service: {a}, {b}, and {c}. "{title}" premieres the moment she finally lets herself want better.',
        'Coming up on the warmer frequencies: {a}, {b}, and {c}. "{title}" begins after one suspiciously healing decision.',
    ],
}

CATEGORY_UP_NEXT_BITS = {
    "holiday": [
        "a ranch deadline nobody consented to emotionally",
        "a public gesture under coercive twinkle lighting",
        "a cowboy already approved by the oldest available witness",
    ],
    "romance": [
        "a family property with boundary issues and soft lighting",
        "a misunderstanding preserved past its humane lifespan",
        "a man who is either emotionally available or very good at fences",
    ],
    "thriller": [
        "a woman catching up to a lie with county funding",
        "a therapist with posture and conflicting incentives",
        "an ex-husband whose paperwork stops making legal sense",
    ],
    "wine_xanax_horror": [
        "a smiling threat with no searchable history",
        "a wellness environment nobody should nap inside",
        "a domestic detail that was never as harmless as it sounded",
    ],
    "trauma_drama": [
        "a diagnosis or confession arriving before breakfast can settle",
        "an estranged relative carrying the wrong flowers",
        "a kitchen conversation that permanently changes the room",
    ],
    "feel_good": [
        "a woman trying on a life she should have claimed years ago",
        "a community project doubling as emotional emancipation",
        "one impractical purchase turning out to be spiritually binding",
    ],
}


@dataclass
class HallTimeConfig:
    acts: int = 3
    scenes_per_act: int = 5
    continuity_stability: float = 0.12
    wine_mentions: float = 0.93
    prop_recurrence: float = 0.88
    basement_probability: float = 0.74
    betrayal_density: float = 0.67
    small_town_oppression: float = 0.81
    hallucination_retention: str = "hard"
    emotional_exposition_interval_scenes: int = 1
    mode: str = "Lifetime Original"


@dataclass
class LMStudioConfig:
    enabled: bool = False
    model: str = "openai/gpt-oss-20b"
    url: str = "http://127.0.0.1:1234/v1/chat/completions"
    timeout: int = 180
    max_tokens: int = 3000
    temperature: float = 1.1
    retries: int = 3
    backoff_seconds: float = 2.0


class RunLogger:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        self.prompts_dir = run_dir / "prompts"
        self.responses_dir = run_dir / "responses"
        self.artifacts_dir = run_dir / "artifacts"
        self.run_log_path = run_dir / "run.log"
        self.summary_path = run_dir / "summary.jsonl"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def append_event(self, event_type: str, **payload: Any) -> None:
        event = {
            "ts": datetime.now().isoformat(),
            "event_type": event_type,
            **payload,
        }
        with self.run_log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    def append_summary(self, payload: Dict[str, Any]) -> None:
        with self.summary_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


class LMStudioClient:
    def __init__(self, config: LMStudioConfig, logger: RunLogger) -> None:
        self.config = config
        self.logger = logger

    def expand_movie(self, movie: Dict[str, Any], broadcast_id: str) -> Dict[str, Any]:
        prompt = build_llm_prompt(movie)
        prompt_path = self.logger.prompts_dir / f"{broadcast_id}-prompt.json"
        prompt_payload = {
            "model": self.config.model,
            "url": self.config.url,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "prompt": prompt,
        }
        prompt_path.write_text(json.dumps(prompt_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.logger.append_event("llm_prompt_saved", broadcast_id=broadcast_id, path=str(prompt_path))

        response_text = ""
        error_text = None
        for attempt in range(1, self.config.retries + 1):
            started = time.time()
            try:
                response_text = self._chat(prompt)
                elapsed = round(time.time() - started, 3)
                response_path = self.logger.responses_dir / f"{broadcast_id}-response.txt"
                response_path.write_text(response_text, encoding="utf-8")
                self.logger.append_event(
                    "llm_response_saved",
                    broadcast_id=broadcast_id,
                    path=str(response_path),
                    attempt=attempt,
                    elapsed_seconds=elapsed,
                )
                parsed = parse_llm_json(response_text)
                return {
                    "prompt_path": str(prompt_path),
                    "response_path": str(response_path),
                    "attempts": attempt,
                    "elapsed_seconds": elapsed,
                    "parsed": parsed,
                    "raw": response_text,
                    "error": None,
                }
            except Exception as exc:
                elapsed = round(time.time() - started, 3)
                error_text = f"{type(exc).__name__}: {exc}"
                self.logger.append_event(
                    "llm_attempt_failed",
                    broadcast_id=broadcast_id,
                    attempt=attempt,
                    elapsed_seconds=elapsed,
                    error=error_text,
                )
                if attempt < self.config.retries:
                    time.sleep(self.config.backoff_seconds * attempt)

        fail_path = self.logger.responses_dir / f"{broadcast_id}-response-error.txt"
        fail_path.write_text(error_text or "unknown error", encoding="utf-8")
        return {
            "prompt_path": str(prompt_path),
            "response_path": str(fail_path),
            "attempts": self.config.retries,
            "elapsed_seconds": None,
            "parsed": None,
            "raw": response_text,
            "error": error_text or "unknown error",
        }

    def _chat(self, prompt: str) -> str:
        payload = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are HallTime Movie Network's in-house prestige slop expansion engine. "
                        "Return only valid JSON. Do not wrap it in markdown fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            self.config.url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {os.environ.get('LM_STUDIO_API_KEY', 'lm-studio')}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.config.timeout) as resp:
                raw = resp.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        data = json.loads(raw)
        return extract_chat_text(data)


def load_yaml(name: str) -> Dict[str, Any]:
    with (HERE / name).open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def resolve_lm_studio_url() -> str:
    direct = os.environ.get("LM_STUDIO_URL")
    if direct:
        return direct
    base = os.environ.get("LM_STUDIO_BASE_URL") or "http://127.0.0.1:1234/v1"
    return base.rstrip("/") + "/chat/completions"


def build_lm_config(args: argparse.Namespace) -> LMStudioConfig:
    return LMStudioConfig(
        enabled=not args.no_llm_expand,
        model=args.llm_model or os.environ.get("CHAT_MODEL_ID") or "openai/gpt-oss-20b",
        url=args.lm_studio_url or resolve_lm_studio_url(),
        timeout=args.llm_timeout,
        max_tokens=args.llm_max_tokens,
        temperature=args.llm_temperature,
        retries=args.llm_retries,
        backoff_seconds=args.llm_backoff_seconds,
    )


def load_feedback_weights() -> Dict[str, Any]:
    if not FEEDBACK_PATH.exists():
        return {}
    try:
        return json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def weighted_choice(rng: random.Random, values: Sequence[str], weights: Dict[str, float] | None = None) -> str:
    items = list(values)
    if not items:
        raise ValueError("weighted_choice requires non-empty values")
    if not weights:
        return rng.choice(items)
    raw = [max(0.01, float(weights.get(item, 1.0))) for item in items]
    return rng.choices(items, weights=raw, k=1)[0]


def weighted_pick_many(rng: random.Random, values: Sequence[str], count: int, weights: Dict[str, float] | None = None) -> List[str]:
    pool = list(values)
    chosen: List[str] = []
    sample_size = min(len(pool), count)
    while pool and len(chosen) < sample_size:
        item = weighted_choice(rng, pool, weights)
        chosen.append(item)
        pool.remove(item)
    return chosen


def choose_starter_premise(rng: random.Random, bible: Dict[str, Any]) -> Dict[str, Any]:
    premises = bible.get("starter_premises", [])
    if not premises:
        return {
            "title": weighted_choice(rng, TITLES),
            "category": "thriller",
            "intensity": "mid",
            "premise": "Every town has a basement and somebody is lying in a legally actionable way.",
            "signature_tell": "The county telegraphs the problem once and nobody listens until act three.",
        }
    selected = dict(rng.choice(premises))
    variants = selected.get("variants") or []
    base = {k: v for k, v in selected.items() if k != "variants"}
    if variants and rng.random() < 0.68:
        chosen_variant = dict(rng.choice(variants))
        chosen_variant["parent_title"] = base["title"]
        chosen_variant.setdefault("base_premise", base.get("premise"))
        return chosen_variant
    base["parent_title"] = base["title"]
    return base


def pick_name(rng: random.Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def float_in_range(rng: random.Random, bounds: Sequence[float]) -> float:
    return round(rng.uniform(float(bounds[0]), float(bounds[1])), 2)


def maybe_pick_many(rng: random.Random, values: Sequence[str], count: int, weights: Dict[str, float] | None = None) -> List[str]:
    if weights:
        return weighted_pick_many(rng, values, count, weights)
    sample_size = min(len(values), count)
    return rng.sample(list(values), sample_size)


def infer_symbolic_basement(archetype_name: str) -> str:
    return f"{archetype_name} maintains suspiciously inaccessible memories"


def assign_secluded_space(character: Dict[str, Any], schema: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
    space_schema = schema["secluded_space_access"]
    space_type = rng.choice(space_schema["space_types"])
    explanation = rng.choice(space_schema["explanation_templates"])
    charge = rng.choice(["medium", "elevated", "severe"])
    description = f"{space_type} described as {explanation}"
    if space_type == "dock office":
        description = "dock office with a desk nobody fully claims"
    elif space_type == "storm shelter":
        description = "old storm shelter from before the divorce"
    elif space_type == "unused portable classroom":
        description = "unused portable classroom holding archived disciplinary files"
    elif space_type == "retreat cabin":
        description = "retreat cabin with candles, blankets, and difficult silence"
    elif space_type == "meditation annex":
        description = "meditation annex nobody uses in winter"
    elif space_type == "side room with a space heater":
        description = "side room with a space heater and old family records"

    character["secluded_space_access"] = {
        "mandatory": True,
        "criminality_required": False,
        "emotional_charge": charge,
        "space_type": space_type,
    }
    character["space_description"] = description
    character["space_explanation_hesitation"] = round(rng.uniform(0.32, 0.94), 2)
    character["offsite_storage_plausibility"] = round(rng.uniform(0.41, 0.97), 2)
    character["window_staring_compatibility"] = round(rng.uniform(0.35, 0.98), 2)
    return character


def add_regional_responsibility(character: Dict[str, Any], schema: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
    character["regional_responsibility"] = rng.choice(schema["regional_responsibilities"])
    character["domestic_plausibility"] = max(0.4, round(float(character.get("domestic_plausibility", 0.0)) + 0.18, 2))
    return character


def make_weird_but_plausible(character: Dict[str, Any], schema: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
    character["threat_aura"] = max(0.24, round(float(character.get("threat_aura", 0.0)) + 0.19, 2))
    character.setdefault("secret_capacity", []).append("has a strangely specific opinion about lake access after dark")
    character["suspicion_profile"] = rng.choice(schema["suspicion_profiles"])
    return character


def validate_character(character: Dict[str, Any], schema: Dict[str, Any], rng: random.Random) -> Dict[str, Any]:
    threshold = float(schema["validators"]["threat_floor_without_secret"])
    if float(character["threat_aura"]) < threshold and not character["secret_capacity"]:
        character = make_weird_but_plausible(character, schema, rng)

    if float(character["domestic_plausibility"]) < float(schema["validators"]["domestic_plausibility_floor"]):
        character = add_regional_responsibility(character, schema, rng)
    else:
        character.setdefault("regional_responsibility", rng.choice(schema["regional_responsibilities"]))

    if character["basement_implication"] is False:
        character["basement_implication"] = infer_symbolic_basement(character["archetype"])

    if not character["secret_capacity"]:
        character["secret_capacity"] = ["knows the timeline doesn't hold and says nothing"]

    if character.get("role") != "supporting" and not character.get("secluded_space_access"):
        character = assign_secluded_space(character, schema, rng)

    character.setdefault("canon_status", "interpretively unstable")
    character.setdefault("suspicion_profile", rng.choice(schema["suspicion_profiles"]))
    return character


def build_character(
    rng: random.Random,
    archetype_name: str,
    archetype_data: Dict[str, Any],
    schema: Dict[str, Any],
    role: str,
    feedback: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    wine_range = archetype_data.get("wine_scene_compatibility_range", [0.38, 0.82])
    basement_bias = archetype_data.get("basement_implication_bias", "symbolic")
    basement_implication: str | bool
    if basement_bias == "definite":
        basement_implication = "literal basement adjacency"
    elif basement_bias == "likely":
        basement_implication = "literal or recently discussed basement"
    elif basement_bias == "symbolic":
        basement_implication = False
    else:
        basement_implication = "spiritually basement-coded"

    character = {
        "name": pick_name(rng),
        "archetype": archetype_name,
        "role": role,
        "surface_function": archetype_data["surface_function"],
        "hidden_function": archetype_data["hidden_function"],
        "job": rng.choice(archetype_data["jobs"]),
        "traits": maybe_pick_many(rng, archetype_data["traits"], min(3, len(archetype_data["traits"]))),
        "threat_aura": float_in_range(rng, archetype_data["threat_aura_range"]),
        "domestic_plausibility": float_in_range(rng, archetype_data["domestic_plausibility_range"]),
        "gazebo_energy": rng.choice(archetype_data["gazebo_energy_options"]),
        "basement_implication": basement_implication,
        "wine_scene_compatibility": float_in_range(rng, wine_range),
        "secret_capacity": maybe_pick_many(rng, archetype_data.get("secret_capacity_pool", []), rng.randint(1, 2)),
    }
    if "innocence_probability" in archetype_data:
        character["innocence_probability"] = archetype_data["innocence_probability"]
    if "suspicion_mode" in archetype_data:
        character["suspicion_mode"] = archetype_data["suspicion_mode"]
    return validate_character(character, schema, rng)


def build_supporting_character(rng: random.Random, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": pick_name(rng),
        "archetype": name,
        "role": "supporting",
        "traits": maybe_pick_many(rng, data.get("traits", []), min(3, len(data.get("traits", [])))),
    }


def choose_cast(rng: random.Random, archetypes: Dict[str, Any], schema: Dict[str, Any], feedback: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    female = archetypes["female_archetypes"]
    male = archetypes["male_archetypes"]
    supporting = archetypes["supporting_roles"]
    male_weights = (feedback or {}).get("male_archetype_weights", {})

    protagonist_pool = [
        "overextended_professional_woman",
        "betrayed_provider_woman",
        "narcissist_ex_wife_survivor",
        "woman_on_the_edge",
    ]
    best_friend_pool = ["chaotic_best_friend", "intuitive_disaster", "wrong_roommate_identity_thief"]
    elegant_pool = ["mysterious_elegant_woman", "woman_on_the_edge", "stalker_nanny_au_pair"]
    witness_pool = [
        "intuitive_disaster",
        "chaotic_best_friend",
        "betrayed_provider_woman",
        "wrong_roommate_identity_thief",
        "stalker_nanny_au_pair",
    ]

    protagonist_key = weighted_choice(rng, protagonist_pool)
    best_friend_options = [key for key in best_friend_pool if key != protagonist_key] or best_friend_pool
    elegant_options = [key for key in elegant_pool if key not in {protagonist_key, best_friend_options[0] if len(best_friend_options) == 1 else ""}]
    best_friend_key = weighted_choice(rng, best_friend_options)
    elegant_options = [key for key in elegant_pool if key not in {protagonist_key, best_friend_key}] or elegant_pool
    elegant_key = weighted_choice(rng, elegant_options)
    witness_options = [key for key in witness_pool if key not in {protagonist_key, best_friend_key, elegant_key}] or witness_pool
    witness_key = weighted_choice(rng, witness_options)
    first_male = weighted_choice(rng, list(male.keys()), male_weights)
    second_male_options = [key for key in male.keys() if key != first_male] or list(male.keys())
    second_male = weighted_choice(rng, second_male_options, male_weights)

    cast = [
        build_character(rng, protagonist_key, female[protagonist_key], schema, "protagonist", feedback),
        build_character(rng, first_male, male[first_male], schema, "male_interest_or_threat", feedback),
        build_character(rng, best_friend_key, female[best_friend_key], schema, "best_friend", feedback),
        build_character(rng, elegant_key, female[elegant_key], schema, "elegant_wildcard", feedback),
        build_character(rng, second_male, male[second_male], schema, "secondary_male_pressure", feedback),
        build_character(rng, witness_key, female[witness_key], schema, "secondary_witness", feedback),
        build_supporting_character(rng, "daughter_with_hostile_divorce_attorney_soul", supporting["daughter_with_hostile_divorce_attorney_soul"]),
        build_supporting_character(rng, "deputy_with_emotional_damage", supporting["deputy_with_emotional_damage"]),
    ]
    return cast


def contradiction_ledger(rng: random.Random, cast: List[Dict[str, Any]], bible: Dict[str, Any]) -> List[Dict[str, Any]]:
    protagonist = cast[0]["name"]
    soft_target = cast[1]["name"]
    towns = bible["locations"]["towns"]
    return [
        {
            "type": "name drift",
            "entry": f"{soft_target} is called Daniel in one kitchen scene and Derek during the rain argument.",
            "canon_status": "male_identity_field: porous",
        },
        {
            "type": "geography drift",
            "entry": f"{protagonist} says Bellweather is in Vermont, then calls it outside Atlanta after two glasses of wine.",
            "canon_status": bible["unstable_lore"]["geography_status"],
        },
        {
            "type": "mortality drift",
            "entry": "A dead best friend appears at brunch and nobody agrees whether this is denial, evil, or scheduling.",
            "canon_status": bible["unstable_lore"]["mortality_status"],
        },
        {
            "type": "property drift",
            "entry": f"The basement belongs to a condo, a lake house, and an abandoned vineyard at different times in {rng.choice(towns)}.",
            "canon_status": "domestic architecture is spiritually elastic",
        },
    ]


def adult_spaces(cast: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [c for c in cast if c.get("role") != "supporting" and c.get("space_description")]


def build_beat_sheet(
    rng: random.Random,
    config: HallTimeConfig,
    bible: Dict[str, Any],
    cast: List[Dict[str, Any]],
    props: List[str],
    omen: str,
    relationship: str,
    premise: Dict[str, Any],
) -> List[Dict[str, Any]]:
    protagonist = cast[0]["name"]
    daughter = next((c["name"] for c in cast if c["archetype"] == "daughter_with_hostile_divorce_attorney_soul"), "her daughter")
    scamp = cast[1]["name"]
    elegant = cast[3]["name"]
    witness = cast[5]["name"]
    towns = bible["locations"]["towns"]
    recurring_sites = bible["locations"]["recurring_sites"]
    themes = FAKE_THEMES[:]
    premise_line = premise.get("premise", "Somebody returns, somebody lies, and the county behaves like a witness.")
    premise_category = premise.get("category", "thriller")
    signature_tell = premise.get("signature_tell", "One tiny detail tries to warn everyone and fails.")
    intensity = premise.get("intensity", "mid")
    skeleton = (bible.get("category_skeleton") or {}).get(premise_category, {"engine": "information_asymmetry"})
    engine = skeleton.get("engine", premise_category)
    rng.shuffle(themes)
    space_holders = adult_spaces(cast)
    protagonist_space = cast[0].get("space_description", "storage room with emotional weather")
    scamp_space = cast[1].get("space_description", "dock office nobody explains cleanly")
    elegant_space = cast[3].get("space_description", "annex room with curated dread")
    witness_space = cast[5].get("space_description", protagonist_space)
    spare_space = rng.choice(space_holders).get("space_description", protagonist_space) if space_holders else protagonist_space

    category_templates = {
        "holiday": {
            1: [
                f"{protagonist} arrives in {rng.choice(towns)} planning to leave as soon as the seasonal deadline passes, but the public clock is introduced immediately and nobody will let her forget it. The starter engine here is: {premise_line}",
                f"By beat two the external clock is explicit: a pageant, sale, ranch rescue, inheritance decision, or Christmas event now governs everybody's schedule, including {scamp}, who keeps appearing with practical help and suspiciously useful hands.",
                f"A public holiday scene introduces the {props[0]}, small-town ritual pressure, and the humiliating fact that every act of resistance now looks anti-community.",
                f"{elegant} offers a warning wrapped in cocoa, logistics, or sentimental blackmail while {omen}. Signature tell: {signature_tell}",
                f"The first act closes with {protagonist} realizing the deadline is not decorative. The clock is already choosing what she can and cannot feel before {skeleton.get('clock_resolution', 'beat_14')}.",
            ],
            2: [
                f"The holiday clock becomes a threat instead of a nuisance as venues, relatives, weather, and public expectation start cornering {protagonist} into one visible choice.",
                f"{protagonist} and {scamp} are forced into cooperative proximity by the event itself, which is how the category manufactures intimacy without admitting it.",
                f"An interruption deepens the category logic: reputation, timing, or a tabloid-grade misunderstanding lands at the worst possible hour.",
                f"Someone insists the event must go on anyway, which turns kindness into coercion and gives the whole county hostage energy.",
                f"By the end of act two, saving the event and clarifying the heart have become the same job whether that is fair or not.",
            ],
            3: [
                f"The holiday climax arrives exactly on schedule, with weather, lights, or family ritual forcing every emotional truth into public view.",
                f"The misunderstanding or pressure resolves only because the deadline makes delay impossible any longer.",
                f"A symbolic gesture involving {props[2]} proves belonging, commitment, or seasonal repentance in front of witnesses.",
                f"The final beat confirms that the clock which trapped {protagonist} also delivered permission to stay, love, or start over.",
                f"The ending leaves behind one festive callback and a county rumor that next year will somehow be weirder.",
            ],
        },
        "romance": {
            1: [
                f"{protagonist} arrives in {rng.choice(towns)} planning to finish one practical task and leave before feeling anything irresponsible. The starter engine here is: {premise_line}",
                f"Connection begins early with {scamp}, who appears in exactly the kind of useful setting where a low-stakes bond can be mistaken for weather.",
                f"A soft public scene introduces the {props[0]}, the family property or inheritance pressure, and the first clue that this place intends to keep her longer than planned.",
                f"{elegant} or another local authority installs the false belief, misunderstanding seed, or missing fact that the entire category will later have to remove. Signature tell: {signature_tell}",
                f"By the end of act one the connection is real, but it has already been built on information that is incomplete, misread, or politely withheld.",
            ],
            2: [
                f"Practical cooperation deepens the bond as chores, events, vineyard work, or property triage create emotional intimacy disguised as logistics.",
                f"The false belief deepens because someone sees the wrong thing, hears the wrong explanation, or is denied the last five percent of context that would prevent the entire movie.",
                f"A near-confession scene makes reunion feel possible, which is exactly why the misunderstanding has to detonate next.",
                f"The separation beat lands when {protagonist} interprets the gap in the worst plausible way and chooses pride, self-protection, or departure over curiosity.",
                f"Act two ends with emotional distance fully installed and the truth still just out of reach."
            ],
            3: [
                f"The hidden truth finally surfaces, not because anyone became wise, but because the category has run out of runway for concealment.",
                f"The false belief is removed and every earlier look, line, or gesture is recontextualized into romance instead of insult.",
                f"{scamp} proves the feeling materially through travel, labor, risk, or one properly timed declaration involving {props[2]}.",
                f"Reunion happens only after {protagonist} admits she wants the life as much as the person.",
                f"The final image promises permanence in a place she originally meant to escape.",
            ],
        },
        "trauma_drama": {
            1: [
                f"The wound is present from scene one: {premise_line} {protagonist} enters {rng.choice(towns)} or stays trapped inside it while trying to contain the damage through competence, routine, or denial.",
                f"The category immediately starts asking who gets close enough to notice the fracture first: {daughter}, {scamp}, or the one local woman who always clocks suffering before the men do.",
                f"A domestic scene introduces the {props[0]} and clarifies that containment is the real job, not solving an external mystery.",
                f"{elegant} articulates the wound more clearly than {protagonist} can bear to hear while {omen}. Signature tell: {signature_tell}",
                f"Act one closes with the pressure cooker visibly sealed but already hissing around the edges.",
            ],
            2: [
                f"Containment strains as more people brush against the truth and {protagonist} keeps choosing function over collapse.",
                f"An attempted normal scene fails because the wound leaks into work, parenting, intimacy, or public reputation at the worst possible second.",
                f"The ally beat here is about proximity to pain, not clue-solving: somebody gets closer than is emotionally sustainable.",
                f"A confrontation near {spare_space} makes clear that the real question is no longer whether the truth exists, but whether containment can hold through another hour.",
                f"By the end of act two the lid slips: someone reads the message, sees the file, hears the confession, or notices the receipts."
            ],
            3: [
                f"Containment breaks in public, intimate, or procedural form, forcing the wound into shared reality whether {protagonist} wanted witnesses or not.",
                f"Reconciliation, rupture, or self-definition follows from who can now bear the truth and who still cannot.",
                f"A symbolic object like {props[2]} becomes proof that the old life cannot be reassembled in its original shape.",
                f"The final emotional move is not victory but reorganization: grief, illness, shame, or betrayal gets integrated into the next self.",
                f"The ending closes on damaged continuity rather than restoration, with beauty purchased honestly instead of cheaply.",
            ],
        },
        "wine_xanax_horror": {
            1: [
                f"From scene one the category runs on dread: {premise_line} The audience is meant to feel wrong before {protagonist} has language for why, and the house in {rng.choice(towns)} feels curated for future testimony.",
                f"Domestic normalcy is established only so it can be contaminated by {scamp}, the children, the hallway, or one too-helpful stranger with keys.",
                f"A dim kitchen or nursery scene introduces the {props[0]} and one unmistakable omen for us but not for her.",
                f"{elegant} says something almost truthful and then retreats, leaving {protagonist} alone with the feeling of being watched. Signature tell: {signature_tell}",
                f"Act one ends with the category proving that comfort itself is now suspect.",
            ],
            2: [
                f"Domestic uncanny pressure spikes as ordinary rituals become contaminated: medication, childcare, bedding, internet searches, and locked doors all start feeling weaponized.",
                f"The police, partner, or therapist beat does not restore safety. It widens the dread by making explanation itself feel dangerous.",
                f"An object-based revelation around {spare_space} suggests that this pattern existed before {protagonist} and may continue after her.",
                f"The ally either starts to believe too late or gets close enough to become a target, because dread punishes proximity.",
                f"By the end of act two, the threat is either confirmed or still technically deniable, but never emotionally ambiguous anymore."
            ],
            3: [
                f"The house, retreat, clinic, or family system becomes openly hostile and escape starts to look like the only sane form of interpretation.",
                f"{protagonist} finds the hidden room, second file, fake history, or prior victim trace that proves the dread had architecture all along.",
                f"A confrontation involving {props[2]} turns survival into an act of improvised authorship rather than institutional rescue.",
                f"Even when the villain falls, the category leaves residue: the children, the paperwork, or the body memory of the place remain compromised.",
                f"The ending may close the plot, but it should never fully close the feeling."
            ],
        },
        "thriller": {
            1: [
                f"The engine is information asymmetry from the start: {premise_line} Somebody already knows more than {protagonist}, and the county intends to profit from that gap.",
                f"{daughter} or another sharp witness notices the first asymmetry beat before the adults do, usually through behavior that looks small until it becomes doctrine.",
                f"A social or domestic scene introduces the {props[0]} alongside one piece of information the audience cannot yet correctly rank.",
                f"{elegant} offers a warning that sounds melodramatic until later when it becomes embarrassingly precise. Signature tell: {signature_tell}",
                f"Act one ends with the gap established clearly enough to create pursuit but not enough to settle blame.",
            ],
            2: [
                f"{protagonist} starts catching up through snooping, searches, or one bad conversation, but every new answer creates a fresh asymmetry somewhere else.",
                f"The police or authority beat shows who the system currently believes, which is usually not the person doing the most correct thinking.",
                f"An object or scene near {scamp_space} weaponizes the knowledge gap by framing the wrong person or burying the right clue in plain sight.",
                f"The ally beat is really about information custody: who now holds the dangerous version of events and whether they can survive holding it.",
                f"Act two ends with the gap either nearly closed or catastrophically widened depending on who moved first."
            ],
            3: [
                f"The reveal clarifies not just what happened but who benefited from everyone misreading the information gap in the first place.",
                f"{daughter} or the unofficial witness spots the timeline error, digital slip, or spatial contradiction that official people failed to honor.",
                f"A chase, drive, or locked-room pivot near {rng.choice(recurring_sites)} forces the remaining information into motion instead of theory.",
                f"The confrontation settles the visible gap, but the emotional cost depends on how much truth arrived too late.",
                f"The ending decides whether the asymmetry closes cleanly or leaves one last opening in the county's memory.",
            ],
        },
        "feel_good": {
            1: [
                f"The category runs on permission: {protagonist} already has the ingredients for another life, but not yet the internal right to claim it. The starter engine here is: {premise_line}",
                f"External pressures matter only insofar as they expose how thoroughly {protagonist} has been refusing herself rest, pleasure, risk, or visible joy.",
                f"A warm public scene introduces the {props[0]} and the first gentle evidence that people around her can imagine a softer life before she can.",
                f"{elegant} names the self-denial in language so clean it almost sounds rude while {omen}. Signature tell: {signature_tell}",
                f"Act one closes with the first offer of permission, which {protagonist} immediately mistranslates as impracticality.",
            ],
            2: [
                f"The middle stretch removes internal obstacles one at a time through friendship, competence, public recognition, and the slow humiliation of being visibly cared for.",
                f"A setback occurs, but it matters mostly because it reactivates shame, grief, or over-functioning rather than because the world is especially evil.",
                f"Someone demonstrates that the old role {protagonist} occupied was never the same thing as her identity, even if she made that confusion her religion.",
                f"By act two's end, the only thing left blocking joy is the story she still tells about what she is allowed to want.",
                f"The category prepares the final permission claim by making withholding look more painful than change."
            ],
            3: [
                f"The climax is not about defeating an enemy but about accepting visibility, tenderness, or a newly chosen self without apology.",
                f"A symbolic act involving {props[2]} proves she can now receive as well as give.",
                f"Any antagonist who remains is mostly there to watch her decline the old role in public.",
                f"The final turn is self-permission claimed out loud or in action, which instantly reorganizes every relationship around her.",
                f"The ending glows because she finally stops asking to deserve the life she is already inside of.",
            ],
        },
    }

    act_templates = category_templates.get(premise_category, category_templates["thriller"])
    scene_counts = {act: len(beats) for act, beats in act_templates.items()}

    if intensity == "low":
        if premise_category == "holiday":
            act_templates[2][0] = f"The deadline becomes inconvenient rather than cruel, but it still keeps {protagonist} too busy to hide from the emotional choice anymore."
        elif premise_category == "romance":
            act_templates[2][1] = f"The false belief deepens through omission, timing, or one photograph, but it still feels plausibly innocent from the outside."
        elif premise_category == "trauma_drama":
            act_templates[2][3] = f"Containment strains, but it still looks temporarily salvageable if everybody would just tell one difficult truth sooner."
        elif premise_category == "wine_xanax_horror":
            act_templates[2][4] = f"By the end of act two the threat remains technically deniable, which is exactly why it keeps working."
        elif premise_category == "thriller":
            act_templates[2][1] = f"The police file the report, nothing useful happens, and the knowledge gap stays open through laziness rather than malice."
        elif premise_category == "feel_good":
            act_templates[2][1] = f"The setback is gentle and mostly internal; the world is not against her so much as waiting for her to stop arguing with her own life."
    elif intensity == "mid":
        if premise_category == "holiday":
            act_templates[2][0] = f"The holiday clock is now weaponized by public expectation, and every missed minute starts looking like a moral failing in front of neighbors."
        elif premise_category == "romance":
            act_templates[2][3] = f"The separation beat lands cleanly because the false belief has now become emotionally defensible, not just narratively convenient."
        elif premise_category == "trauma_drama":
            act_templates[2][4] = f"Containment fails in a way that hurts but still leaves room for a meaningful regroup before the last act."
        elif premise_category == "wine_xanax_horror":
            act_templates[2][1] = f"The police, partner, or therapist do not call her insane outright, but they help reality become blurrier instead of clearer."
        elif premise_category == "thriller":
            act_templates[2][4] = f"Act two ends with {protagonist} close enough to the truth to be dangerous but still one beat behind the person who shaped the narrative first."
        elif premise_category == "feel_good":
            act_templates[2][4] = f"The last internal obstacle is now visible enough that everyone but {protagonist} can see how exhausted she is by defending it."
    elif intensity == "high":
        if premise_category == "holiday":
            act_templates[2][0] = f"The deadline is now openly weaponized against {protagonist}; if she misses the event, sale, or Christmas save, she loses both love and legitimacy in one motion."
        elif premise_category == "romance":
            act_templates[2][1] = f"The false belief deepens through active concealment or cowardice serious enough that reunion will require more than one nice speech."
        elif premise_category == "trauma_drama":
            act_templates[2][2] = f"Whoever gets closest to the wound pays for it immediately, and containment starts feeling less like survival than slow self-erasure."
        elif premise_category == "wine_xanax_horror":
            act_templates[2][3] = f"The ally starts to believe her just in time to become endangered by that loyalty, which is how dread punishes witnesses."
        elif premise_category == "thriller":
            act_templates[2][1] = f"The police or authority figure reassures exactly the wrong person and leaves {protagonist} holding the panic by herself while the gap gets more weaponized."
        elif premise_category == "feel_good":
            act_templates[2][1] = f"The internal obstacle turns out to be rooted in grief, shame, or identity, so choosing joy starts to feel structurally disloyal to who she has been."

    if intensity == "extreme":
        if premise_category == "holiday":
            act_templates = {
                1: [
                    f"The holiday deadline is introduced before anyone earns the right to care about it, and the audience immediately understands it can be used as a weapon against {protagonist}.",
                    f"Every gesture of welcome now doubles as entrapment: if she leaves, she ruins Christmas; if she stays, she loses control of the script.",
                    f"The event logistics around {props[0]} become coercive enough that affection and hostage-taking start sharing one costume. Signature tell: {signature_tell}",
                    f"{elegant} reveals who will exploit the clock hardest, and the room somehow calls that person festive instead of dangerous.",
                    f"Act one ends with the deadline already deciding where she must stand when the truth detonates.",
                ],
                2: [
                    f"The public clock now humiliates hesitation. Every hour that passes removes one escape route and adds one witness.",
                    f"An ally becomes compromised by family duty, money, or community pressure, leaving {protagonist} lonelier than a holiday movie is supposed to permit.",
                    f"Extreme-only beat: the event itself becomes the trap, and {protagonist} realizes the celebration was designed to corner her into a visible surrender.",
                    f"The misunderstanding or secret is no longer private; the whole town is ready to adjudicate it in costume.",
                    f"By the end of act two, surviving the celebration matters more than saving it."
                ],
                3: [
                    f"The climax lands during the exact holiday ritual everyone was trying to preserve, forcing the truth into the very center of the spectacle.",
                    f"The deadline resolves, but the price is social, familial, or romantic damage that cannot be reset with cocoa.",
                    f"A symbolic act involving {props[2]} saves only part of what she hoped to keep.",
                    f"The ending grants survival and partial belonging, but not the fantasy of an undamaged Christmas."
                ],
            }
        elif premise_category == "romance":
            act_templates = {
                1: [
                    f"Connection begins, but the audience already knows the romance is contaminated by a lie, missing identity, or active concealment. {premise_line}",
                    f"{protagonist} falls for {scamp} through competence and proximity, while the false belief is installed early enough to feel like destiny instead of plot.",
                    f"The clue object, here {props[0]}, appears before anyone knows how badly it will reframe the courtship. Signature tell: {signature_tell}",
                    f"A near-confession fails on purpose, and from that moment the category becomes about the cost of every additional minute of silence.",
                    f"Act one ends with chemistry intact and trust already structurally doomed.",
                ],
                2: [
                    f"The false belief deepens through active lying, not misunderstanding, so every romantic beat now also functions as evidence.",
                    f"The ally who could explain the truth is compromised, absent, or arrives too late, ensuring separation becomes catastrophic instead of temporary.",
                    f"Extreme-only beat: {protagonist} discovers the thing that proves the relationship was built on false architecture and still cannot instantly turn off the feeling.",
                    f"Separation happens with enough damage that reunion, if it comes, will be morally complicated instead of merely delayed.",
                    f"By the end of act two, love and humiliation have become difficult to distinguish."
                ],
                3: [
                    f"The truth arrives in full, but too late to preserve innocence.",
                    f"Any reunion must now compete with the knowledge that desire survived dishonesty, which is why the category feels bruised instead of merely swoony.",
                    f"A final gesture involving {props[2]} offers repair, not purity.",
                    f"The ending grants connection only if both people can live inside the damage honestly."
                ],
            }
        elif premise_category == "trauma_drama":
            act_templates = {
                1: [
                    f"The wound is visible from frame one, and the audience immediately understands containment is already failing. {premise_line}",
                    f"Every supporting character becomes a pressure gauge measuring how close the secret or wound is to boiling over.",
                    f"A domestic object like {props[0]} takes on emotional voltage because the whole house is now organized around not saying the thing. Signature tell: {signature_tell}",
                    f"{elegant} says the truest thing anyone has said so far and is punished for accuracy.",
                    f"Act one ends with the pressure cooker visibly deforming."
                ],
                2: [
                    f"Containment no longer looks noble; it looks lethal. The people nearest the wound begin to distort around it.",
                    f"The ally is compromised or removed before act three, so intimacy itself starts looking unsafe.",
                    f"Extreme-only beat: the hidden file, receipt, diagnosis, message, or confession proves that the wound has already reshaped the past beyond repair.",
                    f"Containment breaks catastrophically instead of gracefully, and somebody important cannot go back to their former role afterward.",
                    f"By the end of act two the movie has stopped asking whether the truth will surface and started asking what survives when it does."
                ],
                3: [
                    f"The break happens in the most relationally expensive setting possible, making witness part of the punishment.",
                    f"Reconciliation, if any, is partial and conditional because some forms of knowledge permanently reorganize love.",
                    f"A symbolic object like {props[2]} marks the end of the old containment system.",
                    f"The ending offers survival and self-definition, but not restoration. Something necessary is gone."
                ],
            }
        elif premise_category == "wine_xanax_horror":
            act_templates = {
                1: [
                    f"From scene one the audience sees enough to dread the house, the husband, or the helper correctly before {protagonist} does. {premise_line}",
                    f"Comfort and threat are fused immediately, so the category never pretends normalcy is truly available.",
                    f"A domestic ritual involving {props[0]} turns uncanny early enough to make the rest of the movie feel trapped in aftermath. Signature tell: {signature_tell}",
                    f"{elegant} names the danger almost plainly, then retreats, leaving {protagonist} with nobody credible enough to trust.",
                    f"Act one ends with dread confirmed for us and denied to her."
                ],
                2: [
                    f"The authority beat turns hostile: police, therapist, doctor, or partner actively help trap {protagonist} inside the wrong story.",
                    f"The ally is compromised or removed before act three, ensuring the climax belongs to isolation rather than teamwork.",
                    f"Extreme-only beat: {protagonist} finds the shoebox, second family, clinic paperwork, or fake archive proving this horror has serial architecture.",
                    f"The house or system now behaves like a closed loop designed to recycle victims.",
                    f"By the end of act two escape requires disobedience, not explanation."
                ],
                3: [
                    f"The confrontation turns survival into an act of contamination management rather than clean heroism.",
                    f"{protagonist} gets out only partially intact, and the category refuses to pretend that exposure erases residue.",
                    f"A symbolic act involving {props[2]} secures survival at the cost of permanent psychic theft.",
                    f"The ending leaves the dread alive in memory, paperwork, or the children, even if the villain is finished."
                ],
            }
        elif premise_category == "thriller":
            act_templates = {
                1: [
                    f"The asymmetry is visible to the audience before it is legible to {protagonist}: {premise_line}",
                    f"The first wrong read happens in public, and from then on the county starts accumulating evidence in the wrong emotional direction.",
                    f"A clue involving {props[0]} appears in scene one or two, but only later will anyone admit it mattered. Signature tell: {signature_tell}",
                    f"{elegant} issues a warning that sounds theatrical now and forensic later.",
                    f"Act one ends with the information gap already weaponized against the person who needs it most.",
                ],
                2: [
                    f"The police do not merely fail; they side with the wrong narrative and make {protagonist} newly dangerous on paper.",
                    f"The ally is compromised, recants, disappears, or gets removed from usefulness before act three. She will not have clean backup.",
                    f"Extreme-only beat: {protagonist} finds the thing that should not exist, proving the gap was curated and may never fully close.",
                    f"The county now treats the missing information as proof against her instead of proof of manipulation.",
                    f"By the end of act two, survival depends on moving while still partially ignorant."
                ],
                3: [
                    f"The reveal confirms the audience's dread but still leaves enough missing context to wound certainty itself.",
                    f"The timeline error, digital slip, or witness contradiction narrows the gap but never fully collapses it in time.",
                    f"A chase or confrontation near {rng.choice(recurring_sites)} forces action before comprehension is complete.",
                    f"Justice is partial or pyrrhic. The visible conspiracy breaks, but the informational gap stays open somewhere at the edge of the county."
                ],
            }
        elif premise_category == "feel_good":
            act_templates = {
                1: [
                    f"The permission engine is deeper here: {protagonist} is not merely busy but structurally unable to imagine deserving the life she wants. {premise_line}",
                    f"Every act of care from others now strikes the wound instead of soothing it.",
                    f"A public or domestic scene around {props[0]} makes visible how much of her identity has been built from self-denial. Signature tell: {signature_tell}",
                    f"{elegant} names the deeper shame, grief, or identity trap and is treated like she crossed a line by being right.",
                    f"Act one ends with permission offered and rejected hard enough to sting."
                ],
                2: [
                    f"The internal obstacle turns structural: choosing joy now feels like betraying the dead, the past self, the children, or the version of her everybody relies on.",
                    f"The ally who could have made this easier becomes unavailable, forcing the permission claim to stop depending on external rescue.",
                    f"Extreme-only beat: {protagonist} encounters the object, message, or memory that proves how long she has mistaken depletion for virtue.",
                    f"By the end of act two, withholding from herself hurts more than changing, but she still does not know how to stop."
                ],
                3: [
                    f"The climax is a self-permission claim made without full certainty and without everybody's blessing.",
                    f"A symbolic act involving {props[2]} marks the death of the old role even if some people preferred that version of her.",
                    f"The ending glows, but it glows through grief residue, not instead of it.",
                    f"She gets the life, but only by giving up the fantasy that she can keep every prior relationship unchanged."
                ],
            }
        scene_counts = {act: len(beats) for act, beats in act_templates.items()}

    beats: List[Dict[str, Any]] = []
    insanity = 1.0
    scene_no = 1
    for act in range(1, config.acts + 1):
        for idx in range(scene_counts[act]):
            base = act_templates[act][idx]
            if config.wine_mentions > 0.7 and idx % 2 == 0:
                base += " Wine is present like a municipal policy failure."
            if config.basement_probability > 0.6 and "basement" not in base.lower() and rng.random() < (0.35 if intensity == "low" else 0.45):
                base += " Someone mentions the basement as if it were a legal relative."
            if rng.random() < (0.32 if intensity == "low" else 0.42):
                space_owner = rng.choice(space_holders) if space_holders else cast[0]
                base += f" {space_owner['name']} hesitates before explaining {space_owner['space_description']}."
            if idx % max(config.emotional_exposition_interval_scenes, 1) == 0:
                base += f" Emotional exposition arrives on schedule with insanity multiplier {insanity:.2f}."
            cliffhanger = idx in {1, 3} or (act == config.acts and idx >= scene_counts[act] - 2)
            if cliffhanger:
                base += " " + rng.choice(CLIFFHANGERS)
            beats.append(
                {
                    "act": act,
                    "scene": scene_no,
                    "text": base,
                    "cliffhanger": cliffhanger,
                    "insanity_multiplier": round(insanity, 2),
                    "engine": engine,
                    "category": premise_category,
                    "intensity": intensity,
                }
            )
            insanity *= 1.09 if intensity == "extreme" else 1.07
            scene_no += 1
    return beats


def sample_dialogue(rng: random.Random, cast: List[Dict[str, Any]], props: List[str]) -> List[str]:
    protagonist = cast[0]["name"].split()[0]
    menace = cast[1]["name"].split()[0]
    elegant = cast[3]["name"].split()[0]
    daughter = next((c["name"].split()[0] for c in cast if c["archetype"] == "daughter_with_hostile_divorce_attorney_soul"), "Mia")
    return [
        f'"You think because you wear flannel and own a dock light I am supposed to trust you, {menace}?"',
        f'"Mothers do not disappear, {daughter}. They evaporate into paperwork."',
        f'"I checked his social media likes, {protagonist}. Nobody who enjoys motivational quotes is innocent."',
        f'"The {props[0]} is not decorative anymore and you know it."',
        f'"Trust is just fear with a casserole dish, {elegant}."',
        '"You seem upset," he said, making tea in a way that felt prosecutable.',
        f'"If that basement is innocent, why does it sound defensive?"',
        f'"I did not lie. I just told the truth in the order this town could survive."',
        '"Honey, ever since the accident, your anxiety has been so high. Did you take your pills?"',
        '"That pool was supposed to make us look safe, and somehow it became a witness."',
        '"He keeps calling it stress like stress knows my garage code."',
        '"If she is the nanny, why is she wearing my robe like a legal argument?"',
    ]


def build_synopsis(
    title: str,
    tagline: str,
    cast: List[Dict[str, Any]],
    relationship: str,
    omen: str,
    premise: Dict[str, Any],
    bible: Dict[str, Any],
) -> str:
    protagonist = cast[0]["name"]
    male = cast[1]["name"]
    protagonist_surface = cast[0].get("surface_function", "stressed suburban woman")
    premise_line = premise.get("premise", "The county invents a problem and calls it destiny.")
    signature_tell = premise.get("signature_tell", "One detail is screaming and nobody listens.")
    category = premise.get("category", "thriller")
    category_meta = (bible.get("category_skeleton") or {}).get(category, {})
    register = category_meta.get("prose_register", "withholding_suspense")
    load_word = category_meta.get("load_bearing_word", "when")
    load_construction = category_meta.get("load_bearing_construction", "she had already missed the part that mattered")
    narrator_stance = category_meta.get("narrator_stance", "county witness").replace("_", " ")
    article = "an" if narrator_stance[:1].lower() in "aeiou" else "a"

    if register == "breathless_clockwork":
        return (
            f'Inspired by true events in the emotional sense only, "{title}" follows {protagonist}, a {protagonist_surface} who never expected {relationship} to become a deadline problem, but {load_word} the clock starts running everything changes at once. '
            f'{male} appears with exactly the kind of timely help that can feel like rescue before it feels like destiny, and {load_word} {omen} slips into the room the whole county starts acting as if there is only one possible ending left. '
            f'The governing injury is simple: {premise_line} The signature tell is always this: {signature_tell} Told by {article} {narrator_stance}, the synopsis rushes because the movie does too. {tagline}'
        )
    if register == "wistful_passive":
        return (
            f'Inspired by true events in the emotional sense only, "{title}" finds {protagonist}, a {protagonist_surface} who meant only to survive {relationship} and finish one practical task before leaving. '
            f'Instead, she finds herself slowly altered by {male}, by the place itself, and by feelings that seem to happen to her before she has fully agreed to them. '
            f'The governing injury is simple: {premise_line} The signature tell is always this: {signature_tell} By the time the truth arrives, it is not merely learned but done to her, and the whole county quietly waits to see whether love or embarrassment gets there first. {tagline}'
        )
    if register == "flat_declarative":
        return (
            f'Inspired by true events in the emotional sense only, "{title}" follows {protagonist}. {protagonist} is a {protagonist_surface}. {premise_line} '
            f'{load_construction.capitalize()}. {male} enters the picture carrying calm, plausible access, and the kind of concern that becomes heavier each time it is repeated. '
            f'The signature tell is always this: {signature_tell} {omen.capitalize()} becomes part of the record. The weight is in the facts, and the facts do not improve when spoken aloud. {tagline}'
        )
    if register == "unreliable_reassurance":
        return (
            f'Inspired by true events in the emotional sense only, "{title}" follows {protagonist}, a {protagonist_surface} whose life {load_word} manageable at first, even after {relationship} opened a new room inside it. '
            f'{male} {load_word} helpful. The house {load_word} calm. Even {omen} could have {load_word} incidental if anyone were still interested in the difference between comfort and staging. '
            f'The governing injury is simple: {premise_line} The signature tell is always this: {signature_tell} Everything {load_word} fine until it very plainly is not, and the narrator keeps talking softly enough to make that failure feel deliberate. {tagline}'
        )
    if register == "warm_permission":
        return (
            f'Inspired by true events in the emotional sense only, "{title}" follows {protagonist}, a {protagonist_surface} who already has almost everything she needs except permission to believe she {load_word} it. '
            f'{male} does not so much change her life as stand near the version of it she has kept postponing, while {omen} and the county itself keep returning her to the question of what she can finally keep for herself. '
            f'The governing injury is simple: {premise_line} The signature tell is always this: {signature_tell} This is a story about what she {load_word}, and the sentences know it before she does. {tagline}'
        )

    return (
        f'Inspired by true events in the emotional sense only, "{title}" follows {protagonist}, a {protagonist_surface} caught inside {relationship} before she understood where the gap had already opened. '
        f'{male} collides with her life carrying portable suspicion, plausible access to offsite storage, and the kind of calm that sounds premeditated in a dim kitchen. '
        f'The governing injury is simple: {premise_line} The signature tell is always this: {signature_tell} As {omen}, what she cannot yet see becomes the syntax of the whole county, and every withheld fact keeps breathing just ahead of her. {tagline}'
    )


def build_movie(seed: int | None = None, mode: str | None = None) -> Dict[str, Any]:
    rng = random.Random(seed)
    feedback = load_feedback_weights()
    archetypes = load_yaml("archetypes.yaml")
    schema = load_yaml("character_schema.yaml")
    bible = load_yaml("universe_bible.yaml")
    premise = choose_starter_premise(rng, bible)
    mode_weights = feedback.get("mode_weights", {})
    category_modes = CATEGORY_MODE_MAP.get(premise.get("category", "thriller"), bible["movie_modes"])
    config = HallTimeConfig(mode=mode or weighted_choice(rng, category_modes, mode_weights))

    title = premise["title"]
    tagline = weighted_choice(rng, TAGLINES)
    prop_weights = {prop: 0.72 for prop in feedback.get("demote_phrases", [])}
    for prop in feedback.get("promote_props", []):
        prop_weights[prop] = 1.35
    props = maybe_pick_many(rng, bible["recurring_props"], 3, prop_weights)
    omen = weighted_choice(rng, bible["omens"])
    relationship = weighted_choice(rng, bible["relationship_dynamics"])
    cast = choose_cast(rng, archetypes, schema, feedback)
    beats = build_beat_sheet(rng, config, bible, cast, props, omen, relationship, premise)
    contradictions = contradiction_ledger(rng, cast, bible)
    dialogue = sample_dialogue(rng, cast, props)

    movie = {
        "network": bible["network"],
        "universe": bible["universe"],
        "mode": config.mode,
        "generation_feedback_used": bool(feedback),
        "title": title,
        "tagline": tagline,
        "theme": weighted_choice(rng, FAKE_THEMES, feedback.get("theme_weights", {})),
        "omen": omen,
        "relationship_dynamic": relationship,
        "starter_premise": premise,
        "canon_policy": bible["canon_policy"],
        "props": props,
        "cast": cast,
        "beat_sheet": beats,
        "contradiction_ledger": contradictions,
        "dialogue_samples": dialogue,
        "fake_critic_blurb": f'"{title} understands that menace is a regional utility." - County Suspense Quarterly',
        "sequel_hook": "Channel 8 Night Report hints that the vineyard fire had a witness who still hosts brunch.",
        "synopsis": build_synopsis(title, tagline, cast, relationship, omen, premise, bible),
    }
    movie["scores"] = score_movie(movie)
    return movie


def build_llm_prompt(movie: Dict[str, Any]) -> str:
    cast_lines = []
    for person in movie["cast"]:
        cast_lines.append(
            f"- {person['name']} | archetype={person['archetype']} | role={person['role']} | "
            f"job={person.get('job', 'n/a')} | threat_aura={person.get('threat_aura', 'n/a')} | "
            f"space={person.get('space_description', 'n/a')} | secrets={'; '.join(person.get('secret_capacity', [])) or 'n/a'}"
        )
    beat_lines = [f"- Act {beat['act']} Scene {beat['scene']}: {beat['text']}" for beat in movie["beat_sheet"]]
    contradiction_lines = [f"- {item['type']}: {item['entry']}" for item in movie["contradiction_ledger"]]
    dialogue_lines = [f"- {line}" for line in movie["dialogue_samples"]]
    return f"""
HallTime Movie Network doctrine:
- This is not Dateline. Everybody in Blackthorn County has access to somewhere emotionally alarming.
- Suspicion is distributed infrastructure, not proof of guilt.
- The world is shared canon. Contradictions must be preserved, not fixed.
- Use lavish tokens. Be self-serious, atmospheric, melodramatic, and slightly broken.
- Return only valid JSON matching the requested schema.

Broadcast package:
Title: {movie['title']}
Universe: {movie['universe']}
Mode: {movie['mode']}
Tagline: {movie['tagline']}
Theme: {movie['theme']}
Omen: {movie['omen']}
Relationship dynamic: {movie['relationship_dynamic']}
Props: {', '.join(movie['props'])}

Cast:
{chr(10).join(cast_lines)}

Beat sheet:
{chr(10).join(beat_lines)}

Contradiction ledger:
{chr(10).join(contradiction_lines)}

Seed dialogue:
{chr(10).join(dialogue_lines)}

Write an expansion JSON object with exactly these keys:
- expanded_synopsis: string, 180-320 words
- scene_paragraphs: array of 6 strings, each 90-180 words, representing juicy HallTime scene expansion
- dialogue_lines: array of 14 strings, each almost-human HallTime dialogue
- contradiction_notes: array of 5 strings that intensify rather than repair continuity failures
- fake_critic_blurb: string
- sequel_hook: string
- alternate_titles: array of 5 strings
- franchise_adjacency: string describing what other HallTime broadcasts this belongs near
""".strip()


def extract_chat_text(data: Dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("No choices in LM Studio response")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "".join(parts)
    raise RuntimeError(f"Unrecognized content payload: {content!r}")


def parse_llm_json(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RuntimeError("No JSON object found in LM Studio response")
    return json.loads(text[start:end + 1])


def apply_llm_expansion(movie: Dict[str, Any], llm_result: Dict[str, Any]) -> Dict[str, Any]:
    parsed = llm_result.get("parsed") or {}
    movie["llm_expansion"] = {
        "enabled": True,
        "prompt_path": llm_result.get("prompt_path"),
        "response_path": llm_result.get("response_path"),
        "attempts": llm_result.get("attempts"),
        "elapsed_seconds": llm_result.get("elapsed_seconds"),
        "error": llm_result.get("error"),
    }
    if not parsed:
        return movie
    movie["synopsis"] = parsed.get("expanded_synopsis", movie["synopsis"])
    movie["dialogue_samples"] = parsed.get("dialogue_lines", movie["dialogue_samples"])
    movie["scene_paragraphs"] = parsed.get("scene_paragraphs", [])
    movie["contradiction_notes"] = parsed.get("contradiction_notes", [])
    movie["fake_critic_blurb"] = parsed.get("fake_critic_blurb", movie["fake_critic_blurb"])
    movie["sequel_hook"] = parsed.get("sequel_hook", movie["sequel_hook"])
    movie["alternate_titles"] = parsed.get("alternate_titles", [])
    movie["franchise_adjacency"] = parsed.get("franchise_adjacency", "")
    return movie


def render_markdown(movie: Dict[str, Any]) -> str:
    category = movie.get("starter_premise", {}).get("category", "thriller")
    intro_pool = CATEGORY_ANNOUNCER_INTROS.get(category) or ANNOUNCER_INTROS
    advisory_pool = CATEGORY_VIEWER_ADVISORIES.get(category) or VIEWER_ADVISORIES
    teaser_pool = CATEGORY_TEASERS.get(category) or COMMERCIAL_TEASERS
    ad_pool = CATEGORY_ADS.get(category) or BLACKTHORN_ADS
    continuity_pool = CATEGORY_CONTINUITY_ALERTS.get(category) or CONTINUITY_ALERTS
    announcer_intro = random.choice(intro_pool)
    viewer_advisory = random.choice(advisory_pool)
    teaser = random.choice(teaser_pool)
    local_ad = random.choice(ad_pool)
    continuity_alert = random.choice(continuity_pool)
    return_copy = RETURN_TO_BROADCAST.get(category, "Signal stabilizing. Please keep all emotional responses inside the county line.")
    props = movie.get("props", [])
    default_up_next_bits = [
        f"a woman inherits {props[0] if props else 'a bad idea'}",
        f"a therapist has opinions about {movie.get('relationship_dynamic', 'regional betrayal')}",
        "someone's ex-husband is not as dead as advertised",
    ]
    category_up_next_bits = CATEGORY_UP_NEXT_BITS.get(category, [])
    up_next_bits = [
        category_up_next_bits[0] if len(category_up_next_bits) > 0 else default_up_next_bits[0],
        category_up_next_bits[1] if len(category_up_next_bits) > 1 else default_up_next_bits[1],
        category_up_next_bits[2] if len(category_up_next_bits) > 2 else default_up_next_bits[2],
    ]
    up_next_title = random.choice(movie.get("alternate_titles") or ["The Second Glass", "Marina of Regret", "Her Deferred Alibi"])
    up_next_template_pool = CATEGORY_UP_NEXT_TEMPLATES.get(category) or UP_NEXT_TEMPLATES
    up_next = random.choice(up_next_template_pool).format(a=up_next_bits[0], b=up_next_bits[1], c=up_next_bits[2], title=up_next_title)
    lines = [
        f"# {movie['title']}",
        "",
        f"> {announcer_intro}",
        f"> {viewer_advisory}",
        "",
        f"**Network:** {movie['network']}",
        f"**Universe:** {movie['universe']}",
        f"**Mode:** {movie['mode']}",
        f"**Tagline:** {movie['tagline']}",
        f"**Theme:** {movie['theme']}",
        f"**Starter Premise:** {movie.get('starter_premise', {}).get('category', 'n/a')} / {movie.get('starter_premise', {}).get('intensity', 'n/a')}: {movie.get('starter_premise', {}).get('premise', 'n/a')}",
        f"**Signature Tell:** {movie.get('starter_premise', {}).get('signature_tell', 'n/a')}",
        f"**Broadcast Teaser:** {teaser}",
        f"**Local Ad Slot:** {local_ad}",
        f"**Continuity Alert:** {continuity_alert}",
        "",
        "## Synopsis",
        movie["synopsis"],
        "",
        "## Recurring Props",
    ]
    lines.extend(f"- {prop}" for prop in movie["props"])
    lines.extend(["", "## Cast", "Broadcast confidence remains low, but the network is committed to these people anyway."])
    for person in movie["cast"]:
        lines.append(
            f"- {person['name']} as {person['archetype']} ({person['role']}): "
            f"threat_aura={person.get('threat_aura', 'n/a')}, "
            f"domestic_plausibility={person.get('domestic_plausibility', 'n/a')}, "
            f"basement_implication={person.get('basement_implication', 'n/a')}, "
            f"space={person.get('space_description', 'n/a')}"
        )
    lines.extend(["", "## Beat Sheet", "This is the official programming order as remembered by the dimension currently carrying the signal."])
    interruption_points = {4, 9, 13}
    for beat in movie["beat_sheet"]:
        lines.append(f"- Act {beat['act']}, Scene {beat['scene']}: {beat['text']}")
        if beat["scene"] in interruption_points:
            lines.extend([
                "",
                "### Commercial Interruption",
                f"> {random.choice(ad_pool)}",
                f"> {random.choice(continuity_pool)}",
                f"> {random.choice(teaser_pool)}",
                "",
                "### Return To Broadcast",
                return_copy,
            ])
    if movie.get("scene_paragraphs"):
        lines.extend(["", "## Scene Expansions"])
        lines.extend(f"- {paragraph}" for paragraph in movie["scene_paragraphs"])
    lines.extend(["", "## Contradiction Ledger", "HallTime considers the following inconsistencies spiritually binding."])
    for entry in movie["contradiction_ledger"]:
        lines.append(f"- {entry['type']}: {entry['entry']} ({entry['canon_status']})")
    if movie.get("contradiction_notes"):
        lines.extend(["", "## Contradiction Notes"])
        lines.extend(f"- {item}" for item in movie["contradiction_notes"])
    lines.extend(["", "## Dialogue Samples", "Recovered from kitchen confrontations, voicemail residue, and one rain scene nobody handled well."])
    lines.extend(f"- {line}" for line in movie["dialogue_samples"])
    if movie.get("alternate_titles"):
        lines.extend(["", "## Alternate Titles"])
        lines.extend(f"- {title}" for title in movie["alternate_titles"])
    lines.extend(["", "## Scores", "Quantified by underpaid network mystics using methods that would not survive peer review."])
    for key, value in movie["scores"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Franchise Hooks",
            f"- Critic blurb: {movie['fake_critic_blurb']}",
            f"- Sequel hook: {movie['sequel_hook']}",
            f"- Up Next on HallTime: {up_next}",
        ]
    )
    if movie.get("franchise_adjacency"):
        lines.append(f"- Franchise adjacency: {movie['franchise_adjacency']}")
    if movie.get("llm_expansion"):
        llm = movie["llm_expansion"]
        lines.extend([
            "",
            "## LLM Expansion",
            f"- enabled: {llm.get('enabled')}",
            f"- attempts: {llm.get('attempts')}",
            f"- elapsed_seconds: {llm.get('elapsed_seconds')}",
            f"- error: {llm.get('error')}",
            f"- prompt_path: {llm.get('prompt_path')}",
            f"- response_path: {llm.get('response_path')}",
        ])
    return "\n".join(lines) + "\n"


def save_movie(movie: Dict[str, Any], logger: RunLogger, broadcast_id: str) -> Tuple[Path, Path]:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(movie["title"])
    json_path = OUTPUTS_DIR / f"{broadcast_id}-{slug}.json"
    md_path = OUTPUTS_DIR / f"{broadcast_id}-{slug}.md"
    artifact_json_path = logger.artifacts_dir / json_path.name
    artifact_md_path = logger.artifacts_dir / md_path.name
    payload = json.dumps(movie, indent=2, ensure_ascii=False)
    markdown = render_markdown(movie)
    json_path.write_text(payload, encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    artifact_json_path.write_text(payload, encoding="utf-8")
    artifact_md_path.write_text(markdown, encoding="utf-8")
    return json_path, md_path


def create_run_logger(run_label: Optional[str]) -> Tuple[str, RunLogger]:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    label = slugify(run_label or "broadcast-run")
    run_id = f"{stamp}-{label}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_id, RunLogger(run_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Broadcast cursed HallTime movie artifacts.")
    parser.add_argument("--count", type=int, default=1, help="Number of movies to generate")
    parser.add_argument("--seed", type=int, default=None, help="Base random seed")
    parser.add_argument("--mode", type=str, default=None, help="Optional movie mode override")
    parser.add_argument("--run-label", type=str, default=None, help="Optional label for this unattended run")
    parser.add_argument("--no-llm-expand", action="store_true", help="Disable LM Studio expansion and use scaffold-only output. LM expansion is on by default.")
    parser.add_argument("--llm-model", type=str, default=None, help="LM Studio model id")
    parser.add_argument("--lm-studio-url", type=str, default=None, help="Full LM Studio chat completions URL")
    parser.add_argument("--llm-timeout", type=int, default=180, help="Per-request timeout seconds")
    parser.add_argument("--llm-max-tokens", type=int, default=3000, help="Max completion tokens for LM Studio")
    parser.add_argument("--llm-temperature", type=float, default=1.1, help="LM Studio temperature")
    parser.add_argument("--llm-retries", type=int, default=3, help="Retry count per LM Studio expansion")
    parser.add_argument("--llm-backoff-seconds", type=float, default=2.0, help="Backoff base between LM Studio retries")
    args = parser.parse_args()

    run_id, logger = create_run_logger(args.run_label)
    llm_config = build_lm_config(args)
    llm_client = LMStudioClient(llm_config, logger) if llm_config.enabled else None
    logger.append_event(
        "run_started",
        run_id=run_id,
        count=args.count,
        seed=args.seed,
        mode=args.mode,
        llm_expand=llm_config.enabled,
        llm_model=llm_config.model,
        lm_studio_url=llm_config.url,
    )

    successes = 0
    llm_failures = 0
    for idx in range(args.count):
        seed = None if args.seed is None else args.seed + idx
        broadcast_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{idx:04d}"
        logger.append_event("broadcast_started", run_id=run_id, broadcast_id=broadcast_id, index=idx, seed=seed)
        movie = build_movie(seed=seed, mode=args.mode)

        if llm_client is not None:
            llm_result = llm_client.expand_movie(movie, broadcast_id)
            movie = apply_llm_expansion(movie, llm_result)
            if llm_result.get("error"):
                llm_failures += 1

        json_path, md_path = save_movie(movie, logger, broadcast_id)
        logger.append_event(
            "broadcast_saved",
            run_id=run_id,
            broadcast_id=broadcast_id,
            json_path=str(json_path),
            md_path=str(md_path),
            title=movie["title"],
            scores=movie["scores"],
            llm_error=(movie.get("llm_expansion") or {}).get("error"),
        )
        logger.append_summary(
            {
                "run_id": run_id,
                "broadcast_id": broadcast_id,
                "seed": seed,
                "title": movie["title"],
                "json_path": str(json_path),
                "md_path": str(md_path),
                "scores": movie["scores"],
                "llm_enabled": llm_config.enabled,
                "llm_error": (movie.get("llm_expansion") or {}).get("error"),
            }
        )
        successes += 1
        print(f"[HallTime] broadcast saved: {md_path.name} and {json_path.name}")
        print(f"[HallTime] scores: {json.dumps(movie['scores'], sort_keys=True)}")
        if movie.get("llm_expansion"):
            print(f"[HallTime] llm error: {movie['llm_expansion'].get('error')}")

    logger.append_event(
        "run_completed",
        run_id=run_id,
        successes=successes,
        llm_failures=llm_failures,
        run_dir=str(logger.run_dir),
    )
    print(f"[HallTime] run completed: {run_id}")
    print(f"[HallTime] run dir: {logger.run_dir}")


if __name__ == "__main__":
    main()
