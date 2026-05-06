#!/bin/bash
#
# Compare gemma4 quantization variants
# Tests Q8 (e4b), Q5, and Q4 for speed and quality
#

echo "======================================================================="
echo "GEMMA4 QUANTIZATION COMPARISON"
echo "======================================================================="
echo ""

# Check which models exist
echo "Available models:"
ollama list | grep gemma4
echo ""

MODELS=()

if ollama list | grep -q "gemma4:e4b"; then
    MODELS+=("gemma4:e4b")
fi

if ollama list | grep -q "gemma4:q5"; then
    MODELS+=("gemma4:q5")
fi

if ollama list | grep -q "gemma4:q4"; then
    MODELS+=("gemma4:q4")
fi

if [ ${#MODELS[@]} -eq 0 ]; then
    echo "❌ No gemma4 models found!"
    echo "Run: ./quantize_gemma4.sh first"
    exit 1
fi

echo "Testing ${#MODELS[@]} model(s): ${MODELS[@]}"
echo ""

# Test prompts
TEST_PROMPTS=(
    "What is 2+2?"
    "Explain photosynthesis in one sentence."
    "List 3 programming languages."
)

echo "Running comparison tests..."
echo "This will take a few minutes..."
echo ""

for MODEL in "${MODELS[@]}"; do
    echo "======================================================================="
    echo "Testing: $MODEL"
    echo "======================================================================="

    for i in "${!TEST_PROMPTS[@]}"; do
        PROMPT="${TEST_PROMPTS[$i]}"
        echo ""
        echo "[$((i+1))/${#TEST_PROMPTS[@]}] Prompt: \"$PROMPT\""
        echo "---"

        # Time the response
        START=$(date +%s.%N)

        RESPONSE=$(ollama run "$MODEL" "$PROMPT" 2>&1)

        END=$(date +%s.%N)
        ELAPSED=$(echo "$END - $START" | bc)

        echo "Response: $RESPONSE"
        echo "⏱️  Time: ${ELAPSED}s"
    done

    echo ""
done

echo ""
echo "======================================================================="
echo "SUMMARY"
echo "======================================================================="
echo ""
echo "Quality Assessment:"
echo "  - Check if responses are accurate and complete"
echo "  - Q8 (e4b) should be most accurate"
echo "  - Q5 should be very close to Q8"
echo "  - Q4 may have slightly lower quality"
echo ""
echo "Speed Assessment:"
echo "  - Q4 should be fastest"
echo "  - Q5 should be 20% faster than Q8"
echo "  - Q8 (e4b) is baseline"
echo ""
echo "Recommendation:"
echo "  - For vision/screen reading: Use Q8 (e4b) or Q5"
echo "  - For function calling: Q5 or Q4 work well"
echo "  - For maximum speed: Q4"
echo "======================================================================="
