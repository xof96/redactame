"""Generate a synthetic training set focused on the exact failure modes we measured.

The fine-tuned model still corrupted hard facts. This generator drills them on purpose:

  - exact minutes (3:29, 8:45, 10:15), not only o'clock and half past
  - weekday + day-of-month together ("miércoles 4", "le mardi 12", "Wednesday the 4th")
  - phone numbers preserved verbatim (the model tended to drop them)
  - before / after / range nuance ("antes de las 3", "avant midi", "entre las 9 y las 11")
  - roles kept straight (the OTHER person sends, the sender reviews)

Every example shares one canonical set of facts, rendered as a messy spoken INPUT (source
language) and a clean professional OUTPUT (target language), so the gold preserves the facts by
construction. No AI tells (no em dashes, no stray ; or :), and deliberately NO dangling closings
like "Best regards," with no name, to counter the artifact the last fine-tune learned.

    .\.venv\Scripts\python.exe generate_dataset_opus.py --n 1000
"""

import argparse
import json
import random
from pathlib import Path

OUT_FILE = Path(__file__).resolve().parent / "train_synth_opus.jsonl"

NAMES = [
    "Claire", "Thomas", "Sophie", "Julien", "Amelie", "Emily", "Michael", "Sarah", "James",
    "Daniel", "Valentina", "Ricardo", "Laura", "Carolina", "Andres", "Martin", "Juan", "Emma",
    "Lucas", "Marie", "Paul", "Nicolas", "Elena", "Diego", "Paula", "Camila", "Antoine", "Chloe",
    "David", "Anna", "Pierre", "Sofia", "Hugo", "Clara", "Marc", "Ines", "Leo", "Julia", "Manon",
    "Kevin", "Lucia", "Bruno", "Nadia", "Oscar", "Adele", "Simon", "Rocio", "Louis", "Miguel",
]

DAYS = [
    {"es": "lunes", "fr": "lundi", "en": "Monday"},
    {"es": "martes", "fr": "mardi", "en": "Tuesday"},
    {"es": "miércoles", "fr": "mercredi", "en": "Wednesday"},
    {"es": "jueves", "fr": "jeudi", "en": "Thursday"},
    {"es": "viernes", "fr": "vendredi", "en": "Friday"},
]

MONTHS = [
    {"es": "enero", "fr": "janvier", "en": "January"},
    {"es": "febrero", "fr": "février", "en": "February"},
    {"es": "marzo", "fr": "mars", "en": "March"},
    {"es": "abril", "fr": "avril", "en": "April"},
    {"es": "mayo", "fr": "mai", "en": "May"},
    {"es": "junio", "fr": "juin", "en": "June"},
    {"es": "septiembre", "fr": "septembre", "en": "September"},
    {"es": "octubre", "fr": "octobre", "en": "October"},
    {"es": "noviembre", "fr": "novembre", "en": "November"},
]

ITEMS = [
    {"es": "la descripción del puesto", "fr": "la description du poste", "en": "the job description"},
    {"es": "el contrato", "fr": "le contrat", "en": "the contract"},
    {"es": "la factura", "fr": "la facture", "en": "the invoice"},
    {"es": "el informe", "fr": "le rapport", "en": "the report"},
]

MEDIA = ["Teams", "Zoom", "Google Meet"]


# ---- fact renderers ---------------------------------------------------------------------

def ordinal(n: int) -> str:
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def rand_minute(rng: random.Random) -> int:
    # Bias toward non-round minutes, which is exactly what the model normalized away.
    if rng.random() < 0.75:
        return rng.choice([5, 7, 10, 13, 15, 20, 22, 25, 29, 35, 40, 42, 45, 48, 50, 55])
    return rng.choice([0, 30])


