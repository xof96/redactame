"""Weekday-mapping data for train_synth.jsonl (v3.2 patch).

v3.1 still shifts the weekday when translating (input "el jueves" -> output "vendredi",
"Wednesday" -> "lunes"). The targets in our data are correctly mapped, so this is an exposure
problem: the model has not seen enough cross-lingual weekday pairs, and it had NEVER seen
Saturday/Sunday (the previous generators only used Monday-Friday).

This set drills the exact weekday mapping across all seven days and all language pairs, with the
weekday as the salient element and enough sentence-shape variety to avoid stiffening the model.

    .\.venv\Scripts\python.exe generate_dataset_weekdays.py --n 500 --start 2800
"""

import argparse
import json
import random
from pathlib import Path

OUT_FILE = Path(__file__).resolve().parent / "train_synth_weekdays.jsonl"

NAMES = [
    "Claire", "Thomas", "Sophie", "Julien", "Emily", "Michael", "Sarah", "James", "Daniel",
    "Valentina", "Ricardo", "Laura", "Carolina", "Andres", "Martin", "Juan", "Lucas", "Marie",
    "Paul", "Nicolas", "Elena", "Diego", "Paula", "Camila", "Claudio", "Claudia", "Matías",
    "Sebastián", "Ignacio", "Javiera", "Catalina", "Loïc", "Océane", "Mathieu", "Théo", "Adèle",
    "Rodrigo", "Fernanda", "Joaquín", "Cristóbal", "Xiomara", "Rémi", "Solène", "Anaïs",
]

# All seven days, including the weekend the earlier generators never covered.
DAYS = [
    {"es": "lunes", "fr": "lundi", "en": "Monday"},
    {"es": "martes", "fr": "mardi", "en": "Tuesday"},
    {"es": "miércoles", "fr": "mercredi", "en": "Wednesday"},
    {"es": "jueves", "fr": "jeudi", "en": "Thursday"},
    {"es": "viernes", "fr": "vendredi", "en": "Friday"},
    {"es": "sábado", "fr": "samedi", "en": "Saturday"},
    {"es": "domingo", "fr": "dimanche", "en": "Sunday"},
]

ITEMS = [
    {"es": "el informe", "fr": "le rapport", "en": "the report"},
    {"es": "el contrato", "fr": "le contrat", "en": "the contract"},
    {"es": "los documentos", "fr": "les documents", "en": "the documents"},
    {"es": "la propuesta", "fr": "la proposition", "en": "the proposal"},
]

PART = [
    {"es": "por la mañana", "fr": "dans la matinée", "en": "in the morning"},
    {"es": "por la tarde", "fr": "dans l'après-midi", "en": "in the afternoon"},
]

LANGS = ("es", "fr", "en")


def fr_day(num):
    return "1er" if num == 1 else str(num)


def dnum(lang, day, num):
    """Weekday, optionally followed by a day-of-month, with no article."""
    if num is None:
        return day[lang]
    if lang == "en":
        suf = {1: "st", 2: "nd", 3: "rd"}.get(num % 10, "th")
        if 11 <= num % 100 <= 13:
            suf = "th"
        return f"{day['en']} the {num}{suf}"
    if lang == "fr":
        return f"{day['fr']} {fr_day(num)}"
    return f"{day['es']} {num}"


def gin(lang, name, rng):
    g = {"es": ["hola", "oye", "buenas"], "fr": ["bonjour", "salut"], "en": ["hi", "hey"]}[lang]
    return f"{rng.choice(g)} {name}"


def gout(lang, name, rng):
    g = {"es": ["Hola", "Buenas", "Buenos días"], "fr": ["Bonjour"], "en": ["Hi", "Hello"]}[lang]
    return f"{rng.choice(g)} {name}"


# ---- weekday-centric scenarios ----------------------------------------------------------

def sc_confirm(rng):
    name, day, num = rng.choice(NAMES), rng.choice(DAYS), rng.randint(1, 28) if rng.random() < 0.4 else None
    inp = {
        "es": f"{gin('es', name, rng)} te confirmo que nos vemos el {dnum('es', day, num)}",
        "fr": f"{gin('fr', name, rng)} je te confirme qu'on se voit {dnum('fr', day, num)}",
        "en": f"{gin('en', name, rng)} just confirming we're meeting on {dnum('en', day, num)}",
    }
    out = {
        "es": f"{gout('es', name, rng)}, le confirmo que nos vemos el {dnum('es', day, num)}.",
        "fr": f"{gout('fr', name, rng)}, je vous confirme que nous nous voyons {dnum('fr', day, num)}.",
        "en": f"{gout('en', name, rng)}, I confirm we are meeting on {dnum('en', day, num)}.",
    }
    return inp, out


def sc_move(rng):
    name, d1, d2 = rng.choice(NAMES), rng.choice(DAYS), rng.choice(DAYS)
    inp = {
        "es": f"{gin('es', name, rng)} el {d1['es']} ya no puedo, lo movemos al {d2['es']}?",
        "fr": f"{gin('fr', name, rng)} {d1['fr']} je ne peux plus, on décale à {d2['fr']}?",
        "en": f"{gin('en', name, rng)} I can't do {d1['en']} anymore, can we move it to {d2['en']}?",
    }
    out = {
        "es": f"{gout('es', name, rng)}, el {d1['es']} ya no me es posible. ¿Podríamos moverlo al {d2['es']}?",
        "fr": f"{gout('fr', name, rng)}, {d1['fr']} ne m'est plus possible. Pourrions-nous le décaler à {d2['fr']}?",
        "en": f"{gout('en', name, rng)}, {d1['en']} is no longer possible for me. Could we move it to {d2['en']}?",
    }
    return inp, out


