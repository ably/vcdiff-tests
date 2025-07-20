# VCDIFF Test Suite

This repository contains a comprehensive test suite for VCDIFF (RFC 3284) decoders, organized into three categories of tests to ensure robust implementation validation.

## Test Categories

### 1. Targeted Positive Tests (`targeted-positive/`)
Test cases constructed to exercise specific functionality and code paths in the decoder.

- **Basic Operations**: Empty files, content changes, duplications, unchanged files
- **Varint Boundary Tests**: Tests for all varint encoding boundaries (0, 127, 128, 16383, 16384, 2097151, 2097152) across ADD, COPY, and RUN instructions (21 tests total)
- **Codetable Tests**: Complete coverage of all VCDIFF codetable entries (0-255):
  - Entry 0: RUN instructions 
  - Entries 1-18: ADD instructions
  - Entries 19-162: COPY instructions
  - Entries 163-234: Combined ADD+COPY (modes 0-5)
  - Entries 235-246: Combined ADD+COPY (modes 6-8) 
  - Entries 247-255: Combined COPY+ADD
- **Address Cache Tests**: Near cache, same cache, different addressing modes
- **Checksum Tests**: VCD_ADLER32 validation
- **Edge Cases**: Boundary conditions, minimum/maximum values

### 2. Targeted Negative Tests (`targeted-negative/`)
Test cases that should be rejected by the decoder due to invalid inputs.

- **Invalid Headers**: Wrong magic bytes, unsupported versions
- **Malformed Windows**: Invalid indicators, impossible sizes
- **Bad Instructions**: Invalid instruction codes, out-of-bounds references
- **Checksum Failures**: Incorrect Adler32 checksums
- **Format Violations**: Truncated files, invalid varints

### 3. General Positive Tests (`general-positive/`)
Valid decoding tests with systematically generated content and modifications (~25% file changes).

- **Base File Types**: 
  - 64 bytes random binary data
  - 1024 bytes random binary data  
  - 64KB random binary data
  - 1KB structured JSON data
  - 64KB structured JSON data
- **Modification Types** (4 per base file = 20 tests total):
  - **append**: Add data at end (~25% of original size)
  - **delete**: Remove data from random location (~25% of original size)
  - **insert**: Insert data at random location (~25% of original size) 
  - **modify**: Change data in-place (~25% of original size)
- **JSON Preservation**: JSON modifications maintain valid JSON structure

## Test Format

Each test case consists of:
- `source` - Original file (may be empty)
- `target` - Expected result after applying delta
- `delta.vcdiff` - VCDIFF delta file
- `metadata.json` - Test description and expected behavior

## Test Statistics

The current test suite includes **85 tests** across all categories:
- **32 targeted-positive tests**: 4 basic operations + 21 varint boundary tests + 6 codetable tests + 1 empty files test
- **20 general-positive tests**: 5 base file types × 4 modification types each
- **33 targeted-negative tests**: Comprehensive invalid input validation

### Varint Boundary Tests (21 tests)
- **ADD instruction tests** (7): `varint_add_0` through `varint_add_2097152`
- **COPY instruction tests** (7): `varint_copy_0` through `varint_copy_2097152`  
- **RUN instruction tests** (7): `varint_run_0` through `varint_run_2097152`

### Codetable Tests (6 tests)
- `codetable_entry_0`: RUN instruction (entry 0)
- `codetable_entries_1_18`: ADD instructions (entries 1-18)
- `codetable_entries_19_162`: COPY instructions (entries 19-162)
- `codetable_entries_163_234`: Combined ADD+COPY with modes 0-5 (entries 163-234)
- `codetable_entries_235_246`: Combined ADD+COPY with modes 6-8 (entries 235-246)
- `codetable_entries_247_255`: Combined COPY+ADD (entries 247-255)

### General Positive Tests (20 tests)
- **Binary file tests** (12): 3 sizes × 4 modifications each:
  - `64_bytes_random_append/delete/insert/modify`
  - `1024_bytes_random_append/delete/insert/modify`  
  - `64k_bytes_random_append/delete/insert/modify`
- **JSON file tests** (8): 2 sizes × 4 modifications each:
  - `1k_json_random_append/delete/insert/modify`
  - `64k_json_random_append/delete/insert/modify`

### Targeted Negative Tests (33 tests)
Comprehensive invalid input tests covering all error handling paths:

- **Header Format Violations** (11 tests):
  - `truncated_magic_0_bytes` through `truncated_magic_3_bytes`: Incomplete magic bytes
  - `invalid_magic_0` through `invalid_magic_3`: Wrong magic byte sequences
  - `missing_version`, `invalid_version`: Version field errors
  - `missing_header_indicator`: Truncated header
  
- **Window Header Violations** (7 tests):
  - `missing_window_indicator`: Missing window start
  - `invalid_window_indicator`: Reserved bits set
  - `truncated_source_length/position/delta_length/target_length`: Incomplete varints
  - `unterminated_varint`: Varints with continuation bit never cleared

- **Delta Section Violations** (5 tests):
  - `truncated_data/instructions/addresses_length`: Section length varint errors
  - `missing_data_section`, `data_section_too_short`: Data availability mismatches

- **Instruction Violations** (5 tests):
  - `add_data_overrun`, `add_size_truncated`: ADD instruction boundary errors
  - `copy_no_source`, `copy_address_oob`: COPY instruction validation
  - `run_missing_data`: RUN instruction data requirements

- **Address Cache Violations** (2 tests):
  - `invalid_cache_mode`: Cache addressing mode > 8
  - `uninitialized_near_cache`: References to unpopulated cache slots

- **Format Structure Violations** (2 tests):
  - `second_window_truncated`: Multiple window handling
  - `section_length_inconsistency`: Length field validation

- **Legacy Test** (1 test):
  - `invalid-header`: Original header validation test

## Test Generation

All valid VCDIFF files are generated using xdelta3 to ensure compliance with RFC 3284.
Test cases are validated by applying the delta with xdelta3 and verifying the result matches the expected target.

### Negative Test Generation
Invalid VCDIFF files are systematically constructed to trigger specific error conditions:
- **Truncation**: Files cut at critical parsing points
- **Corruption**: Invalid values in header fields, varints, and instruction codes  
- **Boundary violations**: Out-of-bounds references, buffer overruns
- **Format violations**: Inconsistent length fields, reserved bits set

## Code Coverage Analysis

The test suite includes coverage analysis tools to measure error handling path coverage:

```bash
# Run coverage analysis
./analyze_coverage.sh
```

**Coverage Targets:**
- **Parser coverage**: All header, window, and delta parsing paths
- **Error path coverage**: All validation and bounds checking code
- **Instruction coverage**: All 256 codetable entries and addressing modes
- **Minimum target**: >95% line coverage in decoder and parser logic

## Usage

Tests can be run against any VCDIFF decoder implementation to validate:
- Correct parsing of VCDIFF format
- Proper error handling
- Robustness against malformed input
- Performance with various input sizes