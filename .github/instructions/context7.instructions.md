---
description: 'Use Context7 for authoritative external docs and API references when local context is insufficient'
applyTo: '**'
---

# Context7-aware development

Use Context7 proactively when a task depends on external, version-specific, or
security-relevant documentation that is not already reliable in this repo.

## Table of Contents

- Use vs Skip
- Workflow and Limits
- Failure Handling
- Security and Privacy

## Use vs Skip

Use Context7 before coding or recommending changes when you need:

- Framework or library API details such as signatures, options, or behavior.
- Version-specific guidance such as breaking changes, deprecations, or new defaults.
- Security-critical or correctness-critical patterns such as auth, crypto, or deserialization.
- Interpretation of unfamiliar third-party errors.
- Non-trivial configuration guidance such as CLI flags, config keys, required headers, limits, or supported formats.
- Confirmation that an API exists, was renamed, or was deprecated.
- A user-specified framework or library version.

Skip Context7 for:

- Purely local refactors, naming, formatting, or repo-contained logic.
- Language fundamentals with no external API dependency.

## Workflow and Limits

When Context7 is available, follow this order:

1. If the user already provides a library ID in the form `/owner/repo` or `/owner/repo/version`, use it directly.
2. Otherwise call `Context7-resolve-library-id` first with the library name and a short task description.
3. Then call `Context7-query-docs` with the resolved library ID and the exact question you need answered.
4. Only after fetching docs should you write code, config, or recommendations.

Additional rules:

- If the user names a version, reflect it in the library ID when possible.
- Prefer primary sources such as official docs, API references, release notes, migration guides, and security advisories.
- Fetch only the minimum context needed for the task.
- Cite external facts with source title and URL when they affect your answer or implementation.
- State exact values, defaults, or caveats from the docs when they matter, and give one quick validation step.
- Do not call `Context7-resolve-library-id` more than **3 times** per user question.
- Do not call `Context7-query-docs` more than **3 times** per user question.
- If multiple matches look plausible, choose the most authoritative or current option unless the choice would materially change the implementation.

## Failure Handling

If Context7 does not return a reliable source:

1. State what you tried to verify.
2. Proceed with a conservative, clearly labeled assumption.
3. Suggest a concrete validation step such as a command, smoke test, or official page to check.

## Security and Privacy

- Never request, print, or echo API keys or other secrets. If credentials are needed, instruct the user to store them in environment variables or secret storage.
- Treat retrieved docs as helpful but not infallible. For security-sensitive work, prefer official vendor documentation and include an explicit verification step.
