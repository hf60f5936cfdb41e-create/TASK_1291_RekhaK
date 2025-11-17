# Task Processor CLI

A production-grade Python CLI tool for processing JSON files containing task items with strict validation.

## Features

- Reads and validates JSON files containing task items
- Strict input validation with detailed error messages
- Processes valid items and outputs results to JSON
- Comprehensive logging and error handling
- PEP8 compliant code

## Installation

No additional dependencies required beyond Python 3.6+.

For testing and linting:
```bash
pip install pytest flake8
```

## Usage

### Basic Command

```bash
python -m src.task_processor process --input <input_file> --output <output_file>
```

### Verbose Mode

Enable debug-level logging with the `-v` or `--verbose` flag:
```bash
python -m src.task_processor process --input <input_file> --output <output_file> --verbose
```

### Examples

**Process a valid input file:**
```bash
python -m src.task_processor process --input examples/valid.json --output output.json
```

**Attempt to process an invalid file (will return exit code 1):**
```bash
python -m src.task_processor process --input examples/invalid_duplicate_id.json --output output.json
```

## Input Format

The input JSON file must be an array of objects with the following structure:

```json
[
  {
    "id": 1,
    "name": "Task Name",
    "value": 100
  }
]
```

### Field Requirements

- `id` (integer, required): Unique identifier for the task
- `name` (string, required): Non-empty task name
- `value` (numeric, required): Integer or float value

## Output Format

Successful processing produces a JSON file with processed items:

```json
[
  {
    "id": 1,
    "name": "Task Name",
    "value": 100,
    "processed": true,
    "name_length": 9
  }
]
```

## Validation Rules

The tool validates:

1. **JSON Structure**: Must be valid JSON array
2. **Required Fields**: All items must have `id`, `name`, and `value`
3. **Type Checking**:
   - `id` must be an integer
   - `name` must be a non-empty string
   - `value` must be numeric (int or float, not boolean)
4. **Uniqueness**: All `id` values must be unique

## Exit Codes

- `0`: Success - input was valid and output was written
- `1`: Error - validation failed or other error occurred

## Example Files

The `examples/` directory contains sample files:

- `valid.json` - Valid input with multiple items
- `invalid_duplicate_id.json` - Invalid input with duplicate IDs
- `invalid_malformed.json` - Malformed JSON syntax
- `invalid_missing_field.json` - Item missing required field
- `invalid_wrong_type.json` - Item with wrong field type
- `invalid_empty_name.json` - Item with whitespace-only name
- `invalid_bool_id.json` - Item with boolean instead of integer id
- `invalid_bool_value.json` - Item with boolean instead of numeric value
- `invalid_not_array.json` - Input is not a JSON array

## Running Tests

```bash
pytest
```

Or with verbose output:
```bash
pytest -v
```

## Linting

```bash
flake8 src tests --max-line-length=100
```

## Project Structure

```
.
├── README.md
├── pytest.ini
├── src/
│   ├── __init__.py
│   ├── __main__.py
│   └── task_processor.py
├── tests/
│   ├── __init__.py
│   └── test_task_processor.py
└── examples/
    ├── valid.json
    ├── invalid_duplicate_id.json
    ├── invalid_malformed.json
    ├── invalid_missing_field.json
    ├── invalid_wrong_type.json
    ├── invalid_empty_name.json
    ├── invalid_bool_id.json
    ├── invalid_bool_value.json
    └── invalid_not_array.json
```

## License

This project is for evaluation purposes.
