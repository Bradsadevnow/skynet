from __future__ import annotations

import argparse
import json
import math
import os
import re
from datetime import datetime
from urllib import error, request
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


HERE = Path(__file__).resolve().parent
OUTPUTS_DIR = HERE / "outputs"
INDEX_DIR = HERE / "index"
EDITORIAL_DIR = INDEX_DIR / "editorial"
DOCTRINE_PHRASES = [
    "just storage",
    "emotionally true",
    "interpretively unstable",
    "portable suspicion",
    "municipal policy failure",
    "regional utility",
    "brunch",
    "vineyard fire",
    "kitchen",
    "basement",
    "ceramic owl",
    "casserole dish",
    "boat key",
    "unopened letter",
]
CLUSTER_RULES = {
    "Vineyard Gothic": ["vineyard", "orchard", "wine", "chapel"],
    "Marina Suspicion Cycle": ["marina", "dock", "boat", "lake"],
    "Christmas Orchard Conspiracy": ["christmas", "ornament", "winter", "tree farmer"],
    "Wellness Retreat Menace": ["retreat", "meditation", "wellness", "cabin"],
    "Divorce Lake Canon": ["divorce", "lake", "storm shelter", "custody"],
    "Decorative Husband Quadrilogy": ["decorative_husband", "husband", "storage unit", "voicemail"],
}


@dataclass
class BroadcastRecord:
    path: Path
    data: Dict[str, Any]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9']+", normalize(text))


def iter_records(outputs_dir: Path) -> Iterable[BroadcastRecord]:
    for path in sorted(outputs_dir.glob('*.json')):
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        yield BroadcastRecord(path=path, data=data)


def text_blob(data: Dict[str, Any]) -> str:
    parts = [
        data.get('title', ''),
        data.get('tagline', ''),
        data.get('theme', ''),
        data.get('synopsis', ''),
        ' '.join(data.get('props', [])),
        ' '.join(item.get('entry', '') for item in data.get('contradiction_ledger', [])),
        ' '.join(beat.get('text', '') for beat in data.get('beat_sheet', [])),
        ' '.join(data.get('dialogue_samples', [])),
        ' '.join(data.get('scene_paragraphs', [])),
        data.get('fake_critic_blurb', ''),
        data.get('sequel_hook', ''),
        data.get('franchise_adjacency', ''),
    ]
    return ' '.join(p for p in parts if p)


def extract_towns(blob: str) -> List[str]:
    towns = []
    for town in ['blackthorn lake', 'bellweather', 'marigold falls', 'alder ridge', 'winter hollow']:
        if town in blob:
            towns.append(town)
    return towns


def title_family(title: str) -> str:
    words = tokenize(title)
    if not words:
        return 'unknown'
    if words[0] in {'the', 'a', 'her', 'he', 'what'} and len(words) > 1:
        return words[1]
    return words[0]


def extract_record(record: BroadcastRecord) -> Dict[str, Any]:
    data = record.data
    blob = normalize(text_blob(data))
    cast = data.get('cast', [])
    archetypes = [person.get('archetype', '') for person in cast if person.get('archetype')]
    spaces = [person.get('space_description', '') for person in cast if person.get('space_description')]
    props = data.get('props', [])
    contradiction_types = [item.get('type', '') for item in data.get('contradiction_ledger', [])]
    phrases = [phrase for phrase in DOCTRINE_PHRASES if phrase in blob]
    metrics = data.get('scores', {})
    return {
        'id': record.path.stem,
        'path': str(record.path),
        'title': data.get('title'),
        'title_family': title_family(data.get('title', '')),
        'mode': data.get('mode'),
        'theme': data.get('theme'),
        'tagline': data.get('tagline'),
        'omen': data.get('omen'),
        'relationship_dynamic': data.get('relationship_dynamic'),
        'props': props,
        'towns': extract_towns(blob),
        'archetypes': archetypes,
        'spaces': spaces,
        'contradiction_types': contradiction_types,
        'phrases': phrases,
        'scores': metrics,
        'llm_enabled': bool(data.get('llm_expansion', {}).get('enabled')),
        'text_blob': blob,
        'text_tokens': tokenize(blob),
    }


