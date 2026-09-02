#!/bin/bash
# Detects HTML note files not yet referenced in index.html
# Outputs JSON additionalContext if any are found

PROJECT_DIR="/home/isha/Desktop/CODE/personal-os/AI"
INDEX="$PROJECT_DIR/index.html"

[ -f "$INDEX" ] || exit 0

NEW_FILES=""
while IFS= read -r file; do
    rel=$(realpath --relative-to="$PROJECT_DIR" "$file")
    if ! grep -qF "data-file=\"$rel\"" "$INDEX" 2>/dev/null; then
        NEW_FILES="${NEW_FILES}  - ${rel}"$'\n'
    fi
done < <(find "$PROJECT_DIR" -name "*.html" ! -name "index.html" -type f | sort)

if [ -n "$NEW_FILES" ]; then
    ctx="New HTML note files exist in the project but are NOT yet in index.html:"$'\n'"${NEW_FILES}"$'\n'"Adapt them into index.html proactively."
    jq -n --arg ctx "$ctx" '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":$ctx}}'
fi