def time_input(lang: str, h: int, m: int, rng: random.Random) -> str:
    """Messy, speech-like time in the source language."""
    h12 = h % 12 or 12
    if lang == "es":
        ampm = "de la mañana" if h < 12 else ("de la tarde" if h < 20 else "de la noche")
        forms = [f"las {h12} {m:02d} {ampm}", f"las {h12} y {m} {ampm}", f"las {h}:{m:02d}"]
        if m == 0:
            forms.append(f"las {h12} {ampm}")
        if m == 15:
            forms.append(f"las {h12} y cuarto {ampm}")
        if m == 30:
            forms.append(f"las {h12} y media {ampm}")
        return "a " + rng.choice(forms)
    if lang == "fr":
        return "à " + rng.choice([f"{h}h{m:02d}", f"{h} heures {m:02d}"])
    ampm = "a.m." if h < 12 else "p.m."
    return "at " + rng.choice([f"{h12}:{m:02d} {ampm}", f"{h}:{m:02d}", f"{h12} {m:02d} {ampm}"])


def time_output(lang: str, h: int, m: int) -> str:
    """Clean, professional time in the target language. Preserves the exact minute."""
    h12 = h % 12 or 12
    if lang == "es":
        return f"a las {h}:{m:02d}"
    if lang == "fr":
        return f"à {h}h{m:02d}"
    ampm = "a.m." if h < 12 else "p.m."
    return f"at {h12}:{m:02d} {ampm}"


def time_bare(lang: str, h: int, m: int) -> str:
    """Time without the leading preposition, for 'before/after/from-to' phrases."""
    if lang == "es":
        return f"{h}:{m:02d}"
    if lang == "fr":
        return f"{h}h{m:02d}"
    h12 = h % 12 or 12
    ampm = "a.m." if h < 12 else "p.m."
    return f"{h12}:{m:02d} {ampm}"


def fr_day(num: int) -> str:
    return "1er" if num == 1 else str(num)


def wd(lang: str, day: dict, num: int) -> str:
    """Weekday + day-of-month, no article. Add the preposition in the template."""
    if lang == "en":
        return f"{day['en']} the {ordinal(num)}"
    if lang == "fr":
        return f"{day['fr']} {fr_day(num)}"
    return f"{day['es']} {num}"


def date_md(lang: str, num: int, month: dict) -> str:
    if lang == "es":
        return f"el {num} de {month['es']}"
    if lang == "fr":
        return f"le {fr_day(num)} {month['fr']}"
    return f"{month['en']} {ordinal(num)}"


def gen_phone(rng: random.Random) -> str:
    def d(n: int) -> str:
        return "".join(str(rng.randint(0, 9)) for _ in range(n))
    style = rng.randint(0, 4)
    if style == 0:
        return f"6{d(2)} {d(3)} {d(3)}"
    if style == 1:
        return f"+34 6{d(2)} {d(3)} {d(3)}"
    if style == 2:
        return f"0{rng.randint(1, 7)} {d(2)} {d(2)} {d(2)} {d(2)}"
    if style == 3:
        return f"+56 9 {d(4)} {d(4)}"
    return f"+33 6 {d(2)} {d(2)} {d(2)} {d(2)}"


def gen_amount(rng: random.Random) -> str:
    return f"{rng.choice([180, 320, 480, 750, 990, 1200, 1450, 1500, 1750, 2300, 3450])} euros"


def gen_ref(rng: random.Random) -> str:
    letters = "".join(rng.choice("ABCDEFGHJKLMNPRSTUVWXYZ") for _ in range(2))
    return rng.choice([f"{letters}{rng.randint(1000, 9999)}", f"REF-{rng.randint(10000, 99999)}"])


def greet_in(lang: str, name: str, rng: random.Random) -> str:
    return f"{rng.choice({'es': ['hola', 'oye', 'buenas'], 'fr': ['bonjour', 'salut'], 'en': ['hi', 'hey']}[lang])} {name}"


