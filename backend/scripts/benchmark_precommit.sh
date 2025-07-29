#!/bin/bash

set -e

# Activate virtual environment if exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "=== Measuring pre-commit hook times ==="
echo

declare -a TIMES=()
declare -a HOOKS=("ruff" "bandit" "pytest")

# Function to measure execution time
measure_hook() {
    local hook=$1
    echo ">>> Running $hook..."
    
    START=$(date +%s.%N)
    if pre-commit run $hook --all-files 2>&1; then
        STATUS="✓"
    else
        STATUS="✗"
    fi
    END=$(date +%s.%N)
    
    DURATION=$(python3 -c "print(f'{float($END) - float($START):.3f}')")
    TIMES+=("$DURATION")
    
    echo ">>> $hook took ${DURATION}s [$STATUS]"
    echo
}

# Run measurements
for hook in "${HOOKS[@]}"; do
    measure_hook "$hook"
done

# Summary
echo "=== Summary ==="
for i in "${!HOOKS[@]}"; do
    echo "${HOOKS[$i]}: ${TIMES[$i]}s"
done

TOTAL=$(python3 -c "import sys; times = sys.argv[1:]; print(f'{sum(float(t) for t in times):.3f}')" ${TIMES[@]})
echo "Total: ${TOTAL}s"
echo "=== Done ==="