def sc_available(rng):
    name, day, part = rng.choice(NAMES), rng.choice(DAYS), rng.choice(PART)
    inp = {
        "es": f"{gin('es', name, rng)} el {day['es']} {part['es']} me viene bien si te sirve",
        "fr": f"{gin('fr', name, rng)} {day['fr']} {part['fr']} ça me va si ça te convient",
        "en": f"{gin('en', name, rng)} {day['en']} {part['en']} works for me if that suits you",
    }
    out = {
        "es": f"{gout('es', name, rng)}, el {day['es']} {part['es']} me viene bien, si le sirve.",
        "fr": f"{gout('fr', name, rng)}, {day['fr']} {part['fr']} me convient, si cela vous va.",
        "en": f"{gout('en', name, rng)}, {day['en']} {part['en']} works for me, if that suits you.",
    }
    return inp, out


def sc_deadline(rng):
    name, day, item = rng.choice(NAMES), rng.choice(DAYS), rng.choice(ITEMS)
    inp = {
        "es": f"{gin('es', name, rng)} necesito {item['es']} para el {day['es']} sin falta",
        "fr": f"{gin('fr', name, rng)} il me faut {item['fr']} pour {day['fr']} impérativement",
        "en": f"{gin('en', name, rng)} i need {item['en']} by {day['en']} without fail",
    }
    out = {
        "es": f"{gout('es', name, rng)}, necesito {item['es']} para el {day['es']} sin falta.",
        "fr": f"{gout('fr', name, rng)}, il me faut {item['fr']} pour {day['fr']} impérativement.",
        "en": f"{gout('en', name, rng)}, I need {item['en']} by {day['en']} without fail.",
    }
    return inp, out


def sc_next(rng):
    name, day = rng.choice(NAMES), rng.choice(DAYS)
    inp = {
        "es": f"{gin('es', name, rng)} hablamos el {day['es']} de la semana que viene?",
        "fr": f"{gin('fr', name, rng)} on se parle {day['fr']} prochain?",
        "en": f"{gin('en', name, rng)} shall we talk next {day['en']}?",
    }
    out = {
        "es": f"{gout('es', name, rng)}, ¿hablamos el {day['es']} de la semana que viene?",
        "fr": f"{gout('fr', name, rng)}, pourrions-nous nous parler {day['fr']} prochain?",
        "en": f"{gout('en', name, rng)}, could we talk next {day['en']}?",
    }
    return inp, out


def sc_seeyou(rng):
    name, day = rng.choice(NAMES), rng.choice(DAYS)
    inp = {
        "es": f"{gin('es', name, rng)} perfecto entonces nos vemos el {day['es']} gracias",
        "fr": f"{gin('fr', name, rng)} parfait alors on se voit {day['fr']} merci",
        "en": f"{gin('en', name, rng)} perfect so see you on {day['en']} thanks",
    }
    out = {
        "es": f"{gout('es', name, rng)}, perfecto. Nos vemos el {day['es']}. Gracias.",
        "fr": f"{gout('fr', name, rng)}, parfait. Nous nous voyons {day['fr']}. Merci.",
        "en": f"{gout('en', name, rng)}, perfect. See you on {day['en']}. Thank you.",
    }
    return inp, out


SCENARIOS = (
    [sc_confirm] * 3 + [sc_move] * 3 + [sc_available] * 2 +
    [sc_deadline] * 2 + [sc_next] * 2 + [sc_seeyou] * 2
)

# Weighted toward the translation directions where the shift showed up (es->fr, en->es, es->en,
# fr->es), while keeping same-language pairs so the mapping does not overfit to translation only.
PAIRS = (
    [("es", "fr")] * 6 + [("en", "es")] * 5 + [("es", "en")] * 4 + [("fr", "es")] * 4 +
    [("en", "fr")] * 3 + [("fr", "en")] * 3 +
    [("es", "es")] * 3 + [("fr", "fr")] * 2 + [("en", "en")] * 2
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=500)
    parser.add_argument("--seed", type=int, default=41)
    parser.add_argument("--start", type=int, default=2800)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    seen, rows, attempts = set(), [], 0
    while len(rows) < args.n and attempts < args.n * 80:
        attempts += 1
        inputs, outputs = rng.choice(SCENARIOS)(rng)
        source, target = rng.choice(PAIRS)
        inp, out = inputs[source].replace("..", "."), outputs[target].replace("..", ".")
        if (inp, out) in seen:
            continue
        seen.add((inp, out))
        rows.append({
            "id": f"syn-opus-4.8-{args.start + len(rows)}",
            "source": source,
            "target": target,
            "style": "professional",
            "input": inp,
            "output": out,
        })

    OUT_FILE.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    from collections import Counter
    print(f"wrote {len(rows)} examples to {OUT_FILE.name} (ids {args.start}..{args.start + len(rows) - 1})")
    print("pairs:", dict(Counter(f"{r['source']}->{r['target']}" for r in rows)))
    print("days :", dict(Counter(d[k] for r in rows for k in ('es',) for d in DAYS if d[k] in r['output'])))


if __name__ == "__main__":
    main()