def greet_out(lang: str, name: str, rng: random.Random) -> str:
    return f"{rng.choice({'es': ['Hola', 'Buenas', 'Buenos días'], 'fr': ['Bonjour'], 'en': ['Hi', 'Hello']}[lang])} {name}"


# ---- scenarios --------------------------------------------------------------------------
# Each returns inputs/outputs per language sharing the same canonical facts.
LANGS = ("es", "fr", "en")


def sc_confirm_meeting(rng):
    name = rng.choice(NAMES)
    day = rng.choice(DAYS)
    num = rng.randint(1, 28)
    h, m = rng.choice(range(8, 20)), rand_minute(rng)
    extra = rng.choice(["phone", "medium", "none"])
    phone = gen_phone(rng)
    medium = rng.choice(MEDIA)
    inp, out = {}, {}
    for L in LANGS:
        g_in, g_out = greet_in(L, name, rng), greet_out(L, name, rng)
        base_in = {
            "es": f"{g_in} te confirmo la reunión del {wd('es', day, num)} {time_input('es', h, m, rng)}",
            "fr": f"{g_in} je te confirme le rendez-vous du {wd('fr', day, num)} {time_input('fr', h, m, rng)}",
            "en": f"{g_in} just confirming the meeting on {wd('en', day, num)} {time_input('en', h, m, rng)}",
        }[L]
        base_out = {
            "es": f"{g_out}, le confirmo la reunión del {wd('es', day, num)} {time_output('es', h, m)}",
            "fr": f"{g_out}, je vous confirme le rendez-vous du {wd('fr', day, num)} {time_output('fr', h, m)}",
            "en": f"{g_out}, I confirm the meeting on {wd('en', day, num)} {time_output('en', h, m)}",
        }[L]
        if extra == "phone":
            base_in += {"es": f" y si hay algo me llamas al {phone}", "fr": f" et s'il y a quoi que ce soit tu m'appelles au {phone}", "en": f" and if anything comes up you can call me at {phone}"}[L]
            base_out += {"es": f". Si necesita algo, puede llamarme al {phone}.", "fr": f". En cas de besoin, vous pouvez m'appeler au {phone}.", "en": f". If you need anything, you can reach me at {phone}."}[L]
        elif extra == "medium":
            base_in += {"es": f" si quieres lo hacemos por {medium}", "fr": f" si tu veux on le fait par {medium}", "en": f" if you want we can do it over {medium}"}[L]
            base_out += {"es": f". Si le parece, lo hacemos por {medium}.", "fr": f". Si vous le souhaitez, nous pouvons le faire par {medium}.", "en": f". If you like, we can do it over {medium}."}[L]
        else:
            base_out += "."
        inp[L], out[L] = base_in, base_out
    return inp, out


def sc_reschedule(rng):
    name = rng.choice(NAMES)
    d1, d2 = rng.sample(DAYS, 2)
    n1, n2 = rng.randint(1, 28), rng.randint(1, 28)
    h1, m1 = rng.choice(range(8, 19)), rand_minute(rng)
    h2, m2 = rng.choice(range(8, 19)), rand_minute(rng)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} al final el {wd('es', d1, n1)} {time_input('es', h1, m1, rng)} no voy a poder, lo pasamos al {wd('es', d2, n2)} {time_input('es', h2, m2, rng)}?",
            "fr": f"{greet_in(L, name, rng)} finalement le {wd('fr', d1, n1)} {time_input('fr', h1, m1, rng)} je ne pourrai pas, on décale au {wd('fr', d2, n2)} {time_input('fr', h2, m2, rng)}?",
            "en": f"{greet_in(L, name, rng)} {wd('en', d1, n1)} {time_input('en', h1, m1, rng)} won't work after all, can we move it to {wd('en', d2, n2)} {time_input('en', h2, m2, rng)}?",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, al final el {wd('es', d1, n1)} {time_output('es', h1, m1)} no me será posible. ¿Podríamos pasarlo al {wd('es', d2, n2)} {time_output('es', h2, m2)}?",
            "fr": f"{greet_out(L, name, rng)}, finalement le {wd('fr', d1, n1)} {time_output('fr', h1, m1)} ne sera pas possible. Pourrions-nous le décaler au {wd('fr', d2, n2)} {time_output('fr', h2, m2)}?",
            "en": f"{greet_out(L, name, rng)}, {wd('en', d1, n1)} {time_output('en', h1, m1)} will not work after all. Could we move it to {wd('en', d2, n2)} {time_output('en', h2, m2)}?",
        }[L]
    return inp, out


