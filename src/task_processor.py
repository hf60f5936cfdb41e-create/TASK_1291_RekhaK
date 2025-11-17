#!/usr/bin/env python3
"""
Task Processor CLI Tool

A production-grade CLI tool for processing JSON files containing task items.
Validates input strictly and outputs processed results.
"""

import argparse
import json
import logging
import sys
from typing import Any

# Module logger (configured later by setup_logging)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: If True, set DEBUG level; otherwise INFO level.
    """
    level = logging.DEBUG if verbose else logging.INFO
    format_str = '%(asctime)s - %(levelname)s - %(message)s'

    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt='%Y-%m-%d %H:%M:%S'
    )


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_item(item: Any, index: int) -> dict:
    """
    Validate a single item from the input list.

    Args:
        item: The item to validate
        index: The index of the item in the list (for error messages)

    Returns:
        The validated item as a dictionary

    Raises:
        ValidationError: If the item is invalid
    """
    if not isinstance(item, dict):
        raise ValidationError(f"Item at index {index} is not an object")

    # Check required fields
    required_fields = ['id', 'name', 'value']
    for field in required_fields:
        if field not in item:
            raise ValidationError(f"Item at index {index} is missing required field '{field}'")

    # Validate id (integer, but not bool since bool is subclass of int)
    if isinstance(item['id'], bool) or not isinstance(item['id'], int):
        raise ValidationError(
            f"Item at index {index}: 'id' must be an integer, got {type(item['id']).__name__}"
        )

    # Validate name (non-empty string)
    if not isinstance(item['name'], str):
        raise ValidationError(
            f"Item at index {index}: 'name' must be a string, got {type(item['name']).__name__}"
        )
    if not item['name'].strip():
        raise ValidationError(f"Item at index {index}: 'name' must be a non-empty string")

    # Validate value (numeric - int or float)
    if not isinstance(item['value'], (int, float)):
        raise ValidationError(
            f"Item at index {index}: 'value' must be numeric, got {type(item['value']).__name__}"
        )
    # Check for boolean (which is a subclass of int in Python)
    if isinstance(item['value'], bool):
        raise ValidationError(f"Item at index {index}: 'value' must be numeric, got bool")

    return {
        'id': item['id'],
        'name': item['name'],
        'value': item['value']
    }


def validate_input(data: Any) -> list:
    """
    Validate the entire input data structure.

    Args:
        data: The parsed JSON data

    Returns:
        A list of validated items

    Raises:
        ValidationError: If the data is invalid
    """
    if not isinstance(data, list):
        raise ValidationError("Input must be a JSON array")

    validated_items = []
    seen_ids = set()

    for index, item in enumerate(data):
        validated_item = validate_item(item, index)

        # Check for duplicate IDs
        if validated_item['id'] in seen_ids:
            raise ValidationError(f"Duplicate id found: {validated_item['id']}")
        seen_ids.add(validated_item['id'])

        validated_items.append(validated_item)

    return validated_items


def process_items(items: list) -> list:
    """
    Process the validated items.

    Args:
        items: List of validated items

    Returns:
        Processed items with additional metadata
    """
    processed = []
    for item in items:
        processed_item = {
            'id': item['id'],
            'name': item['name'],
            'value': item['value'],
            'processed': True,
            'name_length': len(item['name'])
        }
        processed.append(processed_item)

    logger.info(f"Successfully processed {len(processed)} items")
    return processed


def read_input_file(input_path: str) -> Any:
    """
    Read and parse the input JSON file.

    Args:
        input_path: Path to the input file

    Returns:
        Parsed JSON data

    Raises:
        ValidationError: If file cannot be read or parsed
    """
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Successfully read input file: {input_path}")
        return data
    except FileNotFoundError:
        raise ValidationError(f"Input file not found: {input_path}")
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON in input file: {e}")
    except PermissionError:
        raise ValidationError(f"Permission denied reading file: {input_path}")
    except Exception as e:
        raise ValidationError(f"Error reading input file: {e}")


def write_output_file(output_path: str, data: list) -> None:
    """
    Write processed data to output JSON file.

    Args:
        output_path: Path to the output file
        data: Data to write

    Raises:
        ValidationError: If file cannot be written
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Successfully wrote output file: {output_path}")
    except PermissionError:
        raise ValidationError(f"Permission denied writing to file: {output_path}")
    except Exception as e:
        raise ValidationError(f"Error writing output file: {e}")


def process_command(input_path: str, output_path: str) -> int:
    """
    Execute the process command.

    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Read input
        data = read_input_file(input_path)

        # Validate input
        validated_items = validate_input(data)

        # Process items
        processed_items = process_items(validated_items)

        # Write output
        write_output_file(output_path, processed_items)

        return 0

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog='task_processor',
        description='Process JSON files containing task items'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process a JSON input file')
    process_parser.add_argument(
        '--input',
        required=True,
        dest='input_file',
        help='Path to input JSON file'
    )
    process_parser.add_argument(
        '--output',
        required=True,
        dest='output_file',
        help='Path to output JSON file'
    )
    process_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose (debug) logging'
    )

    return parser


def main(args: list = None) -> int:
    """
    Main entry point for the CLI tool.

    Args:
        args: Command line arguments (defaults to sys.argv)

    Returns:
        Exit code
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.command is None:
        parser.print_help()
        return 1

    if parsed_args.command == 'process':
        # Setup logging based on verbose flag
        verbose = getattr(parsed_args, 'verbose', False)
        setup_logging(verbose=verbose)
        return process_command(parsed_args.input_file, parsed_args.output_file)

    return 1


if __name__ == '__main__':
    sys.exit(main())
