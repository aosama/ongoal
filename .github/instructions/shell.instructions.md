---
description: 'Shell scripting best practices and conventions for bash, sh, zsh, and other shells'
applyTo: '**/*.sh'
---

# Shell Scripting Guidelines

Instructions for writing clean, safe, and maintainable shell scripts for bash, sh, zsh, and other shells.

## General Principles

- Generate code that is clean, simple, and concise
- Ensure scripts are easily readable and understandable
- Add comments where helpful for understanding how the script works
- Generate concise and simple echo outputs to provide execution status
- Avoid unnecessary echo output and excessive logging
- Use shellcheck for static analysis when available
- Assume scripts may be developer automation, CI orchestration, or operational runtime entrypoints. Treat them as production-adjacent unless the repository clearly marks them as disposable one-off helpers.
- Prefer safe expansions: double-quote variable references (`"$var"`), use `${var}` for clarity, and avoid `eval`
- Match the script syntax to the declared interpreter. If the shebang is `sh`, keep the script POSIX-compliant. If the script requires Bash or Zsh features (`[[ ]]`, arrays, `local`, `pipefail`), declare that interpreter explicitly in the shebang.
- Prefer POSIX shell constructs when the script is intended to run across multiple shells, and use shell-specific features only when the operational requirement is clear.
- Choose reliable parsers for structured data instead of ad-hoc text processing

## Error Handling & Safety

- Use `set -eu` as the portable fail-fast baseline.
- Add `set -o pipefail` only when the declared interpreter supports it, such as Bash, Zsh, and Ksh.
- If `pipefail` is unavailable, avoid pipelines that can hide upstream failures, or split the pipeline into explicit steps and validate each step.
- Validate all required parameters before execution
- Provide clear error messages with context
- Use `trap` to clean up temporary resources or handle unexpected exits when the script terminates
- Declare immutable values with `readonly` (or `declare -r`) to prevent accidental reassignment
- Use `mktemp` to create temporary files or directories safely and ensure they are removed in your cleanup handler

## Script Structure

- Start with a clear shebang that matches the required interpreter, such as `#!/usr/bin/env sh` for portable scripts or `#!/usr/bin/env bash` when Bash features are required
- Include a header comment explaining the script's purpose
- Define default values for all variables at the top
- Use functions for reusable code blocks
- Create reusable functions instead of repeating similar blocks of code
- Keep the main execution flow clean and readable

## Working with JSON and YAML

- Prefer dedicated parsers (`jq` for JSON, `yq` for YAML—or `jq` on JSON converted via `yq`) over ad-hoc text processing with `grep`, `awk`, or shell string splitting
- When `jq`/`yq` are unavailable or not appropriate, choose the next most reliable parser available in your environment, and be explicit about how it should be used safely
- Validate that required fields exist and handle missing/invalid data paths explicitly (e.g., by checking `jq` exit status or using `// empty`)
- Quote jq/yq filters to prevent shell expansion and prefer `--raw-output` when you need plain strings
- Treat parser errors as fatal: combine with `set -eu` plus `pipefail` when supported, or test command success before using results
- Document parser dependencies at the top of the script and fail fast with a helpful message if `jq`/`yq` (or alternative tools) are required but not installed

```sh
#!/usr/bin/env sh

# ============================================================================
# Script Description Here
# ============================================================================

set -eu

# Enable pipefail when the active shell supports it.
if (set -o pipefail) 2>/dev/null; then
    set -o pipefail
fi

cleanup() {
    # Remove temporary resources or perform other teardown steps as needed
    if [ -n "${TEMP_DIR:-}" ] && [ -d "${TEMP_DIR}" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

trap cleanup 0

# Default values
RESOURCE_GROUP=""
REQUIRED_PARAM=""
OPTIONAL_PARAM="default-value"
readonly SCRIPT_NAME="$(basename "$0")"

TEMP_DIR=""

# Functions
usage() {
    echo "Usage: ${SCRIPT_NAME} [OPTIONS]"
    echo "Options:"
    echo "  -g, --resource-group   Resource group (required)"
    echo "  -h, --help            Show this help"
    exit 0
}

validate_requirements() {
    if [ -z "${RESOURCE_GROUP}" ]; then
        echo "Error: Resource group is required" >&2
        exit 1
    fi
}

main() {
    validate_requirements

    TEMP_DIR="$(mktemp -d)"
    if [ ! -d "${TEMP_DIR}" ]; then
        echo "Error: failed to create temporary directory" >&2
        exit 1
    fi

    echo "============================================================================"
    echo "Script Execution Started"
    echo "============================================================================"

    # Main logic here

    echo "============================================================================"
    echo "Script Execution Completed"
    echo "============================================================================"
}

# Parse arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        -g|--resource-group)
            if [ "$#" -lt 2 ]; then
                echo "Error: --resource-group requires a value" >&2
                exit 1
            fi
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Execute main function
main "$@"