def sc_before_after(rng):
    name = rng.choice(NAMES)
    day = rng.choice(DAYS)
    num = rng.randint(1, 28)
    h, m = rng.choice(range(9, 19)), rand_minute(rng)
    ba = rng.choice(["before", "after"])
    inp, out = {}, {}
    ba_word = {"before": {"es": "antes de", "fr": "avant", "en": "before"}, "after": {"es": "después de", "fr": "après", "en": "after"}}[ba]
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} el {wd('es', day, num)} solo puedo {ba_word['es']} las {time_bare('es', h, m)}",
            "fr": f"{greet_in(L, name, rng)} le {wd('fr', day, num)} je suis seulement disponible {ba_word['fr']} {time_bare('fr', h, m)}",
            "en": f"{greet_in(L, name, rng)} on {wd('en', day, num)} i'm only free {ba_word['en']} {time_bare('en', h, m)}",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, el {wd('es', day, num)} solo tengo disponibilidad {ba_word['es']} las {time_bare('es', h, m)}.",
            "fr": f"{greet_out(L, name, rng)}, le {wd('fr', day, num)} je ne suis disponible que {ba_word['fr']} {time_bare('fr', h, m)}.",
            "en": f"{greet_out(L, name, rng)}, on {wd('en', day, num)} I am only available {ba_word['en']} {time_bare('en', h, m)}.",
        }[L]
    return inp, out


def sc_range(rng):
    name = rng.choice(NAMES)
    day = rng.choice(DAYS)
    num = rng.randint(1, 28)
    h1 = rng.choice(range(8, 15))
    h2 = h1 + rng.randint(1, 4)
    m1, m2 = rand_minute(rng), rand_minute(rng)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} el {wd('es', day, num)} me sirve entre las {time_bare('es', h1, m1)} y las {time_bare('es', h2, m2)}",
            "fr": f"{greet_in(L, name, rng)} le {wd('fr', day, num)} ça me va entre {time_bare('fr', h1, m1)} et {time_bare('fr', h2, m2)}",
            "en": f"{greet_in(L, name, rng)} on {wd('en', day, num)} i'm good between {time_bare('en', h1, m1)} and {time_bare('en', h2, m2)}",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, el {wd('es', day, num)} tengo disponibilidad entre las {time_bare('es', h1, m1)} y las {time_bare('es', h2, m2)}.",
            "fr": f"{greet_out(L, name, rng)}, le {wd('fr', day, num)} je suis disponible entre {time_bare('fr', h1, m1)} et {time_bare('fr', h2, m2)}.",
            "en": f"{greet_out(L, name, rng)}, on {wd('en', day, num)} I am available between {time_bare('en', h1, m1)} and {time_bare('en', h2, m2)}.",
        }[L]
    return inp, out


def sc_payment(rng):
    name = rng.choice(NAMES)
    amount = gen_amount(rng)
    num = rng.randint(1, 28)
    month = rng.choice(MONTHS)
    ref = gen_ref(rng)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} te confirmo que el pago de {amount} lo hice {date_md('es', num, month)}, referencia {ref}",
            "fr": f"{greet_in(L, name, rng)} je te confirme que le paiement de {amount} a été fait {date_md('fr', num, month)}, référence {ref}",
            "en": f"{greet_in(L, name, rng)} confirming the payment of {amount} was made on {date_md('en', num, month)}, reference {ref}",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, le confirmo que el pago de {amount} se realizó {date_md('es', num, month)}, con la referencia {ref}.",
            "fr": f"{greet_out(L, name, rng)}, je vous confirme que le paiement de {amount} a été effectué {date_md('fr', num, month)}, avec la référence {ref}.",
            "en": f"{greet_out(L, name, rng)}, I confirm that the payment of {amount} was made on {date_md('en', num, month)}, with reference {ref}.",
        }[L]
    return inp, out


