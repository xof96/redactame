"""Rebalancing data for train_synth.jsonl.

The v3 model started HALLUCINATING minutes (input "las tres" -> "15h30") because the previous
synthetic batch (opus) was almost all exact-minute times. This set counteracts that bias:

  - round hours, so the model learns "las tres" -> "à 15h" (no invented minutes)
  - vague times ("mañana por la mañana", "esta semana") kept vague, no clock invented
  - many messages with NO time / NO phone at all, so the model stops expecting them always
  - some day-of-week WITHOUT a number, to balance the "always day + number" bias

Same conventions as the other generators: shared canonical facts rendered as a messy spoken
INPUT and a clean professional OUTPUT, no AI tells, and no dangling closings.

    .\.venv\Scripts\python.exe generate_dataset_balance.py --n 800 --start 2000
"""

import argparse
import json
import random
from pathlib import Path

OUT_FILE = Path(__file__).resolve().parent / "train_synth_balance.jsonl"

NAMES = [
    # common pool (kept)
    "Claire", "Thomas", "Sophie", "Julien", "Amelie", "Emily", "Michael", "Sarah", "James",
    "Daniel", "Valentina", "Ricardo", "Laura", "Carolina", "Andres", "Martin", "Juan", "Emma",
    "Lucas", "Marie", "Paul", "Nicolas", "Elena", "Diego", "Paula", "Camila", "Antoine", "Chloe",
    "David", "Anna", "Pierre", "Sofia", "Hugo", "Clara", "Marc", "Ines", "Leo", "Julia",
    # Hispanic names, many accented (the model must copy the accent verbatim, not anglicize)
    "Claudio", "Claudia", "Matías", "Tomás", "Ignacio", "Javiera", "Rodrigo", "Fernanda",
    "Catalina", "Sebastián", "Josefa", "Benjamín", "Constanza", "Vicente", "Isidora", "Agustín",
    "Francisca", "Joaquín", "Antonia", "Felipe", "Bárbara", "Gonzalo", "Daniela", "Álvaro",
    "Macarena", "Cristián", "Cristóbal", "Nicolás", "Trinidad", "Renata", "Emilia", "Maite",
    "Xiomara", "Rocío", "Begoña", "Iñaki", "Nuria", "Jesús",
    # French names with diacritics (must keep the exact accent/diaeresis)
    "Mathieu", "Théo", "Océane", "Loïc", "Adèle", "Baptiste", "Margaux", "Guillaume", "Aurélie",
    "Rémi", "Solène", "Côme", "Anaïs", "Gaël", "Éloïse", "Zoé", "Hélène", "Maël", "Noémie",
]

DAYS = [
    {"es": "lunes", "fr": "lundi", "en": "Monday"},
    {"es": "martes", "fr": "mardi", "en": "Tuesday"},
    {"es": "miércoles", "fr": "mercredi", "en": "Wednesday"},
    {"es": "jueves", "fr": "jeudi", "en": "Thursday"},
    {"es": "viernes", "fr": "vendredi", "en": "Friday"},
]

ITEMS = [
    {"es": "la descripción del puesto", "fr": "la description du poste", "en": "the job description"},
    {"es": "el contrato", "fr": "le contrat", "en": "the contract"},
    {"es": "la factura del mes pasado", "fr": "la facture du mois dernier", "en": "last month's invoice"},
    {"es": "el informe", "fr": "le rapport", "en": "the report"},
]

VAGUE = [
    {"es": "mañana por la mañana", "fr": "demain matin", "en": "tomorrow morning"},
    {"es": "mañana por la tarde", "fr": "demain après-midi", "en": "tomorrow afternoon"},
    {"es": "esta semana", "fr": "cette semaine", "en": "this week"},
    {"es": "la semana que viene", "fr": "la semaine prochaine", "en": "next week"},
    {"es": "a principios de semana", "fr": "en début de semaine", "en": "early next week"},
    {"es": "cuando te venga bien", "fr": "à votre convenance", "en": "whenever it suits you"},
]

ROUND_HOURS = [8, 9, 10, 11, 12, 14, 15, 16, 17, 18]
LANGS = ("es", "fr", "en")


def fr_day(num):
    return "1er" if num == 1 else str(num)


