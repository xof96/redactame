"""Generate a synthetic training set for Redactame by filling professional-message templates.

Why templates instead of an LLM teacher: we control the slot values (name, day, time, amount,
reference), so the informal INPUT and the polished OUTPUT are built with the exact same facts.
The gold answers preserve dates, times, numbers and roles by construction, which is precisely
the weakness we found in small models. No hallucinated facts, and no AI tells (no em dashes, no
stray ; or :, no signature placeholders).

This gives breadth and clean fact-preservation. Combine it with real, hand-written data (which
adds natural variety) for the best result.

    .\.venv\Scripts\python.exe generate_dataset.py --n 1000
"""

import argparse
import json
import random
from pathlib import Path

OUT_FILE = Path(__file__).resolve().parent / "train_synth.jsonl"

NAMES = [
    "Claire", "Thomas", "Sophie", "Julien", "Amelie", "Emily", "Michael", "Sarah", "James",
    "Daniel", "Valentina", "Ricardo", "Laura", "Carolina", "Andres", "Martin", "Juan", "Emma",
    "Lucas", "Marie", "Paul", "Nicolas", "Elena", "Diego", "Paula", "Camila", "Antoine", "Chloe",
    "David", "Anna", "Pierre", "Sofia", "Hugo", "Clara", "Marc", "Ines", "Leo", "Julia",
]

DAYS = [
    {"es": "lunes", "fr": "lundi", "en": "Monday"},
    {"es": "martes", "fr": "mardi", "en": "Tuesday"},
    {"es": "miércoles", "fr": "mercredi", "en": "Wednesday"},
    {"es": "jueves", "fr": "jeudi", "en": "Thursday"},
    {"es": "viernes", "fr": "vendredi", "en": "Friday"},
]

# Parallel time phrases: same instant expressed naturally in each language.
TIMES = [
    {"es": "las nueve", "fr": "9h", "en": "9 a.m."},
    {"es": "las nueve y media", "fr": "9h30", "en": "9:30 a.m."},
    {"es": "las diez", "fr": "10h", "en": "10 a.m."},
    {"es": "las diez y media", "fr": "10h30", "en": "10:30 a.m."},
    {"es": "las once", "fr": "11h", "en": "11 a.m."},
    {"es": "las dos de la tarde", "fr": "14h", "en": "2 p.m."},
    {"es": "las tres de la tarde", "fr": "15h", "en": "3 p.m."},
    {"es": "las cuatro de la tarde", "fr": "16h", "en": "4 p.m."},
    {"es": "las cinco de la tarde", "fr": "17h", "en": "5 p.m."},
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
]

ITEMS = [
    {"es": "el enlace", "fr": "le lien", "en": "the link"},
    {"es": "la factura", "fr": "la facture", "en": "the invoice"},
    {"es": "el documento", "fr": "le document", "en": "the document"},
]

MEDIA = ["Teams", "Zoom", "Google Meet"]


def ordinal(n: int) -> str:
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def date_str(day_num: int, month: dict, lang: str) -> str:
    if lang == "es":
        return f"el {day_num} de {month['es']}"
    if lang == "fr":
        return f"le {day_num} {month['fr']}"
    return f"{month['en']} {ordinal(day_num)}"


# --- Professional scenarios --------------------------------------------------------------
# Each returns dicts of informal INPUT and polished OUTPUT per language, sharing the same facts.

def sc_reschedule(rng):
    n = rng.choice(NAMES)
    d1, d2 = rng.sample(DAYS, 2)
    t = rng.choice(TIMES)
    return {
        "inputs": {
            "es": f"hola {n} perdona pero al final el {d1['es']} a {t['es']} se me complicó y no voy a poder, podríamos moverlo al {d2['es']} a la misma hora si te sirve",
            "fr": f"salut {n} désolé mais finalement le {d1['fr']} à {t['fr']} ça va pas être possible, est-ce qu'on pourrait le déplacer au {d2['fr']} à la même heure",
            "en": f"hey {n} sorry but {d1['en']} at {t['en']} isn't going to work anymore, could we move it to {d2['en']} at the same time",
        },
        "outputs": {
            "es": f"Hola {n}, disculpa, pero al final el {d1['es']} a {t['es']} no me va a ser posible. ¿Podríamos moverlo al {d2['es']} a la misma hora, si te viene bien?",
            "fr": f"Bonjour {n}, je suis désolé, mais finalement le {d1['fr']} à {t['fr']} ne sera pas possible. Pourrions-nous le déplacer au {d2['fr']} à la même heure, si cela vous convient ?",
            "en": f"Hi {n}, my apologies, but {d1['en']} at {t['en']} will no longer work. Could we move it to {d2['en']} at the same time, if that works for you?",
        },
    }