def sc_call_me(rng):
    name = rng.choice(NAMES)
    phone = gen_phone(rng)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} cualquier cosa llámame al {phone}, ahí estoy disponible toda la tarde",
            "fr": f"{greet_in(L, name, rng)} au besoin appelle moi au {phone}, je suis dispo tout l'après-midi",
            "en": f"{greet_in(L, name, rng)} if anything just call me at {phone}, i'm around all afternoon",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, si necesita algo puede llamarme al {phone}. Estaré disponible toda la tarde.",
            "fr": f"{greet_out(L, name, rng)}, en cas de besoin vous pouvez m'appeler au {phone}. Je serai disponible tout l'après-midi.",
            "en": f"{greet_out(L, name, rng)}, if you need anything you can call me at {phone}. I will be available all afternoon.",
        }[L]
    return inp, out


def sc_delivery(rng):
    name = rng.choice(NAMES)
    units = rng.choice([100, 150, 200, 250, 500, 750, 1000, 1200])
    d1, d2 = rng.sample(DAYS, 2)
    n1, n2 = rng.randint(1, 14), rng.randint(15, 28)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} podemos mover la entrega de las {units} unidades del {wd('es', d1, n1)} al {wd('es', d2, n2)}?",
            "fr": f"{greet_in(L, name, rng)} est-ce qu'on peut décaler la livraison des {units} unités du {wd('fr', d1, n1)} au {wd('fr', d2, n2)}?",
            "en": f"{greet_in(L, name, rng)} can we push the delivery of the {units} units from {wd('en', d1, n1)} to {wd('en', d2, n2)}?",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, ¿podríamos mover la entrega de las {units} unidades del {wd('es', d1, n1)} al {wd('es', d2, n2)}?",
            "fr": f"{greet_out(L, name, rng)}, pourrions-nous décaler la livraison des {units} unités du {wd('fr', d1, n1)} au {wd('fr', d2, n2)}?",
            "en": f"{greet_out(L, name, rng)}, could we push the delivery of the {units} units from {wd('en', d1, n1)} to {wd('en', d2, n2)}?",
        }[L]
    return inp, out


def sc_arrival(rng):
    name = rng.choice(NAMES)
    h1, m1 = rng.choice(range(8, 19)), rand_minute(rng)
    h2, m2 = h1, min(m1 + rng.choice([15, 20, 30, 40]), 59)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} al final no llego {time_input('es', h1, m1, rng)}, llego {time_input('es', h2, m2, rng)}, perdón",
            "fr": f"{greet_in(L, name, rng)} finalement je n'arrive pas {time_input('fr', h1, m1, rng)}, j'arrive plutôt {time_input('fr', h2, m2, rng)}, désolé",
            "en": f"{greet_in(L, name, rng)} i can't make it {time_input('en', h1, m1, rng)} after all, i'll be there {time_input('en', h2, m2, rng)}, sorry",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, al final no alcanzo a llegar {time_output('es', h1, m1)}. Llegaré {time_output('es', h2, m2)}. Perdón.",
            "fr": f"{greet_out(L, name, rng)}, finalement je n'arriverai pas {time_output('fr', h1, m1)}. J'arriverai {time_output('fr', h2, m2)}. Désolé.",
            "en": f"{greet_out(L, name, rng)}, I will not make it {time_output('en', h1, m1)} after all. I will be there {time_output('en', h2, m2)}. Sorry.",
        }[L]
    return inp, out


