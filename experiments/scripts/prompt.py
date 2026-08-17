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

SYSTEM_PROMPT = """You rewrite messy, informal, or spoken input into a single polished written message.

Rules:
- Preserve the meaning, intent, dates, times, names, numbers, commitments, and level of \
certainty. Never invent information or add anything the user did not say.
- Remove filler words, hesitations, and spoken repetition.
- Adapt the tone to the requested style.
- Write the output in the target language. If it differs from the source language, translate \
naturally (convey the meaning) rather than word-for-word.
- Do not turn uncertainty into a commitment, and do not strengthen claims.
- Return ONLY the final rewritten message: no explanations, no quotes, no preamble.
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