def dp(lang, day, num):
    """Weekday, optionally + day-of-month, no article."""
    if num is None:
        return day[lang] if lang != "en" else day["en"]
    if lang == "en":
        suf = {1: "st", 2: "nd", 3: "rd"}.get(num % 10, "th")
        if 11 <= num % 100 <= 13:
            suf = "th"
        return f"{day['en']} the {num}{suf}"
    if lang == "fr":
        return f"{day['fr']} {fr_day(num)}"
    return f"{day['es']} {num}"


def r_in(lang, h, rng):
    h12 = h % 12 or 12
    if lang == "es":
        ampm = "de la mañana" if h < 12 else ("de la tarde" if h < 20 else "de la noche")
        return rng.choice([f"a las {h12} {ampm}", f"a eso de las {h12} {ampm}", f"sobre las {h12} {ampm}"])
    if lang == "fr":
        return rng.choice([f"à {h}h", f"vers {h}h"])
    ampm = "a.m." if h < 12 else "p.m."
    return rng.choice([f"at {h12} {ampm}", f"around {h12} {ampm}"])


def r_out(lang, h):
    if lang == "es":
        return f"a las {h}:00"
    if lang == "fr":
        return f"à {h}h"
    h12 = h % 12 or 12
    return f"at {h12} {'a.m.' if h < 12 else 'p.m.'}"


def r_bare(lang, h):
    if lang == "es":
        return f"las {h}:00"
    if lang == "fr":
        return f"{h}h"
    h12 = h % 12 or 12
    return f"{h12} {'a.m.' if h < 12 else 'p.m.'}"


def greet_in(lang, name, rng):
    return f"{rng.choice({'es': ['hola', 'oye', 'buenas'], 'fr': ['bonjour', 'salut'], 'en': ['hi', 'hey']}[lang])} {name}"


def greet_out(lang, name, rng):
    return f"{rng.choice({'es': ['Hola', 'Buenas', 'Buenos días'], 'fr': ['Bonjour'], 'en': ['Hi', 'Hello']}[lang])} {name}"


# Informal / regional greetings that must be normalized in the output while the NAME after them
# is preserved verbatim (the v3 model dropped the name or swapped it, e.g. "wena Claudio" -> "Clairet").
INFORMAL_GREET = {
    "es": ["wena", "wenas", "quiubo", "epa", "oe", "ey", "holi", "qué onda", "ola"],
    "fr": ["coucou", "salut", "hé", "yo", "cc"],
    "en": ["yo", "heya", "hiya", "sup", "hey there"],
}


def informal_in(lang, name, rng):
    return f"{rng.choice(INFORMAL_GREET[lang])} {name}"


def maybe_num(rng):
    return rng.randint(1, 28) if rng.random() < 0.5 else None


# ---- scenarios (round / vague / no-time) ------------------------------------------------

def sc_confirm_round(rng):
    name, day, num, h = rng.choice(NAMES), rng.choice(DAYS), maybe_num(rng), rng.choice(ROUND_HOURS)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} te confirmo la reunión del {dp('es', day, num)} {r_in('es', h, rng)}",
            "fr": f"{greet_in(L, name, rng)} je te confirme le rendez-vous du {dp('fr', day, num)} {r_in('fr', h, rng)}",
            "en": f"{greet_in(L, name, rng)} just confirming the meeting on {dp('en', day, num)} {r_in('en', h, rng)}",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, le confirmo la reunión del {dp('es', day, num)} {r_out('es', h)}.",
            "fr": f"{greet_out(L, name, rng)}, je vous confirme le rendez-vous du {dp('fr', day, num)} {r_out('fr', h)}.",
            "en": f"{greet_out(L, name, rng)}, I confirm the meeting on {dp('en', day, num)} {r_out('en', h)}.",
        }[L]
    return inp, out


def sc_before_after_round(rng):
    name, day, num, h = rng.choice(NAMES), rng.choice(DAYS), maybe_num(rng), rng.choice(ROUND_HOURS)
    ba = rng.choice(["before", "after"])
    w = {"before": {"es": "antes de", "fr": "avant", "en": "before"}, "after": {"es": "después de", "fr": "après", "en": "after"}}[ba]
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} el {dp('es', day, num)} solo puedo {w['es']} las {r_bare('es', h)[4:] if r_bare('es', h).startswith('las ') else r_bare('es', h)}",
            "fr": f"{greet_in(L, name, rng)} le {dp('fr', day, num)} je suis seulement dispo {w['fr']} {r_bare('fr', h)}",
            "en": f"{greet_in(L, name, rng)} on {dp('en', day, num)} i'm only free {w['en']} {r_bare('en', h)}",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, el {dp('es', day, num)} solo tengo disponibilidad {w['es']} {r_bare('es', h)}.",
            "fr": f"{greet_out(L, name, rng)}, le {dp('fr', day, num)} je ne suis disponible qu'{w['fr']} {r_bare('fr', h)}.",
            "en": f"{greet_out(L, name, rng)}, on {dp('en', day, num)} I am only available {w['en']} {r_bare('en', h)}.",
        }[L]
    return inp, out