def sc_contract_dates(rng):
    name = rng.choice(NAMES)
    month = rng.choice(MONTHS)
    a = rng.randint(1, 14)
    b = a + rng.randint(3, 12)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} en el contrato aparece {date_md('es', a, month)} pero habíamos hablado {date_md('es', b, month)}, cuál es la correcta?",
            "fr": f"{greet_in(L, name, rng)} sur le contrat il y a {date_md('fr', a, month)} mais on avait parlé {date_md('fr', b, month)}, laquelle est la bonne?",
            "en": f"{greet_in(L, name, rng)} the contract shows {date_md('en', a, month)} but we had talked about {date_md('en', b, month)}, which one is right?",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, en el contrato aparece {date_md('es', a, month)}, pero habíamos hablado {date_md('es', b, month)}. ¿Me confirma cuál es la correcta?",
            "fr": f"{greet_out(L, name, rng)}, le contrat indique {date_md('fr', a, month)}, alors que nous avions parlé {date_md('fr', b, month)}. Pourriez-vous me confirmer laquelle est la bonne?",
            "en": f"{greet_out(L, name, rng)}, the contract shows {date_md('en', a, month)}, but we had talked about {date_md('en', b, month)}. Could you confirm which one is correct?",
        }[L]
    return inp, out


def sc_send_and_review(rng):
    name = rng.choice(NAMES)
    item = rng.choice(ITEMS)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} si puede mándeme {item['es']} y yo la reviso durante el día y le comento",
            "fr": f"{greet_in(L, name, rng)} si possible envoyez moi {item['fr']} et je le regarde dans la journée et je vous dis",
            "en": f"{greet_in(L, name, rng)} if you can send me {item['en']} and i'll review it during the day and get back to you",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, si le parece, envíeme {item['es']} y la reviso durante el día y le comento.",
            "fr": f"{greet_out(L, name, rng)}, si possible, envoyez-moi {item['fr']} et je le regarde dans la journée et je reviens vers vous.",
            "en": f"{greet_out(L, name, rng)}, if you can, please send me {item['en']} and I will review it during the day and get back to you.",
        }[L]
    return inp, out


def sc_meeting_link(rng):
    name = rng.choice(NAMES)
    day = rng.choice(DAYS)
    num = rng.randint(1, 28)
    h, m = rng.choice(range(8, 19)), rand_minute(rng)
    inp, out = {}, {}
    for L in LANGS:
        inp[L] = {
            "es": f"{greet_in(L, name, rng)} todavía no me llegó el enlace de la reunión del {wd('es', day, num)} {time_input('es', h, m, rng)}, me lo reenvías?",
            "fr": f"{greet_in(L, name, rng)} je n'ai toujours pas reçu le lien de la réunion du {wd('fr', day, num)} {time_input('fr', h, m, rng)}, tu peux me le renvoyer?",
            "en": f"{greet_in(L, name, rng)} i still haven't got the link for the {wd('en', day, num)} meeting {time_input('en', h, m, rng)}, can you resend it?",
        }[L]
        out[L] = {
            "es": f"{greet_out(L, name, rng)}, todavía no me ha llegado el enlace de la reunión del {wd('es', day, num)} {time_output('es', h, m)}. ¿Podría reenviármelo?",
            "fr": f"{greet_out(L, name, rng)}, je n'ai toujours pas reçu le lien de la réunion du {wd('fr', day, num)} {time_output('fr', h, m)}. Pourriez-vous me le renvoyer?",
            "en": f"{greet_out(L, name, rng)}, I still haven't received the link for the meeting on {wd('en', day, num)} {time_output('en', h, m)}. Could you resend it?",
        }[L]
    return inp, out


