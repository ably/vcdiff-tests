# VCDIFF Test Runner

This directory contains a comprehensive test runner script that validates VCDIFF decoder implementations against xdelta3.

## Prerequisites

- **xdelta3**: Required for running tests
- **jq**: Optional, for enhanced metadata parsing
- **bash**: Version 4.0 or higher

### Installing Dependencies

**macOS (Homebrew):**
```bash
brew install xdelta jq
```

**Ubuntu/Debian:**
```bash
sudo apt-get install xdelta3 jq
```

**CentOS/RHEL:**
```bash
sudo yum install xdelta jq
```

## Usage

### Run All Tests
```bash
./run_tests.sh
```

### Understanding Test Results

The script automatically discovers and runs tests in four categories:

1. **targeted-positive**: Tests that should succeed
   - Validates that xdelta3 can decode the VCDIFF file
   - Compares the result with the expected target file
   - Reports PASS if files match, FAIL if they don't

2. **targeted-negative**: Tests that should fail
   - Validates that xdelta3 properly rejects invalid VCDIFF files
   - Reports PASS if xdelta3 fails (as expected), FAIL if it succeeds

3. **general-positive**: Random content tests (when available)
   - Same validation as targeted-positive tests

4. **fuzz**: Corruption tests (when available)
   - Tests decoder robustness against malformed input

### Test Discovery

The script automatically finds tests by looking for directories containing:
- `source` - Source file
- `target` - Expected result file  
- `delta.vcdiff` - VCDIFF delta file
- `metadata.json` - Test description (optional)

### Output Format

```
=== targeted-positive tests ===
Running basic-operations/unchanged-file... PASS
Running basic-operations/duplicated-content... PASS

=== Test Summary ===
Total tests: 6
Passed: 6
Failed: 0 
Skipped: 0
```

### Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

### Metadata Support

If `metadata.json` is present and `jq` is installed, the script uses:
- `expected_behavior`: "success" or "error"
- `name`: Test description for output
- Other fields are available for future enhancements

## Troubleshooting

### xdelta3 not found
```
Error: xdelta3 is not installed or not in PATH
```
Install xdelta3 using your package manager.

### Permission denied
```bash
chmod +x run_tests.sh
```

### No tests found
Ensure test directories contain the required files (source, target, delta.vcdiff).

## Adding New Tests

1. Create a new directory in the appropriate category
2. Add the required files: `source`, `target`, `delta.vcdiff`
3. Optionally add `metadata.json` with test description
4. Run the test script to validate

Example metadata.json:
```json
{
  "name": "Test Description",
  "description": "Detailed explanation",
  "category": "basic-operations",
  "expected_behavior": "success"
}
```