def sc_confirm_avail(rng):
    n = rng.choice(NAMES)
    d = rng.choice(DAYS)
    t = rng.choice(TIMES)
    m = rng.choice(MEDIA)
    return {
        "inputs": {
            "es": f"hola {n} sí perfecto revisé mi agenda y el {d['es']} a {t['es']} me sirve sin problema si quieres lo hacemos por {m} gracias",
            "fr": f"bonjour {n} oui parfait j'ai vérifié mon agenda et le {d['fr']} à {t['fr']} ça me va très bien si tu veux on le fait par {m} merci",
            "en": f"hi {n} yeah perfect i checked my calendar and {d['en']} at {t['en']} works for me no problem if you want we can do it over {m} thanks",
        },
        "outputs": {
            "es": f"Hola {n}, perfecto. Revisé mi agenda y el {d['es']} a {t['es']} me viene bien sin problema. Si le parece, podemos hacerlo por {m}. Gracias.",
            "fr": f"Bonjour {n}, parfait. J'ai vérifié mon agenda et le {d['fr']} à {t['fr']} me convient sans problème. Si vous le souhaitez, nous pouvons le faire par {m}. Merci.",
            "en": f"Hi {n}, perfect. I checked my calendar and {d['en']} at {t['en']} works for me without any problem. If you like, we can do it over {m}. Thank you.",
        },
    }


def sc_payment(rng):
    n = rng.choice(NAMES)
    amount = rng.choice([320, 480, 850, 990, 1200, 1500, 1750, 2300])
    dnum = rng.randint(1, 28)
    month = rng.choice(MONTHS)
    ref = f"{rng.choice('ABCDEFGH')}{rng.choice('ABCDEFGH')}{rng.randint(1000, 9999)}"
    return {
        "inputs": {
            "es": f"buenas {n} te confirmo que el pago de {amount} euros lo hice {date_str(dnum, month, 'es')} y el número de referencia es {ref} cualquier cosa me avisas",
            "fr": f"bonjour {n} je te confirme que le paiement de {amount} euros a été fait {date_str(dnum, month, 'fr')} et le numéro de référence est {ref} n'hésite pas si besoin",
            "en": f"hi {n} just confirming the payment of {amount} euros was made on {date_str(dnum, month, 'en')} and the reference number is {ref} let me know if anything",
        },
        "outputs": {
            "es": f"Buenas {n}, le confirmo que el pago de {amount} euros se realizó {date_str(dnum, month, 'es')} y que el número de referencia es {ref}. No dude en avisarme si necesita algo.",
            "fr": f"Bonjour {n}, je vous confirme que le paiement de {amount} euros a été effectué {date_str(dnum, month, 'fr')} et que le numéro de référence est {ref}. N'hésitez pas à me contacter si besoin.",
            "en": f"Hi {n}, I confirm that the payment of {amount} euros was made on {date_str(dnum, month, 'en')} and that the reference number is {ref}. Please let me know if you need anything.",
        },
    }


def sc_job_uncertain(rng):
    n = rng.choice(NAMES)
    return {
        "inputs": {
            "es": f"hola {n} gracias por escribirme la verdad sí me interesa la oportunidad pero antes de confirmar nada necesito revisar mi agenda te digo pronto",
            "fr": f"bonjour {n} merci pour votre message franchement l'opportunité m'intéresse mais avant de confirmer quoi que ce soit je dois vérifier mon agenda je vous dis vite",
            "en": f"hi {n} thanks for reaching out i'm genuinely interested in the opportunity but before i confirm anything i need to check my schedule i'll let you know soon",
        },
        "outputs": {
            "es": f"Hola {n}, gracias por escribirme. La oportunidad me interesa, pero antes de confirmar nada necesito revisar mi agenda. Le comento pronto.",
            "fr": f"Bonjour {n}, merci pour votre message. L'opportunité m'intéresse, mais avant de confirmer quoi que ce soit, je dois vérifier mon agenda. Je reviens vers vous rapidement.",
            "en": f"Hi {n}, thank you for reaching out. The opportunity interests me, but before confirming anything I need to check my schedule. I will get back to you soon.",
        },
    }