def sc_vague(rng):
    name, v = rng.choice(NAMES), rng.choice(VAGUE)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} podríamos hablar {v['es']} si te parece",
            "fr": f"{greet_in(L, name, rng)} on pourrait se parler {v['fr']} si ça te va",
            "en": f"{greet_in(L, name, rng)} we could talk {v['en']} if that works",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, ¿podríamos hablar {v['es']}, si le parece?",
            "fr": f"{greet_out(L, name, rng)}, pourrions-nous nous parler {v['fr']}, si cela vous convient?",
            "en": f"{greet_out(L, name, rng)}, could we talk {v['en']}, if that works for you?",
        }[L]
    return inp, out


def sc_request_invoice(rng):
    name, item = rng.choice(NAMES), rng.choice(ITEMS)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} cuando puedas me mandas {item['es']}, sin apuro",
            "fr": f"{greet_in(L, name, rng)} quand tu peux tu m'envoies {item['fr']}, rien d'urgent",
            "en": f"{greet_in(L, name, rng)} whenever you can send me {item['en']}, no rush",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, cuando pueda, ¿me podría enviar {item['es']}? No hay prisa.",
            "fr": f"{greet_out(L, name, rng)}, quand vous pourrez, pourriez-vous m'envoyer {item['fr']}? Rien d'urgent.",
            "en": f"{greet_out(L, name, rng)}, whenever you can, could you send me {item['en']}? There is no rush.",
        }[L]
    return inp, out


def sc_interest_uncertain(rng):
    name = rng.choice(NAMES)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} gracias por escribirme la verdad la oportunidad me interesa pero antes de confirmar nada tengo que ver mi agenda",
            "fr": f"{greet_in(L, name, rng)} merci pour votre message franchement l'opportunité m'intéresse mais avant de confirmer je dois regarder mon agenda",
            "en": f"{greet_in(L, name, rng)} thanks for reaching out honestly the opportunity interests me but before confirming i need to check my schedule",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, gracias por escribirme. La oportunidad me interesa, pero antes de confirmar nada necesito revisar mi agenda.",
            "fr": f"{greet_out(L, name, rng)}, merci pour votre message. L'opportunité m'intéresse, mais avant de confirmer quoi que ce soit, je dois vérifier mon agenda.",
            "en": f"{greet_out(L, name, rng)}, thank you for reaching out. The opportunity interests me, but before confirming anything I need to check my schedule.",
        }[L]
    return inp, out


def sc_reject(rng):
    name = rng.choice(NAMES)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} gracias por pensar en mí pero por ahora prefiero quedarme en mi puesto actual igual agradezco el contacto",
            "fr": f"{greet_in(L, name, rng)} merci d'avoir pensé à moi mais pour l'instant je préfère rester à mon poste actuel merci quand même",
            "en": f"{greet_in(L, name, rng)} thanks for thinking of me but for now i'd rather stay in my current role i appreciate it though",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, gracias por pensar en mí. Por el momento prefiero quedarme en mi puesto actual. De todos modos le agradezco el contacto.",
            "fr": f"{greet_out(L, name, rng)}, merci d'avoir pensé à moi. Pour le moment, je préfère rester à mon poste actuel. Je vous remercie néanmoins de m'avoir contacté.",
            "en": f"{greet_out(L, name, rng)}, thank you for thinking of me. For now, I prefer to stay in my current role. I appreciate you reaching out all the same.",
        }[L]
    return inp, out


