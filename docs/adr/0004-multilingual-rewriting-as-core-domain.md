# 4. Multilingual rewriting is a core domain concept

- Status: Accepted
- Date: 2026-08-10

## Context

Cross-language rewriting (e.g. informal Spanish → professional French) is a first-class
requirement, not an optional translation feature. Hiding it inside ad-hoc prompts would
scatter product behavior across the codebase and make it untestable.

## Decision

Model source and target language as first-class domain types on `RewriteRequest`:

- `SourceLanguage` = `Auto | Known(Language)` — the input language may be inferred.
- `TargetLanguage` = `SameAsSource | Fixed(Language)` — the output language is ALWAYS
  deterministic; an "unknown" target is unrepresentable by construction.

Translation is defined as the case where the resolved target differs from the source.
Same-language polishing and cross-language rewriting use one request type and one path.
The *how* (prompting the model to clean up, translate if needed, and adapt tone) is
encapsulated in the infrastructure layer, not in domain, use-case, or UI code.

## Consequences

- The multilingual product exists in the domain from day one, testable via a fake engine.
- Prompts are centralized and versionable.
- Cross-language quality (ES→FR, ES→EN) becomes a blocking criterion for model selection.