def sc_job_reject(rng):
    n = rng.choice(NAMES)
    return {
        "inputs": {
            "es": f"buenas {n} muchas gracias por pensar en mí pero por ahora prefiero quedarme en mi puesto actual igual le agradezco el contacto y quizás seguimos en contacto para más adelante",
            "fr": f"bonjour {n} merci beaucoup d'avoir pensé à moi mais pour l'instant je préfère rester à mon poste actuel je vous remercie quand même et on peut peut-être rester en contact pour plus tard",
            "en": f"hi {n} thanks a lot for thinking of me but for now i'd rather stay in my current role i really appreciate you reaching out and maybe we can keep in touch for the future",
        },
        "outputs": {
            "es": f"Buenas {n}, muchas gracias por pensar en mí. Por el momento prefiero quedarme en mi puesto actual. De todos modos le agradezco mucho el contacto y quizás podamos mantenernos en contacto para más adelante.",
            "fr": f"Bonjour {n}, merci beaucoup d'avoir pensé à moi. Pour le moment, je préfère rester à mon poste actuel. Je vous remercie néanmoins de m'avoir contacté et nous pourrions peut-être rester en contact pour plus tard.",
            "en": f"Hi {n}, thank you very much for thinking of me. For now, I prefer to stay in my current role. I still appreciate you reaching out, and perhaps we can keep in touch for the future.",
        },
    }


def sc_resend(rng):
    n = rng.choice(NAMES)
    it = rng.choice(ITEMS)
    d = rng.choice(DAYS)
    t = rng.choice(TIMES)
    return {
        "inputs": {
            "es": f"buenas {n} te escribo porque todavía no me llegó {it['es']} para la reunión del {d['es']} a {t['es']} no sé si me lo podrías reenviar cuando tengas un momento gracias",
            "fr": f"bonjour {n} je t'écris parce que je n'ai toujours pas reçu {it['fr']} pour la réunion du {d['fr']} à {t['fr']} est-ce que tu pourrais me le renvoyer quand tu as un moment merci",
            "en": f"hi {n} i'm writing because i still haven't received {it['en']} for the {d['en']} meeting at {t['en']} could you resend it when you have a moment thanks",
        },
        "outputs": {
            "es": f"Buenas {n}, le escribo porque todavía no me ha llegado {it['es']} para la reunión del {d['es']} a {t['es']}. ¿Podría reenviármelo cuando tenga un momento? Gracias.",
            "fr": f"Bonjour {n}, je vous écris car je n'ai toujours pas reçu {it['fr']} pour la réunion du {d['fr']} à {t['fr']}. Pourriez-vous me le renvoyer quand vous avez un moment ? Merci.",
            "en": f"Hi {n}, I'm writing because I still haven't received {it['en']} for the {d['en']} meeting at {t['en']}. Could you resend it when you have a moment? Thank you.",
        },
    }


def sc_delivery(rng):
    n = rng.choice(NAMES)
    units = rng.choice([100, 150, 200, 250, 500, 750, 1000])
    m = rng.choice(MONTHS)
    d1 = rng.randint(1, 14)
    d2 = d1 + rng.randint(3, 10)
    return {
        "inputs": {
            "es": f"hola {n} una consulta podríamos mover la entrega de las {units} unidades del {d1} de {m['es']} al {d2} de {m['es']}",
            "fr": f"bonjour {n} une question est-ce qu'on pourrait décaler la livraison des {units} unités du {d1} {m['fr']} au {d2} {m['fr']}",
            "en": f"hi {n} quick question could we push the delivery of the {units} units from {m['en']} {ordinal(d1)} to {m['en']} {ordinal(d2)}",
        },
        "outputs": {
            "es": f"Hola {n}, quería consultarle si podríamos mover la entrega de las {units} unidades del {d1} de {m['es']} al {d2} de {m['es']}.",
            "fr": f"Bonjour {n}, je voulais savoir si nous pourrions décaler la livraison des {units} unités du {d1} {m['fr']} au {d2} {m['fr']}.",
            "en": f"Hi {n}, I wanted to ask whether we could push the delivery of the {units} units from {m['en']} {ordinal(d1)} to {m['en']} {ordinal(d2)}.",
        },
    }