def classify_motif_tiers(summary: Dict[str, Any]) -> Dict[str, List[str]]:
    phrase_counts = dict(summary.get('phrase_counts', []))
    prop_counts = dict(summary.get('prop_counts', []))
    broadcast_count = max(int(summary.get('broadcast_count', 1)), 1)

    tier_0 = sorted([
        key for key, count in phrase_counts.items()
        if count >= int(0.95 * broadcast_count)
    ])
    tier_1 = sorted([
        key for key, count in prop_counts.items()
        if 0.35 * broadcast_count <= count < 0.95 * broadcast_count
    ])
    tier_2 = sorted([
        key for key, count in phrase_counts.items()
        if 0.08 * broadcast_count <= count < 0.35 * broadcast_count and key not in tier_0
    ])
    tier_3 = sorted([
        key for key, count in prop_counts.items()
        if count < 0.18 * broadcast_count
    ])
    return {
        'tier_0_foundational_texture': tier_0,
        'tier_1_identity_markers': tier_1,
        'tier_2_high_variance_mutations': tier_2,
        'tier_3_dead_sludge_candidates': tier_3,
    }


def write_editorial_report(index_dir: Path, summary: Dict[str, Any], records: List[Dict[str, Any]]) -> Path:
    tiers = classify_motif_tiers(summary)
    title_counts = summary.get('title_counts', [])[:7]
    phrase_counts = summary.get('phrase_counts', [])[:12]
    prop_counts = summary.get('prop_counts', [])[:10]
    cluster_sizes = {k: len(v) for k, v in summary.get('clusters', {}).items()}

    strongest = sorted(records, key=lambda r: (
        float(r.get('scores', {}).get('canon_drift', 0.0)),
        float(r.get('scores', {}).get('kitchen_lighting_truth_index', 0.0)),
        float(r.get('scores', {}).get('male_cardigan_threat_score', 0.0)),
    ), reverse=True)[:8]

    lines = [
        '# HallTime Editorial Report',
        '',
        f"Broadcast corpus size: {summary.get('broadcast_count', 0)}", 
        '',
        '## Canon Saturation',
        'The corpus is now large enough to distinguish climate from meaningful variation.',
        '',
        '### Tier 0 Foundational Texture',
    ]
    lines.extend(f'- {item}' for item in tiers['tier_0_foundational_texture'])
    lines.extend(['', '### Tier 1 Identity Markers'])
    lines.extend(f'- {item}' for item in tiers['tier_1_identity_markers'])
    lines.extend(['', '### Tier 2 High-Variance Mutations'])
    lines.extend(f'- {item}' for item in tiers['tier_2_high_variance_mutations'])
    lines.extend(['', '### Tier 3 Dead Sludge Candidates'])
    lines.extend(f'- {item}' for item in tiers['tier_3_dead_sludge_candidates'])
    lines.extend(['', '## Recurrence Pressure', '### Title Families'])
    lines.extend(f'- {title}: {count}' for title, count in title_counts)
    lines.extend(['', '### Props'])
    lines.extend(f'- {prop}: {count}' for prop, count in prop_counts)
    lines.extend(['', '### Phrases'])
    lines.extend(f'- {phrase}: {count}' for phrase, count in phrase_counts)
    lines.extend(['', '## Franchise Clusters'])
    lines.extend(f'- {cluster}: {count}' for cluster, count in sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True))
    lines.extend(['', '## Canon Candidates', 'These broadcasts currently look like strong survivors under synthetic taste pressure.'])
    for record in strongest:
        lines.append(
            f"- {record['title']} [{record['id']}]: canon_drift={record.get('scores', {}).get('canon_drift')}, "
            f"kitchen_scene_pressure={record.get('scores', {}).get('kitchen_lighting_truth_index')}, "
            f"cardigan_threat={record.get('scores', {}).get('male_cardigan_threat_score')}, "
            f"props={', '.join(record.get('props', []))}"
        )
    lines.extend([
        '',
        '## Editorial Reading',
        'HallTime is no longer short on ideas. It is now suffering from canon saturation in its most successful substrate motifs.',
        'That is not failure. That is the signal that the next generation pass should weight identity markers and high-variance mutations more heavily while treating foundational texture as background climate.',
    ])

    report_path = index_dir / 'editorial_report.md'
    report_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return report_path



