---
applyTo: "**/*.py"
---

# Python Coding Conventions

## Core Expectations

- Type-checking is a first-class requirement. Write Python that passes strict static analysis.
- Prefer built-in generics on Python 3.11 code, such as `list[str]` and `dict[str, int]`, instead of legacy `typing.List` and `typing.Dict`.
- Keep line length aligned with repo tooling defaults, targeting `<= 120` unless a stricter local rule applies.

## Documentation

- Write meaningful docstrings for modules, classes, and public methods when responsibilities, contracts, or control flow are not obvious.
- Write docstrings with enough context for Java-background maintainers to understand responsibilities and behavior without relying on Python-specific idioms.
- Avoid boilerplate docstrings that only restate names or signatures.

## Module and Class Design

- Prefer classes when state, lifecycle, or dependency boundaries matter, and module-level functions when logic is stateless and composable.
- Organize modules by cohesive responsibility.
- Non-public module helpers should use a leading underscore.

## Naming

- Use explicit, domain-specific names that communicate purpose and scope; avoid vague or generic names unless the scope is trivially small.
- Name references by their role in context rather than repeating the full type name.

## API Surface and Explicitness

- Prefer explicit, typed parameters in public APIs over flexible signatures.
- Avoid implicit or dynamic public APIs built around monkey patching, `setattr`, `getattr`, or runtime metaprogramming.
- Avoid module import side effects; module top-level code should primarily declare constants, types, and functions, with execution wired through explicit entry points.

## Boundary and Data Handling

- Parse and validate untyped boundary data immediately at HTTP, JSON, environment, and CLI edges, then pass typed objects inward.
- Use typed DTOs for external payloads when the boundary benefits from a clear parsed representation.
- REST API request and response payloads use snake_case field names on the wire. Do not use `alias_generator=to_camel`, `Field(alias=...)`, `Query(alias=...)`, `populate_by_name`, or `by_alias=True`. Pydantic `BaseModel` DTOs should use `model_config = ConfigDict(extra="forbid")` with plain snake_case field names only.
- Centralize value parsing utilities instead of scattering ad hoc conversions throughout the codebase.
- Keep I/O bounded with explicit timeouts, and do not hide failures behind silent defaults.

## Error Handling

- Raise explicit, domain-relevant errors with context-rich messages.
- Prefer explicit `raise` checks over `assert` for runtime validation because asserts can be optimized out.
- For Java ports, preserve the exact exception type mapping and exception messages when the ported contract depends on them.
- Avoid broad exception handling except at true boundaries; when a boundary must translate an error, re-raise a typed exception with a clear message and the chained cause.

## Testing

- Keep tests typed when strict checking reaches fixtures or helpers.
- Mirror the source package structure under `tests/` so production and test paths stay easy to map.
- Prefer test module names that map cleanly to the production module or primary class under test.
- Keep shared fixtures and factories in dedicated support packages instead of scattering cross-cutting helpers across class-specific test modules.
- Preserve package semantics in tests when the layout requires `__init__.py` files to mirror source package boundaries cleanly.
