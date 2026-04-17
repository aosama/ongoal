---
description: "Mandatory congruency instruction for authoring and full-file review before commit or push"
applyTo: "**"
---

# Congruency Instruction

## Table of Contents

- Purpose
- Authoring-Time Requirement
- Required Trigger Points
- Required Workflow
- Congruency Checklist
- Completion Gate

## Purpose

Require coding agents to adhere to this congruency instruction while writing any code or content, and require a full-file congruency review of every changed file before any commit or push.

This instruction applies to code and non-code content, including Markdown, configuration, shell scripts, and workflow files.

## Authoring-Time Requirement

Apply this congruency checklist continuously while writing and editing, not only at the end of the task.

- Before writing, choose names, interfaces, and structure that communicate clear intent.
- While writing, keep comments and docstrings congruent with behavior and contracts.
- As soon as an inconsistency is noticed, remediate it in the same edit pass.

## Required Trigger Points

Run this review when any of the following are true:

- You are about to write new code or content.
- You edited files in this task.
- You are about to commit.
- You are about to push.

## Required Workflow

1. During authoring, apply the congruency checklist continuously to each changed area.
2. Before commit or push, list changed files using `git status` or an equivalent change listing tool.
3. Read each changed file in full, not only the diff.
4. Re-apply the congruency checklist at full-file scope.
5. Remediate issues directly in source files.
6. Run quality gates and fix remaining errors.

## Congruency Checklist

For each changed file, verify and remediate all of the following:

### Naming

- Variable Names: Does the variable name communicate its purpose, type, and what it contains or is used for?
- Function Names: Does the function name communicate its purpose, return type, and side effects?
- Constants Names: Does the constant name communicate its purpose, type and value?
- Types Names: Does the type name communicate its purpose, structure and usage?

### Comments and Docstrings

- Comments in unison should tell a story of what the code is doing, why it does it, and any constraints or edge cases.
- Docstrings should accurately describe the intent, parameters, return values, and behavior of functions and classes.

### Public API and Documentation

- Public API: method signatures, parameter names, and return types should be consistent with their documentation and intended use.

### Validation and Errors

- Validation checks should be fail-fast, and error messages should be explicit, informative, and consistent across the codebase.

## Completion Gate

Do not commit or push until all changed files were reviewed in full and congruency fixes are complete.

Do not mark a task complete if this instruction was not followed during authoring and at pre-commit review time.
