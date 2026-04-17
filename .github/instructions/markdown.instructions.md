---
description: 'Documentation and content creation standards'
applyTo: '**/*.md'
---

# Markdown Files Editing Rules

## Markdown Content Rules

The following markdown content rules are enforced in the validators:

1. **Headings**: Use appropriate heading levels (H2, H3, etc.) to structure your content. Do not use an H1 heading more than once in a file.
2. **Lists**: Use bullet points or numbered lists for lists. Do not use multi-level bullets or lists.
3. **Code Blocks**: Use fenced code blocks for code snippets and specify the language for syntax highlighting.
4. **Links**: Use proper markdown syntax for links. Ensure that links are valid and accessible.
5. **Images**: Use proper markdown syntax for images. Include alt text for accessibility.
6. **Tables**: Use markdown tables for tabular data. Ensure proper formatting and alignment.
7. **Line Length**: Limit line length to 400 characters for readability.
8. **Whitespace**: Use appropriate whitespace to separate sections and improve readability.
9. **Front Matter**: Include YAML front matter at the beginning of the file with required metadata fields.

## Formatting and Structure

Follow these guidelines for formatting and structuring your markdown content:

- **Headings**: Use `##` for H2 and `###` for H3. Ensure that headings are used in a hierarchical manner. Recommend restructuring if content includes H4, and more strongly recommend for H5.
- **Lists**: Use `-` for bullet points and `1.` for numbered lists.
- **Code Blocks**: Use triple backticks (three backtick characters) to create fenced code blocks. Specify the language after the opening backticks for syntax highlighting (e.g., `csharp`).
- **Links**: Use `[link text](https://example.com)` for links. Ensure that the link text is descriptive and the URL is valid.
- **Images**: Use `![alt text](https://example.com/image.png)` for images. Include a brief description of the image in the alt text.
- **Tables**: Use `|` to create tables. Ensure that columns are properly aligned and headers are included.
- **Whitespace**: Use blank lines to separate sections and improve readability. Avoid excessive whitespace.

## Citations/Footnote Instructions in Markdown Documents

- Convert author–date citations into Markdown footnotes manually (paragraph-by-paragraph), not via bulk replace/regex.
- Remove in-text parenthetical citations entirely and replace with footnote markers. Example: `...(Romo & Chappell, 2023).` → `...[^romo-chappell-2023].`
- Use **semantic** footnote labels (not sequential numbers). Prefer a stable, human-readable key like `author-year` (optionally add a short disambiguator): `[^romo-chappell-2023]`, `[^smith-2021-methods]`.
- For multi-cite groups like `(A, 1994; B, 2021)`, use multiple footnote markers (one per source): `...[^a-1994][^b-2021]`.
- Put all footnote definitions in one block at the end under a single heading titled : `FOOTNOTE CITATIONS`. Each definition is one line: `[^romo-chappell-2023]: Full reference text (plus any locator like p./pp. if present).`
- Only convert true citations; do not convert date-only parentheses that are not citations (e.g., `(December, 2017)`), unless explicitly instructed otherwise.