def write_best_of_batch(index_dir: Path, records: List[Dict[str, Any]]) -> Path:
    strongest = sorted(records, key=lambda r: (
        float(r.get('scores', {}).get('canon_drift', 0.0)),
        float(r.get('scores', {}).get('kitchen_lighting_truth_index', 0.0)),
        float(r.get('scores', {}).get('male_cardigan_threat_score', 0.0)),
        float(r.get('scores', {}).get('commercial_break_violence_potential', 0.0)),
    ), reverse=True)[:12]
    lines = ['# HallTime Best Of Batch', '', 'These are current survivor candidates under synthetic taste pressure.', '']
    for record in strongest:
        lines.append(
            f"- {record['title']} [{record['id']}]: props={', '.join(record.get('props', []))}; "
            f"archetypes={', '.join(record.get('archetypes', [])[:6])}; "
            f"canon_drift={record.get('scores', {}).get('canon_drift')}; "
            f"kitchen_scene_pressure={record.get('scores', {}).get('kitchen_lighting_truth_index')}"
        )
    out = index_dir / 'best_of_batch.md'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return out


def write_failed_patterns(index_dir: Path, summary: Dict[str, Any]) -> Path:
    broadcast_count = max(int(summary.get('broadcast_count', 1)), 1)
    phrase_counts = dict(summary.get('phrase_counts', []))
    title_counts = dict(summary.get('title_counts', []))
    cluster_sizes = {k: len(v) for k, v in summary.get('clusters', {}).items()}
    lines = ['# HallTime Failed Patterns', '', 'These are not failures in a moral sense. They are oversaturated or low-signal recurrences.', '']
    lines.append('## Oversaturated Climate')
    for phrase, count in sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True):
        if count >= int(0.95 * broadcast_count):
            lines.append(f'- {phrase}: climate, not differentiator ({count}/{broadcast_count})')
    lines.append('')
    lines.append('## Title Overpressure')
    for title, count in sorted(title_counts.items(), key=lambda x: x[1], reverse=True):
        if count >= 0.13 * broadcast_count:
            lines.append(f'- {title}: currently over-represented ({count}/{broadcast_count})')
    lines.append('')
    lines.append('## Cluster Breadth Warnings')
    for cluster, count in sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True):
        if count >= int(0.8 * broadcast_count):
            lines.append(f'- {cluster}: too broad to function as a selective franchise cluster ({count}/{broadcast_count})')
    out = index_dir / 'failed_patterns.md'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return out


def write_canon_candidates(index_dir: Path, summary: Dict[str, Any], records: List[Dict[str, Any]]) -> Path:
    phrase_counts = dict(summary.get('phrase_counts', []))
    prop_counts = dict(summary.get('prop_counts', []))
    archetype_counts = dict(summary.get('archetype_counts', []))
    title_counts = dict(summary.get('title_counts', []))
    payload = {
        'foundational_texture': summary.get('motif_tiers', {}).get('tier_0_foundational_texture', []),
        'identity_markers': summary.get('motif_tiers', {}).get('tier_1_identity_markers', []),
        'high_variance_mutations': summary.get('motif_tiers', {}).get('tier_2_high_variance_mutations', []),
        'title_families_under_pressure': sorted(title_counts.items(), key=lambda x: x[1], reverse=True)[:7],
        'archetypes_by_survivability': sorted(archetype_counts.items(), key=lambda x: x[1], reverse=True),
        'props_by_symbolic_charge': sorted(prop_counts.items(), key=lambda x: x[1], reverse=True),
        'phrases_by_doctrinal_charge': sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True),
        'survivor_ids': [record['id'] for record in sorted(records, key=lambda r: float(r.get('scores', {}).get('male_cardigan_threat_score', 0.0)), reverse=True)[:20]],
    }
    out = index_dir / 'canon_candidates.json'
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    return out