def sc_contract(rng):
    n = rng.choice(NAMES)
    m = rng.choice(MONTHS)
    a = rng.randint(1, 14)
    b = a + rng.randint(3, 10)
    return {
        "inputs": {
            "es": f"hola {n} ya revisé el contrato y en general está todo bien pero tengo una duda con la fecha de inicio porque aparece el {a} de {m['es']} y habíamos hablado del {b} de {m['es']} me confirmas cuál es la correcta",
            "fr": f"bonjour {n} j'ai relu le contrat et globalement tout est bon mais j'ai un doute sur la date de début parce qu'il indique le {a} {m['fr']} alors qu'on avait parlé du {b} {m['fr']} peux tu me confirmer laquelle est la bonne",
            "en": f"hi {n} i've reviewed the contract and overall it's all good but i have a question about the start date because it shows {m['en']} {ordinal(a)} and we had talked about {m['en']} {ordinal(b)} can you confirm which one is correct",
        },
        "outputs": {
            "es": f"Hola {n}, ya revisé el contrato y en general está todo bien, pero tengo una duda con la fecha de inicio. Aparece el {a} de {m['es']}, pero habíamos hablado del {b} de {m['es']}. ¿Me confirma cuál es la correcta?",
            "fr": f"Bonjour {n}, j'ai relu le contrat et, dans l'ensemble, tout est bon. J'ai toutefois un doute sur la date de début. Il indique le {a} {m['fr']}, alors que nous avions parlé du {b} {m['fr']}. Pourriez-vous me confirmer laquelle est la bonne ?",
            "en": f"Hi {n}, I've reviewed the contract and overall everything is fine, but I have a question about the start date. It shows {m['en']} {ordinal(a)}, but we had talked about {m['en']} {ordinal(b)}. Could you confirm which one is correct?",
        },
    }


def sc_late_reply(rng):
    n = rng.choice(NAMES)
    reason = rng.choice([
        {"es": "estuve de viaje estos días", "fr": "j'étais en déplacement ces jours-ci", "en": "I was traveling these past few days"},
        {"es": "estuve bastante ocupado esta semana", "fr": "j'ai été assez occupé cette semaine", "en": "I was quite busy this week"},
    ])
    return {
        "inputs": {
            "es": f"buenas {n} perdón por responder tan tarde {reason['es']} y recién pude ver su mensaje me gustaría saber un poco más del puesto si todavía sigue disponible gracias",
            "fr": f"bonjour {n} désolé de répondre si tard {reason['fr']} et je viens seulement de voir votre message j'aimerais en savoir un peu plus sur le poste s'il est toujours disponible merci",
            "en": f"hi {n} sorry for the late reply {reason['en']} and i only just saw your message i'd like to know a bit more about the position if it's still available thanks",
        },
        "outputs": {
            "es": f"Buenas {n}, perdón por responder tan tarde. {reason['es'].capitalize()} y recién pude ver su mensaje. Me gustaría saber un poco más sobre el puesto, si todavía sigue disponible. Gracias.",
            "fr": f"Bonjour {n}, désolé de répondre si tard. {reason['fr'].capitalize()} et je viens seulement de voir votre message. J'aimerais en savoir un peu plus sur le poste, s'il est toujours disponible. Merci.",
            "en": f"Hi {n}, apologies for the late reply. {reason['en']} and I only just saw your message. I would like to know a bit more about the position, if it is still available. Thank you.",
        },
    }


PRO_SCENARIOS = [
    sc_reschedule, sc_confirm_avail, sc_payment, sc_job_uncertain, sc_job_reject,
    sc_resend, sc_delivery, sc_contract, sc_late_reply,
]

