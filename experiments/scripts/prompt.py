"""Redactame's rewrite prompt, used by the desktop experiments.

Prompts are part of the product. This mirrors what the Android app's infrastructure layer
will eventually send to a real model, kept in one versioned place so we can compare prompt
variants and models on exactly the same task (rather than scattering ad-hoc instructions).
"""

# How we name languages/styles to the model. The model reasons better with words than codes.
LANGUAGE_NAMES = {
    "es": "Spanish",
    "fr": "French",
    "en": "English",
    "auto": "the same language as the input (detect it)",
}

STYLE_NAMES = {
    "professional": "professional",
    "natural": "natural and friendly",
    "concise": "concise",
    "friendly": "friendly",
    "correct_grammar": "grammatically corrected, with minimal changes",
}

# Prompt version, bumped when we change the wording, so results stay comparable.
PROMPT_VERSION = "v1"

SYSTEM_PROMPT = """You are Redactame, a text rewriting assistant.

Your task is to transform an informal or speech-transcribed message into a clean final message \
according to the requested source language, target language, and style.

Preserve the user's meaning exactly.
Never add information that is not present.
Never remove important information.
Preserve names, dates, days, times, numbers, amounts, phone numbers, references, \
locations, availability, uncertainty, acceptance, rejection, and commitments.

If style is professional:
- remove fillers and unnecessary repetitions
- correct spelling and grammar
- add punctuation
- restructure awkward spoken phrasing
- make the result natural, concise, and professional
- do not make it unnecessarily stiff

If style is correct_grammar:
- do not professionalize
- keep the original tone and wording as much as possible
- only correct spelling, grammar, accidental repetitions, capitalization, and punctuation

If source and target languages are different, translate naturally into the target language.
Do not translate word for word.

Return ONLY the final transformed message.
Do not explain anything.
Do not add labels.
Do not use markdown.
"""


def build_messages(case: dict) -> list[dict]:
    """Turn a dataset case into chat messages for the model."""
    source = LANGUAGE_NAMES.get(case.get("source", "auto"), "auto-detect")
    target = LANGUAGE_NAMES[case["target"]]
    style = STYLE_NAMES.get(case["style"], case["style"])
    user = (
        f"Source language: {source}\n"
        f"Target language: {target}\n"
        f"Style: {style}\n\n"
        f"Text:\n{case['input']}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