def write_generation_feedback(index_dir: Path, summary: Dict[str, Any]) -> Path:
    tiers = summary.get('motif_tiers', {})
    title_counts = dict(summary.get('title_counts', []))
    archetype_counts = dict(summary.get('archetype_counts', []))
    feedback = {
        'demote_phrases': tiers.get('tier_0_foundational_texture', []),
        'promote_props': [item for item in tiers.get('tier_1_identity_markers', []) if item not in {'casserole dish', 'ceramic owl', 'unopened letter'}],
        'protect_phrases': tiers.get('tier_2_high_variance_mutations', []),
        'title_weights': {},
        'male_archetype_weights': {},
        'mode_weights': {
            'Court-Ordered Lifetime': 1.05,
            'Mother Was Right All Along': 1.08,
            'Divorce Gothic': 1.1,
            'Menace Christmas': 1.02,
            'Hallmark Possession Event': 0.98,
            'Lifetime Original': 1.0,
        },
        'theme_weights': {
            "Trust isn't given. It's rented.": 0.92,
            'A town never forgets. It just redecorates.': 1.05,
            'Some homes hold families. Some hold motive.': 1.08,
            'Silence is just fear wearing cashmere.': 1.12,
        },
    }
    max_title = max(title_counts.values()) if title_counts else 1
    for title, count in title_counts.items():
        feedback['title_weights'][title] = round(max(0.55, 1.15 - (count / max_title) * 0.45), 3)
    for archetype, count in archetype_counts.items():
        if archetype in {'decorative_husband', 'soft_spoken_menace', 'rugged_scamp', 'divorced_redemption_dad'}:
            feedback['male_archetype_weights'][archetype] = round(0.9 + (count / max(archetype_counts.values(), default=1)) * 0.3, 3)
    out = index_dir / 'generation_feedback.json'
    out.write_text(json.dumps(feedback, indent=2, ensure_ascii=False), encoding='utf-8')
    return out