# Weighted language pairs (source, target), Spanish-source emphasized to match real use.
PRO_PAIRS = (
    [("es", "fr")] * 5 + [("es", "en")] * 4 + [("es", "es")] * 3 +
    [("en", "es")] * 2 + [("en", "fr")] * 2 + [("en", "en")] * 2 +
    [("fr", "es")] * 2 + [("fr", "en")] * 1 + [("fr", "fr")] * 1
)


# --- correct_grammar templates (same language, fix typos minimally) ----------------------

def cg_examples(rng):
    n = rng.choice(NAMES)
    t = rng.choice(TIMES)
    d = rng.choice(DAYS)
    es = [
        (f"hola {n} como estas queria preguntarte si mañana vas a estar en la oficina porque tengo que dejarte unos papeles",
         f"Hola {n}, ¿cómo estás? Quería preguntarte si mañana vas a estar en la oficina, porque tengo que dejarte unos papeles."),
        (f"oye {n} te queria avisar que al final no alcanzo a llegar a {t['es']} voy a llegar como media hora mas tarde perdon",
         f"Oye {n}, te quería avisar que al final no alcanzo a llegar a {t['es']}. Voy a llegar como media hora más tarde. Perdón."),
        (f"{n} te mande el archivo ayer pero creo que se me olvido adjuntar la ultima pagina avisame si quieres que te lo mande de nuevo",
         f"{n}, te mandé el archivo ayer, pero creo que se me olvidó adjuntar la última página. Avísame si quieres que te lo mande de nuevo."),
        (f"hola {n} si claro puedo ayudarte pero hoy estoy medio ocupado si quieres lo vemos mañana en la tarde",
         f"Hola {n}, sí, claro que puedo ayudarte, pero hoy estoy medio ocupado. Si quieres, lo vemos mañana por la tarde."),
    ]
    en = [
        (f"hi {n} i wanted to confirmed that the meeting is on {d['en']} and that we will discussing the budget",
         f"Hi {n}, I wanted to confirm that the meeting is on {d['en']} and that we will be discussing the budget."),
        (f"hey {n} i writting to let you know i recieved you're email and i will responded tomorrow",
         f"Hey {n}, I'm writing to let you know I received your email and I will respond tomorrow."),
    ]
    fr = [
        (f"salut {n} je voulais te dire que jai bien recu ton message et je te repond demain sans faute",
         f"Salut {n}, je voulais te dire que j'ai bien reçu ton message et je te réponds demain sans faute."),
        (f"bonjour {n} desole pour le retard je vous envois le document ce soir",
         f"Bonjour {n}, désolé pour le retard, je vous envoie le document ce soir."),
    ]
    return {"es": es, "en": en, "fr": fr}


CG_LANGS = ["es"] * 7 + ["en"] * 2 + ["fr"] * 2


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--cg-ratio", type=float, default=0.15)
    args = parser.parse_args()
    rng = random.Random(args.seed)

    seen: set[tuple[str, str]] = set()
    rows = []
    attempts = 0
    while len(rows) < args.n and attempts < args.n * 60:
        attempts += 1
        if rng.random() < args.cg_ratio:
            lang = rng.choice(CG_LANGS)
            inp, out = rng.choice(cg_examples(rng)[lang])
            source = target = lang
            style = "correct_grammar"
        else:
            scenario = rng.choice(PRO_SCENARIOS)(rng)
            source, target = rng.choice(PRO_PAIRS)
            inp = scenario["inputs"][source]
            out = scenario["outputs"][target]
            style = "professional"

        key = (inp, out)
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "id": f"syn-{len(rows):04d}",
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

    # Small summary so we can sanity-check the mix.
    from collections import Counter
    pairs = Counter(f"{r['source']}->{r['target']}" for r in rows)
    styles = Counter(r["style"] for r in rows)
    print(f"wrote {len(rows)} examples to {OUT_FILE.name}")
    print("styles:", dict(styles))
    print("pairs:", dict(sorted(pairs.items(), key=lambda kv: -kv[1])))


if __name__ == "__main__":
    main()