# Weighted so the time / phone / weekday+daynum heavy scenarios dominate.
PRO_SCENARIOS = (
    [sc_confirm_meeting] * 5 + [sc_reschedule] * 4 + [sc_before_after] * 3 + [sc_range] * 2 +
    [sc_call_me] * 3 + [sc_arrival] * 3 + [sc_meeting_link] * 2 + [sc_payment] * 3 +
    [sc_delivery] * 2 + [sc_contract_dates] * 2 + [sc_send_and_review] * 2
)

PRO_PAIRS = (
    [("es", "fr")] * 6 + [("es", "en")] * 5 + [("es", "es")] * 4 +
    [("en", "es")] * 2 + [("en", "fr")] * 2 + [("en", "en")] * 2 +
    [("fr", "es")] * 2 + [("fr", "en")] * 1 + [("fr", "fr")] * 1
)


def cg_example(rng):
    """correct_grammar: same language, minimal fixes, keeps the hard facts."""
    name = rng.choice(NAMES)
    day = rng.choice(DAYS)
    num = rng.randint(1, 28)
    h, m = rng.choice(range(8, 19)), rand_minute(rng)
    phone = gen_phone(rng)
    es = [
        (f"oye {name} te confirmo el {day['es']} {num} {time_input('es', h, m, rng)} si algo llamame al {phone}",
         f"Oye {name}, te confirmo el {day['es']} {num} a las {h}:{m:02d}. Si algo, llámame al {phone}."),
        (f"hola {name} al final no alcanzo a llegar a las {h}:{m:02d} llego como media hora mas tarde perdon",
         f"Hola {name}, al final no alcanzo a llegar a las {h}:{m:02d}. Llego como media hora más tarde. Perdón."),
        (f"{name} me mandas el enlace de la reunion del {day['es']} {num} porfa que no me llego",
         f"{name}, ¿me mandas el enlace de la reunión del {day['es']} {num}, por favor? No me llegó."),
    ]
    en = [
        (f"hey {name} confirming the {day['en']} the {ordinal(num)} at {h % 12 or 12}:{m:02d} pm call me at {phone} if needed",
         f"Hey {name}, confirming {day['en']} the {ordinal(num)} at {h % 12 or 12}:{m:02d} p.m. Call me at {phone} if needed."),
    ]
    fr = [
        (f"salut {name} je te confirme le {day['fr']} {num} a {h}h{m:02d} appelle moi au {phone} si besoin",
         f"Salut {name}, je te confirme le {day['fr']} {num} à {h}h{m:02d}. Appelle-moi au {phone} si besoin."),
    ]
    return {"es": es, "en": en, "fr": fr}


CG_LANGS = ["es"] * 7 + ["en"] * 2 + ["fr"] * 2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--cg-ratio", type=float, default=0.12)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    seen: set[tuple[str, str]] = set()
    rows = []
    attempts = 0
    while len(rows) < args.n and attempts < args.n * 80:
        attempts += 1
        if rng.random() < args.cg_ratio:
            lang = rng.choice(CG_LANGS)
            inp, out = rng.choice(cg_example(rng)[lang])
            source = target = lang
            style = "correct_grammar"
        else:
            inputs, outputs = rng.choice(PRO_SCENARIOS)(rng)
            source, target = rng.choice(PRO_PAIRS)
            inp, out = inputs[source], outputs[target]
            style = "professional"

        # Collapse the double period that appears when an English "p.m." meets a sentence stop.
        inp, out = inp.replace("..", "."), out.replace("..", ".")

        key = (inp, out)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "id": f"opus-{len(rows):04d}",
            "source": source,
            "target": target,
            "style": style,
            "input": inp,
            "output": out,
        })

    OUT_FILE.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )

    from collections import Counter
    pairs = Counter(f"{r['source']}->{r['target']}" for r in rows)
    styles = Counter(r["style"] for r in rows)
    print(f"wrote {len(rows)} examples to {OUT_FILE.name}")
    print("styles:", dict(styles))
    print("pairs:", dict(sorted(pairs.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
