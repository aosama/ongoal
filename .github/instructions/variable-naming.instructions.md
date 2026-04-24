---
description: "How to name Variables for maximum code clarity and Readability"
applyTo: '**'
---

# Effective Variable Naming Guidelines for Coding Agents

## Universal Instructions for Any Programming Language

These guidelines help coding agents (and human developers) produce code that is self-documenting, maintainable, and easy to understand. The goal is to replace generic, low-intent names like `i`, `j`, `chunk`, `buffer`, `data`, `temp`, or `result` with names that clearly communicate **intent, purpose, meaning, and domain relevance**.

Good names reduce the need for comments, speed up code reviews, and minimize bugs caused by misunderstanding.

---

## Why Variable Naming Matters

- **Readability First**: Code is read 10x more than it is written. Names are the primary way readers understand *what* data represents and *why* it exists.
- **Cognitive Load**: Cryptic names force readers to keep mental mappings ("what does `buf` mean again?"). Clear names free mental bandwidth for logic.
- **Maintainability**: When requirements change, descriptive names make refactoring safer and faster.
- **Domain Alignment**: Names should reflect the business or problem domain (e.g., `invoiceTotal`, `customerEligibilityStatus`) rather than generic programming concepts.
- **AI-Specific Benefit**: As a coding agent, using precise names makes your generated code more trustworthy and easier for humans (or future agents) to review, extend, or debug.

**Core Rule**: Every variable name should answer three questions:

1. **What** does this variable hold?
2. **Why** does it exist in this context?
3. **How** is it used or transformed?

If the name doesn't answer these clearly, rename it.

---

## Core Principles

1. **Intention-Revealing Names**
   The name must reveal the variable's purpose at first glance.
   - Bad: `data`, `info`, `value`, `obj`, `item`
   - Good: `customerProfile`, `orderValidationErrors`, `monthlySalesTotal`

2. **Use Domain-Relevant Vocabulary**
   Draw from the problem domain, not implementation details.
   - Instead of `chunk` or `buffer` → `invoiceBatch`, `compressedImageBlock`, `networkResponsePacket`, `userSessionState`
   - Instead of generic `list` or `array` → `activeSubscriptions`, `pendingOrders`, `searchResults`

3. **Pronounceable and Searchable**
   - Names should be easy to say aloud and find with search (Ctrl+F / grep).
   - Avoid unpronounceable abbreviations: `genYmdHms` → `generationTimestamp`
   - Avoid single letters except in the narrowest scopes (see below).

4. **Length Proportional to Scope**
   - Small scope (inside a 5-line loop): shorter names acceptable if context is obvious.
   - Module / class / file scope: fully descriptive names required.
   - Example: `i` might be tolerable in a 3-line `for` loop over a clearly named collection, but never `userData` at the top of a file.

5. **Avoid Disinformation and Noise Words**
   - Do not imply false information (e.g., calling something `list` when it can be empty or a different type).
   - Remove redundant words: `userDataObject`, `stringName`, `intCount`, `tempVariable` → `user`, `name`, `count`, `intermediateValue`

6. **Follow Language Naming Conventions**
   - Apply the principles *within* the language's style:
     - Python: `snake_case`
     - JavaScript / Java / C#: `camelCase`
     - Constants: `UPPER_SNAKE_CASE` or language equivalent
   - Never let style override clarity.

7. **Consistency Across the Codebase**
   - Use the same term for the same concept everywhere (`user` vs `customer` vs `account` — pick one and stick to it).
   - Maintain a project glossary of domain terms if the domain is complex.

---

## Specific Guidelines by Context

### Loop Variables and Iterators

**Never use bare `i`, `j`, `k`, `idx` when the collection has meaning.**

- **Bad**:

  ```python
  for i in range(len(users)):
      process(users[i])
  ```

- **Good**:

  ```python
  for user_index, user in enumerate(users):
      process_user_profile(user)

  # Or even better when possible:
  for user in users:
      process_user_profile(user)
  ```

- For nested loops:

  ```python
  for row_index, row in enumerate(grid):
      for column_index, cell in enumerate(row):
          ...
  ```

- Use `index` / `idx` only when the numeric position itself is semantically important (rare).

### Collections, Arrays, Lists, Dicts, Sets

- Use **plural nouns** for collections of the same type.
- Specify the *kind* of thing when helpful.
  - `users` (if context makes type obvious)
  - `activeUsers`, `pendingOrders`, `searchResultItems`
  - `userIdToProfileMap` (for dicts/maps when key/value types matter)

- Avoid: `items`, `elements`, `dataList`, `arr`, `collection`

### Buffers, Chunks, Packets, Blocks

Replace generic terms with content + purpose:

| Generic       | Better Alternatives                              |
|---------------|--------------------------------------------------|
| `chunk`       | `dataChunk`, `fileChunk`, `messageChunk`, `invoiceBatch` |
| `buffer`      | `inputBuffer`, `renderBuffer`, `networkPacketBuffer`, `responseCache` |
| `block`       | `compressedBlock`, `memoryBlock`, `transactionBlock` |
| `packet`      | `networkPacket`, `authenticationPacket`          |

**Best practice**: Include the *source* or *destination* and *format* when relevant.

### Temporary and Intermediate Variables

**Never use `temp`, `tmp`, `temporary`, `intermediate` as the base name.**