def build_index(outputs_dir: Path, index_dir: Path) -> Dict[str, Any]:
    index_dir.mkdir(parents=True, exist_ok=True)
    records = [extract_record(record) for record in iter_records(outputs_dir)]
    token_df: Counter[str] = Counter()
    for record in records:
        token_df.update(set(record['text_tokens']))

    total_docs = max(len(records), 1)
    for record in records:
        tf = Counter(record['text_tokens'])
        max_tf = max(tf.values()) if tf else 1
        weights = {}
        for token, count in tf.items():
            idf = math.log((1 + total_docs) / (1 + token_df[token])) + 1.0
            weights[token] = round((count / max_tf) * idf, 6)
        record['tfidf'] = weights

    title_counts = Counter(record['title'] for record in records)
    family_counts = Counter(record['title_family'] for record in records)
    prop_counts = Counter(prop for record in records for prop in record['props'])
    archetype_counts = Counter(a for record in records for a in record['archetypes'])
    phrase_counts = Counter(p for record in records for p in record['phrases'])
    contradiction_counts = Counter(c for record in records for c in record['contradiction_types'])
    cluster_map = cluster_records(records)
    graph = build_concept_graph(records)

    with (index_dir / 'broadcasts.jsonl').open('w', encoding='utf-8') as handle:
        for record in records:
            slim = dict(record)
            slim.pop('text_tokens', None)
            handle.write(json.dumps(slim, ensure_ascii=False) + '\n')

    summary = {
        'broadcast_count': len(records),
        'title_counts': title_counts.most_common(),
        'title_family_counts': family_counts.most_common(),
        'prop_counts': prop_counts.most_common(),
        'archetype_counts': archetype_counts.most_common(),
        'phrase_counts': phrase_counts.most_common(),
        'contradiction_counts': contradiction_counts.most_common(),
        'clusters': cluster_map,
    }
    summary['motif_tiers'] = classify_motif_tiers(summary)
    (index_dir / 'summary.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    (index_dir / 'concept_graph.json').write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding='utf-8')
    write_editorial_report(index_dir, summary, records)
    write_best_of_batch(index_dir, records)
    write_failed_patterns(index_dir, summary)
    write_canon_candidates(index_dir, summary, records)
    write_generation_feedback(index_dir, summary)
    return summary


def cluster_records(records: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    clusters: Dict[str, List[str]] = defaultdict(list)
    for record in records:
        blob = record['text_blob']
        for cluster_name, keywords in CLUSTER_RULES.items():
            if any(keyword in blob for keyword in keywords):
                clusters[cluster_name].append(record['id'])
    return {name: ids for name, ids in clusters.items()}


def build_concept_graph(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    node_weights: Counter[Tuple[str, str]] = Counter()
    edge_weights: Counter[Tuple[str, str, str, str, str]] = Counter()
    for record in records:
        title_node = ('title', record['title'])
        node_weights[title_node] += 1
        for prop in record['props']:
            prop_node = ('prop', prop)
            node_weights[prop_node] += 1
            edge_weights[(title_node[0], title_node[1], 'appears_with', prop_node[0], prop_node[1])] += 1
        for archetype in record['archetypes']:
            a_node = ('archetype', archetype)
            node_weights[a_node] += 1
            edge_weights[(title_node[0], title_node[1], 'casts', a_node[0], a_node[1])] += 1
        for phrase in record['phrases']:
            p_node = ('phrase', phrase)
            node_weights[p_node] += 1
            edge_weights[(title_node[0], title_node[1], 'recurs_in', p_node[0], p_node[1])] += 1
        for town in record['towns']:
            t_node = ('town', town)
            node_weights[t_node] += 1
            edge_weights[(title_node[0], title_node[1], 'located_in', t_node[0], t_node[1])] += 1
    return {
        'nodes': [
            {'kind': kind, 'value': value, 'weight': weight}
            for (kind, value), weight in node_weights.most_common()
        ],
        'edges': [
            {
                'source_kind': sk,
                'source_value': sv,
                'relation': rel,
                'target_kind': tk,
                'target_value': tv,
                'weight': weight,
            }
            for (sk, sv, rel, tk, tv), weight in edge_weights.most_common()
        ],
    }



def resolve_lm_studio_url() -> str:
    direct = os.environ.get("LM_STUDIO_URL")
    if direct:
        return direct
    base = os.environ.get("LM_STUDIO_BASE_URL") or "http://127.0.0.1:1234/v1"
    return base.rstrip("/") + "/chat/completions"


def extract_chat_text(data: Dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError("No choices in editorial response")
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
    raise RuntimeError(f"Unrecognized editorial content payload: {content!r}")


def parse_editorial_json(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RuntimeError("No JSON object found in editorial response")
    return json.loads(text[start:end + 1])


def editorial_chat(prompt: str, model: str, url: str, timeout: int, max_tokens: int, temperature: float) -> str:
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are HallTime Movie Network's editorial board. "
                    "You are not generating broadcasts. You are deciding what deserves recurrence. "
                    "Return only valid JSON."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.environ.get('LM_STUDIO_API_KEY', 'lm-studio')}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    return extract_chat_text(json.loads(raw))


def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def get_record_map(records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {record['id']: record for record in records}


def sibling_query(record: Dict[str, Any]) -> str:
    parts = [record.get('title', ''), ' '.join(record.get('props', [])[:3]), ' '.join(record.get('phrases', [])[:5]), ' '.join(record.get('archetypes', [])[:6])]
    return ' '.join(p for p in parts if p)


def build_editorial_candidates(index_dir: Path, records: List[Dict[str, Any]], candidate_count: int, sibling_count: int) -> List[Dict[str, Any]]:
    candidates = load_json_file(index_dir / 'canon_candidates.json', {})
    ids = candidates.get('survivor_ids', [])[:candidate_count]
    record_map = get_record_map(records)
    selected = []
    for rid in ids:
        record = record_map.get(rid)
        if not record:
            continue
        siblings = search_records(records, sibling_query(record), sibling_count + 1, metric='canon_drift')
        siblings = [item for item in siblings if item['id'] != rid][:sibling_count]
        selected.append({
            'record': record,
            'siblings': siblings,
        })
    return selected


def build_editorial_prompt(summary: Dict[str, Any], candidates: List[Dict[str, Any]], feedback: Dict[str, Any]) -> str:
    lines = [
        'HallTime editorial mandate:',
        '- Distinguish climate from signal.',
        '- Protect rare high-voltage doctrine particles.',
        '- Prefer atmospheric persistence over logical coherence.',
        '- Recommend gentle weight updates, not total rewrites.',
        '',
        'Current motif tiers:',
        json.dumps(summary.get('motif_tiers', {}), ensure_ascii=False),
        '',
        'Current feedback weights:',
        json.dumps(feedback, ensure_ascii=False),
        '',
        'Candidate comparisons:',
    ]
    for idx, item in enumerate(candidates, start=1):
        record = item['record']
        lines.append(f"Candidate {idx}: {record['title']} [{record['id']}]")
        lines.append(f"  props={record.get('props', [])}")
        lines.append(f"  phrases={record.get('phrases', [])}")
        lines.append(f"  archetypes={record.get('archetypes', [])}")
        lines.append(f"  scores={record.get('scores', {})}")
        lines.append('  siblings:')
        for sib in item['siblings']:
            lines.append(f"    - {sib['title']} [{sib['id']}] props={sib.get('props', [])} phrases={sib.get('phrases', [])} scores={sib.get('scores', {})}")
    lines.extend([
        '',
        'Return valid JSON only. You MUST include every key below even if some values are empty.',
        'Do not return markdown fences. Do not omit empty arrays or empty objects.',
        'Multiplier semantics: values above 1.0 increase recurrence pressure, values below 1.0 decrease recurrence pressure.',
        'If you want to bump a title, theme, mode, or archetype, return a multiplier greater than 1.0.',
        'Required schema:',
        '{',
        '  "notes_markdown": "string",',
        '  "promote_props": [],',
        '  "demote_phrases": [],',
        '  "protect_phrases": [],',
        '  "title_weight_adjustments": {},',
        '  "theme_weight_adjustments": {},',
        '  "mode_weight_adjustments": {},',
        '  "male_archetype_weight_adjustments": {},',
        '  "canon_candidates": [],',
        '  "dead_sludge": []',
        '}',
    ])
    return "\n".join(lines)


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _clean_mapping_key(value: str) -> str:
    return str(value).strip().strip('"').strip("'")


def merge_feedback(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key in ['demote_phrases', 'promote_props', 'protect_phrases']:
        merged[key] = sorted(set(base.get(key, [])) | set(update.get(key, [])))
    for key, low, high in [
        ('title_weights', 0.45, 1.25),
        ('theme_weights', 0.75, 1.25),
        ('mode_weights', 0.85, 1.2),
        ('male_archetype_weights', 0.85, 1.25),
    ]:
        current = dict(base.get(key, {}))
        for item, factor in update.get(key.replace('_weights', '_weight_adjustments'), {}).items():
            clean_item = _clean_mapping_key(item)
            new_value = clamp(float(current.get(clean_item, 1.0)) * float(factor), low, high)
            current[clean_item] = round(new_value, 3)
        merged[key] = current
    return merged


def run_editorial_pass(index_dir: Path, model: str, url: str, timeout: int, max_tokens: int, temperature: float, candidate_count: int, sibling_count: int) -> Dict[str, Any]:
    records = load_index(index_dir)
    summary = load_json_file(index_dir / 'summary.json', {})
    feedback_path = index_dir / 'generation_feedback.json'
    feedback = load_json_file(feedback_path, {})
    candidates = build_editorial_candidates(index_dir, records, candidate_count, sibling_count)
    prompt = build_editorial_prompt(summary, candidates, feedback)

    editorial_dir = index_dir / 'editorial'
    editorial_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    prompt_path = editorial_dir / f'{stamp}-editorial-prompt.json'
    response_path = editorial_dir / f'{stamp}-editorial-response.txt'
    note_path = editorial_dir / f'{stamp}-editorial-notes.md'
    prompt_path.write_text(json.dumps({
        'model': model,
        'url': url,
        'timeout': timeout,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'prompt': prompt,
    }, indent=2, ensure_ascii=False), encoding='utf-8')

    raw = editorial_chat(prompt, model, url, timeout, max_tokens, temperature)
    response_path.write_text(raw, encoding='utf-8')
    parsed = parse_editorial_json(raw)
    note_path.write_text(parsed.get('notes_markdown', ''), encoding='utf-8')

    merged = merge_feedback(feedback, parsed)
    feedback_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding='utf-8')

    log_path = editorial_dir / 'editorial_notes.jsonl'
    with log_path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({
            'ts': datetime.now().isoformat(),
            'model': model,
            'prompt_path': str(prompt_path),
            'response_path': str(response_path),
            'note_path': str(note_path),
            'candidate_ids': [item['record']['id'] for item in candidates],
            'updates': parsed,
        }, ensure_ascii=False) + '\n')

    return {
        'prompt_path': str(prompt_path),
        'response_path': str(response_path),
        'note_path': str(note_path),
        'feedback_path': str(feedback_path),
        'candidate_count': len(candidates),
    }

def cosine_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    numerator = sum(a[t] * b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return numerator / (norm_a * norm_b)


def load_index(index_dir: Path) -> List[Dict[str, Any]]:
    path = index_dir / 'broadcasts.jsonl'
    if not path.exists():
        raise SystemExit('index missing; run index command first')
    records = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def search_records(records: List[Dict[str, Any]], query: str, limit: int, metric: str | None = None) -> List[Dict[str, Any]]:
    q_tokens = tokenize(query)
    q_tf = Counter(q_tokens)
    q_weights = {token: float(count) for token, count in q_tf.items()}
    scored = []
    for record in records:
        score = cosine_similarity(q_weights, record.get('tfidf', {}))
        if metric:
            score += 0.15 * float(record.get('scores', {}).get(metric, 0.0))
        scored.append((score, record))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [
        {
            'score': round(score, 4),
            'id': record['id'],
            'title': record['title'],
            'mode': record['mode'],
            'props': record['props'],
            'phrases': record['phrases'],
            'scores': record['scores'],
            'path': record['path'],
        }
        for score, record in scored[:limit]
    ]


def print_summary(summary: Dict[str, Any]) -> None:
    print(json.dumps({
        'broadcast_count': summary['broadcast_count'],
        'top_titles': summary['title_counts'][:5],
        'top_props': summary['prop_counts'][:5],
        'top_phrases': summary['phrase_counts'][:8],
        'clusters': {k: len(v) for k, v in summary['clusters'].items()},
        'motif_tiers': summary.get('motif_tiers', {}),
    }, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description='HallTime refinement and corpus tooling')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_index = sub.add_parser('index', help='Build searchable corpus index')
    p_index.add_argument('--outputs-dir', default=str(OUTPUTS_DIR))
    p_index.add_argument('--index-dir', default=str(INDEX_DIR))

    p_search = sub.add_parser('search', help='Search indexed corpus by atmospheric similarity')
    p_search.add_argument('query')
    p_search.add_argument('--index-dir', default=str(INDEX_DIR))
    p_search.add_argument('--limit', type=int, default=8)
    p_search.add_argument('--metric', default=None)

    p_editorial = sub.add_parser('editorial-pass', help='Run retrieval-backed LM Studio editorial criticism and update generation feedback')
    p_editorial.add_argument('--index-dir', default=str(INDEX_DIR))
    p_editorial.add_argument('--model', default=os.environ.get('CHAT_MODEL_ID') or 'openai/gpt-oss-20b')
    p_editorial.add_argument('--lm-studio-url', default=resolve_lm_studio_url())
    p_editorial.add_argument('--timeout', type=int, default=180)
    p_editorial.add_argument('--max-tokens', type=int, default=2600)
    p_editorial.add_argument('--temperature', type=float, default=0.9)
    p_editorial.add_argument('--candidate-count', type=int, default=5)
    p_editorial.add_argument('--sibling-count', type=int, default=4)

    args = parser.parse_args()
    if args.cmd == 'index':
        summary = build_index(Path(args.outputs_dir), Path(args.index_dir))
        print_summary(summary)
    elif args.cmd == 'search':
        records = load_index(Path(args.index_dir))
        results = search_records(records, args.query, args.limit, args.metric)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    elif args.cmd == 'editorial-pass':
        result = run_editorial_pass(
            Path(args.index_dir),
            args.model,
            args.lm_studio_url,
            args.timeout,
            args.max_tokens,
            args.temperature,
            args.candidate_count,
            args.sibling_count,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
