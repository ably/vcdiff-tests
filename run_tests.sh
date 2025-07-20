#!/bin/bash

# VCDIFF Test Runner
# Automatically discovers and runs all tests against xdelta3

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test statistics
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check for xdelta3
if ! command -v xdelta3 &> /dev/null; then
    echo -e "${RED}Error: xdelta3 is not installed or not in PATH${NC}"
    echo "Please install xdelta3 to run tests"
    exit 1
fi

# Check for jq for JSON parsing
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq not found. Metadata validation will be limited${NC}"
    HAS_JQ=false
else
    HAS_JQ=true
fi

echo -e "${BLUE}VCDIFF Test Suite Runner${NC}"
echo "Using xdelta3: $(which xdelta3)"
echo "Test directory: $SCRIPT_DIR"
echo ""

# Function to parse metadata
parse_metadata() {
    local metadata_file="$1"
    if [[ -f "$metadata_file" ]] && [[ "$HAS_JQ" == true ]]; then
        jq -r '.' "$metadata_file" 2>/dev/null || echo "{}"
    else
        echo "{}"
    fi
}

# Function to get metadata field
get_metadata_field() {
    local metadata="$1"
    local field="$2"
    local default="$3"
    
    if [[ "$HAS_JQ" == true ]] && [[ "$metadata" != "{}" ]]; then
        echo "$metadata" | jq -r ".$field // \"$default\"" 2>/dev/null || echo "$default"
    else
        echo "$default"
    fi
}

# Function to run a single test
run_test() {
    local test_dir="$1"
    local category="$2"
    local test_name="$(basename "$test_dir")"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Running $category/$test_name... "
    
    # Check required files
    local source_file="$test_dir/source"
    local target_file="$test_dir/target"
    local delta_file="$test_dir/delta.vcdiff"
    local metadata_file="$test_dir/metadata.json"
    
    if [[ ! -f "$source_file" ]] || [[ ! -f "$target_file" ]] || [[ ! -f "$delta_file" ]]; then
        echo -e "${YELLOW}SKIP (missing files)${NC}"
        SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
        return
    fi
    
    # Parse metadata
    local metadata=$(parse_metadata "$metadata_file")
    local expected_behavior=$(get_metadata_field "$metadata" "expected_behavior" "success")
    local test_description=$(get_metadata_field "$metadata" "name" "$test_name")
    
    # Create temporary files
    local temp_dir=$(mktemp -d)
    local result_file="$temp_dir/result"
    local xdelta_output="$temp_dir/xdelta_output"
    local xdelta_error="$temp_dir/xdelta_error"
    
    # Run xdelta3 decode
    local xdelta_exit_code=0
    xdelta3 -d -s "$source_file" "$delta_file" "$result_file" > "$xdelta_output" 2> "$xdelta_error" || xdelta_exit_code=$?
    
    # Check results based on expected behavior
    case "$expected_behavior" in
        "success")
            if [[ $xdelta_exit_code -eq 0 ]]; then
                # Compare result with expected target
                if cmp -s "$result_file" "$target_file"; then
                    echo -e "${GREEN}PASS${NC}"
                    PASSED_TESTS=$((PASSED_TESTS + 1))
                else
                    echo -e "${RED}FAIL (output mismatch)${NC}"
                    echo "  Expected target differs from xdelta3 result"
                    FAILED_TESTS=$((FAILED_TESTS + 1))
                fi
            else
                echo -e "${RED}FAIL (xdelta3 error)${NC}"
                echo "  xdelta3 exit code: $xdelta_exit_code"
                if [[ -s "$xdelta_error" ]]; then
                    echo "  Error: $(head -n1 "$xdelta_error")"
                fi
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
            ;;
        "error")
            if [[ $xdelta_exit_code -ne 0 ]]; then
                echo -e "${GREEN}PASS (correctly rejected)${NC}"
                PASSED_TESTS=$((PASSED_TESTS + 1))
            else
                echo -e "${RED}FAIL (should have been rejected)${NC}"
                echo "  xdelta3 should have failed but succeeded"
                FAILED_TESTS=$((FAILED_TESTS + 1))
            fi
            ;;
        *)
            echo -e "${YELLOW}SKIP (unknown expected behavior: $expected_behavior)${NC}"
            SKIPPED_TESTS=$((SKIPPED_TESTS + 1))
            ;;
    esac
    
    # Clean up
    rm -rf "$temp_dir"
}

# Function to run tests in a category
run_category() {
    local category_dir="$1"
    local category_name="$(basename "$category_dir")"
    
    if [[ ! -d "$category_dir" ]]; then
        echo -e "${YELLOW}Category $category_name not found, skipping${NC}"
        return
    fi
    
    echo -e "${BLUE}=== $category_name tests ===${NC}"
    
    local test_count=0
    local processed_tests=()
    
    # Find all test directories (containing delta.vcdiff) and avoid duplicates
    while IFS= read -r -d '' test_dir; do
        if [[ -f "$test_dir/delta.vcdiff" ]]; then
            # Check if we've already processed this test
            local test_already_processed=false
            for processed in "${processed_tests[@]}"; do
                if [[ "$processed" == "$test_dir" ]]; then
                    test_already_processed=true
                    break
                fi
            done
            
            if [[ "$test_already_processed" == false ]]; then
                local relative_path="${test_dir#$category_dir/}"
                if [[ "$relative_path" == "" ]]; then
                    relative_path="$category_name"
                fi
                run_test "$test_dir" "$relative_path"
                processed_tests+=("$test_dir")
                test_count=$((test_count + 1))
            fi
        fi
    done < <(find "$category_dir" -name "delta.vcdiff" -type f -exec dirname {} \; | sort -u | tr '\n' '\0')
    
    if [[ $test_count -eq 0 ]]; then
        echo -e "${YELLOW}No tests found in $category_name${NC}"
    fi
    
    echo ""
}

# Main execution
echo -e "${BLUE}Discovering and running tests...${NC}"
echo ""

# Run each category
run_category "$SCRIPT_DIR/targeted-positive"
run_category "$SCRIPT_DIR/targeted-negative" 
run_category "$SCRIPT_DIR/general-positive"
run_category "$SCRIPT_DIR/fuzz"

# Print summary
echo -e "${BLUE}=== Test Summary ===${NC}"
echo "Total tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
echo -e "Skipped: ${YELLOW}$SKIPPED_TESTS${NC}"

if [[ $FAILED_TESTS -eq 0 ]]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}$FAILED_TESTS test(s) failed${NC}"
    exit 1
fi