- `tempUser` → `newlyRegisteredUser` or `userBeingValidated`
- `tmpResult` → `calculatedSubtotalBeforeTax`
- `buffer` (as temp) → `accumulatedResponseBody`

### Function Parameters and Return Values

- Parameters should describe their role in the function.
  - `def calculate_shipping_cost(order: Order, shipping_method: str)` — not `def calc(o, m)`
- Return values: name them after *what they represent*, not "result".
  - `processed_orders`, `validated_user_profile`, `eligibility_decision`

### Boolean Variables and Flags

Use prefixes that read naturally in conditions:

- `isActive`, `hasPermission`, `canProceed`, `shouldRetry`, `wasSuccessful`, `needsRefresh`
- Avoid: `active`, `permission`, `proceed` (these read poorly in `if active:`)

### Constants and Configuration

- `MAX_RETRY_ATTEMPTS`, `DEFAULT_SESSION_TIMEOUT_SECONDS`, `SUPPORTED_IMAGE_FORMATS`
- Include units when numeric: `MAX_FILE_SIZE_BYTES` not `MAX_FILE_SIZE`

### Class / Object Properties

- `customer.fullName`, `order.totalAmountIncludingTax`, `report.generationTimestamp`

---

## Common Pitfalls to Avoid

| Pitfall                    | Example Bad Name          | Why It's Bad                     | Better Name                     |
|----------------------------|---------------------------|----------------------------------|---------------------------------|
| Single letter              | `i`, `j`, `x`, `n`        | No meaning outside tiny scope    | `customerIndex`, `retryCount`   |
| Generic / vague            | `data`, `info`, `value`   | Could be anything                | `rawApiResponse`, `userDetails` |
| Implementation leak        | `arrayOfUsers`, `dictData`| Exposes type, not purpose        | `registeredUsers`, `profileMap` |
| Abbreviations              | `usr`, `cust`, `addr`     | Hard to remember / search        | `user`, `customer`, `address`   |
| Noise words                | `userObject`, `nameString`| Redundant                        | `user`, `name`                  |
| Misleading                 | `list` (that can be empty) | Implies non-empty                | `users` (or `userCollection`)   |
| Hungarian notation         | `strName`, `intCount`     | Ties to type, not meaning        | `name`, `count`                 |

---

## Best Practices Specifically for Coding Agents

1. **Plan Names Before Writing Code**
   In your reasoning step, explicitly list key variables and their intended names + justification.

2. **Refactor Immediately When Purpose Changes**
   If a variable's role evolves during implementation, rename it right away. Do not leave "legacy" names.

3. **Prefer Longer, Clear Names Over Short Cryptic Ones**
   A 30-character descriptive name is better than a 5-character mystery.

4. **Use the Domain Language the Human Uses**
   If the user talks about "invoices", "subscriptions", or "risk scores", use those exact terms in variable names.

5. **Leverage Type Systems When Available**
   In typed languages, the type helps, but the name should still add meaning beyond the type (e.g., `List<Order>` is good, but `pendingOrders: List<Order>` is better).

6. **Review Generated Code Aloud (in your mind)**
   Read the code back: "For each active subscription in activeSubscriptions, calculate the prorated amount..." — if it doesn't flow naturally, the names need work.

7. **Avoid "Result" and "Response" as Default Return Names**
   Only use them when the function truly returns a generic result with no better descriptor.

8. **Document Non-Obvious Abbreviations** (rarely needed)
   If you must use one (e.g., industry-standard `SKU`), add a comment on first use or use a glossary.

---

## Quick Decision Checklist (Use Before Naming Any Variable)

- [ ] Does the name answer "what is this?" and "why does it exist here?"
- [ ] Is it a noun or noun phrase (for data-holding variables)?
- [ ] Is it pronounceable and searchable?
- [ ] Does it use domain terms instead of generic programming terms?
- [ ] Is the length appropriate for its scope?
- [ ] Have I avoided `i`, `j`, `data`, `buffer`, `chunk`, `temp`, `result`, `info`, `obj`?
- [ ] Is it consistent with other names in the file / project?
- [ ] Would a new developer (or future me) understand it without reading surrounding code?

If any answer is "no", rename immediately.

---

## Example Transformation

**Before (Typical AI-generated code with poor names):**

```python
def process(data):
    result = []
    for i in range(len(data)):
        chunk = data[i]
        buffer = transform(chunk)
        if validate(buffer):
            result.append(buffer)
    return result
```

**After (Clear, intent-revealing names):**

```python
def process_customer_invoices(invoices: list[Invoice]) -> list[ProcessedInvoice]:
    processed_invoices: list[ProcessedInvoice] = []

    for invoice_index, raw_invoice in enumerate(invoices):
        validated_invoice = validate_invoice(raw_invoice)
        enriched_invoice = enrich_with_customer_data(validated_invoice)
        processed_invoices.append(enriched_invoice)

    return processed_invoices
```

The second version tells the story of *what* is happening and *why* each variable exists.

---

## Final Note for Coding Agents

**Clarity is a feature.**
Brevity in naming is false economy. Every minute you "save" with a short name costs the reader (human or agent) far more time later.

When in doubt, err on the side of **more descriptive**. Future readers — including yourself in six months — will thank you.

---

*These guidelines are inspired by principles from "Clean Code" by Robert C. Martin and decades of software engineering best practices. They are language-agnostic and apply equally to Python, JavaScript, Java, C#, Go, Rust, and any other language.*

## End of Guidelines