def sc_more_info(rng):
    name = rng.choice(NAMES)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} gracias por contactarme sí estoy abierto a escuchar y me gustaría saber más del proyecto y del equipo antes de organizar una llamada",
            "fr": f"{greet_in(L, name, rng)} merci de m'avoir contacté oui je suis ouvert et j'aimerais en savoir plus sur le projet et l'équipe avant d'organiser un appel",
            "en": f"{greet_in(L, name, rng)} thanks for reaching out yes i'm open and i'd like to know more about the project and the team before arranging a call",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, gracias por contactarme. Estoy abierto a escuchar y me gustaría saber más sobre el proyecto y el equipo antes de organizar una llamada.",
            "fr": f"{greet_out(L, name, rng)}, merci de m'avoir contacté. Je suis ouvert et j'aimerais en savoir plus sur le projet et l'équipe avant d'organiser un appel.",
            "en": f"{greet_out(L, name, rng)}, thank you for reaching out. I am open to it and I would like to know more about the project and the team before arranging a call.",
        }[L]
    return inp, out


def sc_day_only(rng):
    name, day = rng.choice(NAMES), rng.choice(DAYS)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} el {day['es']} me viene bien, sin hora fija todavía",
            "fr": f"{greet_in(L, name, rng)} le {day['fr']} ça me va, sans heure fixe pour l'instant",
            "en": f"{greet_in(L, name, rng)} {day['en']} works for me, no fixed time yet",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, el {day['es']} me viene bien. Todavía sin una hora fija.",
            "fr": f"{greet_out(L, name, rng)}, le {day['fr']} me convient. Sans heure fixe pour le moment.",
            "en": f"{greet_out(L, name, rng)}, {day['en']} works for me. No fixed time yet.",
        }[L]
    return inp, out


def sc_informal_greeting(rng):
    """Informal/regional greeting + name. Output normalizes the greeting and keeps the name verbatim."""
    name, day = rng.choice(NAMES), rng.choice(DAYS)
    body = rng.choice(["confirm", "thanks", "resend"])
    item = rng.choice(ITEMS)
    inp, out = {}, {}
    for L in LANGS:
        ig = informal_in(L, name, rng)
        gout = greet_out(L, name, rng)
        if body == "confirm":
            inp[L] = {
                "es": f"{ig}, te confirmo que seguimos con la reunión del {day['es']}",
                "fr": f"{ig}, je te confirme qu'on maintient le rendez-vous de {day['fr']}",
                "en": f"{ig}, just confirming we're still on for the meeting on {day['en']}",
            }[L]
            out[L] = {
                "es": f"{gout}, le confirmo que seguimos con la reunión del {day['es']}.",
                "fr": f"{gout}, je vous confirme que nous maintenons le rendez-vous de {day['fr']}.",
                "en": f"{gout}, I confirm we are still on for the meeting on {day['en']}.",
            }[L]
        elif body == "thanks":
            inp[L] = {
                "es": f"{ig}, gracias por el envío, todo llegó bien",
                "fr": f"{ig}, merci pour l'envoi, tout est bien arrivé",
                "en": f"{ig}, thanks for the delivery, everything arrived fine",
            }[L]
            out[L] = {
                "es": f"{gout}, gracias por el envío. Todo llegó bien.",
                "fr": f"{gout}, merci pour l'envoi. Tout est bien arrivé.",
                "en": f"{gout}, thank you for the delivery. Everything arrived fine.",
            }[L]
        else:
            inp[L] = {
                "es": f"{ig}, cuando puedas me reenvías {item['es']}",
                "fr": f"{ig}, quand tu peux tu me renvoies {item['fr']}",
                "en": f"{ig}, when you can could you resend {item['en']}",
            }[L]
            out[L] = {
                "es": f"{gout}, cuando pueda, ¿me podría reenviar {item['es']}?",
                "fr": f"{gout}, quand vous pourrez, pourriez-vous me renvoyer {item['fr']}?",
                "en": f"{gout}, whenever you can, could you resend {item['en']}?",
            }[L]
    return inp, out


SCENARIOS = (
    [sc_confirm_round] * 4 + [sc_before_after_round] * 3 + [sc_vague] * 3 + [sc_day_only] * 2 +
    [sc_request_invoice] * 3 + [sc_interest_uncertain] * 3 + [sc_reject] * 2 + [sc_more_info] * 2 +
    [sc_informal_greeting] * 6
)

PAIRS = (
    [("es", "fr")] * 6 + [("es", "en")] * 5 + [("es", "es")] * 5 +
    [("en", "es")] * 2 + [("en", "fr")] * 2 + [("en", "en")] * 2 +
    [("fr", "es")] * 2 + [("fr", "en")] * 1 + [("fr", "fr")] * 1
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=800)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("--start", type=int, default=2000, help="first id number: syn-opus-4.8-<start>")
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


if __name__ == "__main__":
    main()
