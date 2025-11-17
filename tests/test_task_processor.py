#!/usr/bin/env python3
"""
Tests for task_processor CLI tool.

Includes unit tests and integration tests.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from src.task_processor import (
    ValidationError,
    create_parser,
    main,
    process_command,
    process_items,
    read_input_file,
    setup_logging,
    validate_input,
    validate_item,
    write_output_file,
)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_default(self):
        """Test setup_logging with default (INFO) level."""
        import logging
        # Clear existing handlers to allow basicConfig to work
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)  # Reset to default

        setup_logging(verbose=False)
        assert root_logger.level == logging.INFO

    def test_setup_logging_verbose(self):
        """Test setup_logging with verbose (DEBUG) level."""
        import logging
        # Clear existing handlers to allow basicConfig to work
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.setLevel(logging.WARNING)  # Reset to default

        setup_logging(verbose=True)
        assert root_logger.level == logging.DEBUG


class TestValidateItem:
    """Tests for validate_item function."""

    def test_valid_item(self):
        """Test validation of a valid item."""
        item = {'id': 1, 'name': 'Test', 'value': 100}
        result = validate_item(item, 0)
        assert result == {'id': 1, 'name': 'Test', 'value': 100}

    def test_valid_item_with_float_value(self):
        """Test validation with float value."""
        item = {'id': 1, 'name': 'Test', 'value': 99.5}
        result = validate_item(item, 0)
        assert result['value'] == 99.5

    def test_valid_item_with_negative_value(self):
        """Test validation with negative value."""
        item = {'id': 1, 'name': 'Test', 'value': -50}
        result = validate_item(item, 0)
        assert result['value'] == -50

    def test_invalid_not_dict(self):
        """Test that non-dict items are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_item("not a dict", 0)
        assert "not an object" in str(exc_info.value)

    def test_missing_id_field(self):
        """Test that missing id field is detected."""
        item = {'name': 'Test', 'value': 100}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "missing required field 'id'" in str(exc_info.value)

    def test_missing_name_field(self):
        """Test that missing name field is detected."""
        item = {'id': 1, 'value': 100}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "missing required field 'name'" in str(exc_info.value)

    def test_missing_value_field(self):
        """Test that missing value field is detected."""
        item = {'id': 1, 'name': 'Test'}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "missing required field 'value'" in str(exc_info.value)

    def test_id_not_integer(self):
        """Test that non-integer id is rejected."""
        item = {'id': '1', 'name': 'Test', 'value': 100}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "'id' must be an integer" in str(exc_info.value)

    def test_name_not_string(self):
        """Test that non-string name is rejected."""
        item = {'id': 1, 'name': 123, 'value': 100}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "'name' must be a string" in str(exc_info.value)

    def test_name_empty_string(self):
        """Test that empty name is rejected."""
        item = {'id': 1, 'name': '', 'value': 100}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "'name' must be a non-empty string" in str(exc_info.value)

    def test_name_whitespace_only(self):
        """Test that whitespace-only name is rejected."""
        item = {'id': 1, 'name': '   ', 'value': 100}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "'name' must be a non-empty string" in str(exc_info.value)

    def test_value_not_numeric(self):
        """Test that non-numeric value is rejected."""
        item = {'id': 1, 'name': 'Test', 'value': 'hundred'}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "'value' must be numeric" in str(exc_info.value)

    def test_value_boolean_rejected(self):
        """Test that boolean value is rejected."""
        item = {'id': 1, 'name': 'Test', 'value': True}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "'value' must be numeric" in str(exc_info.value)

    def test_id_boolean_rejected(self):
        """Test that boolean id is rejected."""
        item = {'id': True, 'name': 'Test', 'value': 100}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "'id' must be an integer" in str(exc_info.value)

    def test_id_boolean_false_rejected(self):
        """Test that boolean False id is rejected."""
        item = {'id': False, 'name': 'Test', 'value': 100}
        with pytest.raises(ValidationError) as exc_info:
            validate_item(item, 0)
        assert "'id' must be an integer" in str(exc_info.value)

    def test_valid_item_with_zero_value(self):
        """Test validation with zero value."""
        item = {'id': 1, 'name': 'Test', 'value': 0}
        result = validate_item(item, 0)
        assert result['value'] == 0

    def test_valid_item_with_zero_id(self):
        """Test validation with zero id."""
        item = {'id': 0, 'name': 'Test', 'value': 100}
        result = validate_item(item, 0)
        assert result['id'] == 0


class TestValidateInput:
    """Tests for validate_input function."""

    def test_valid_input(self):
        """Test validation of valid input."""
        data = [
            {'id': 1, 'name': 'First', 'value': 10},
            {'id': 2, 'name': 'Second', 'value': 20},
        ]
        result = validate_input(data)
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[1]['id'] == 2

    def test_empty_list(self):
        """Test that empty list is valid."""
        result = validate_input([])
        assert result == []

    def test_not_a_list(self):
        """Test that non-list input is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_input({'id': 1, 'name': 'Test', 'value': 100})
        assert "Input must be a JSON array" in str(exc_info.value)

    def test_duplicate_ids(self):
        """Test that duplicate IDs are detected."""
        data = [
            {'id': 1, 'name': 'First', 'value': 10},
            {'id': 1, 'name': 'Duplicate', 'value': 20},
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate_input(data)
        assert "Duplicate id found: 1" in str(exc_info.value)

    def test_multiple_duplicates(self):
        """Test with multiple items having same ID."""
        data = [
            {'id': 1, 'name': 'First', 'value': 10},
            {'id': 2, 'name': 'Second', 'value': 20},
            {'id': 1, 'name': 'Duplicate', 'value': 30},
        ]
        with pytest.raises(ValidationError) as exc_info:
            validate_input(data)
        assert "Duplicate id found: 1" in str(exc_info.value)


class TestProcessItems:
    """Tests for process_items function."""

    def test_process_items(self):
        """Test processing of items."""
        items = [
            {'id': 1, 'name': 'First', 'value': 10},
            {'id': 2, 'name': 'Second', 'value': 20},
        ]
        result = process_items(items)
        assert len(result) == 2
        assert result[0]['processed'] is True
        assert result[0]['name_length'] == 5
        assert result[1]['name_length'] == 6

    def test_empty_list(self):
        """Test processing empty list."""
        result = process_items([])
        assert result == []


class TestFileOperations:
    """Tests for file read/write operations."""

    def test_read_valid_file(self):
        """Test reading a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{'id': 1, 'name': 'Test', 'value': 100}], f)
            temp_path = f.name

        try:
            result = read_input_file(temp_path)
            assert result == [{'id': 1, 'name': 'Test', 'value': 100}]
        finally:
            os.unlink(temp_path)

    def test_read_nonexistent_file(self):
        """Test reading non-existent file."""
        with pytest.raises(ValidationError) as exc_info:
            read_input_file('/nonexistent/path/file.json')
        assert "Input file not found" in str(exc_info.value)

    def test_read_malformed_json(self):
        """Test reading malformed JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            temp_path = f.name

        try:
            with pytest.raises(ValidationError) as exc_info:
                read_input_file(temp_path)
            assert "Invalid JSON" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_write_output_file(self):
        """Test writing output file."""
        data = [{'id': 1, 'name': 'Test', 'value': 100}]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            write_output_file(temp_path, data)

            with open(temp_path, 'r') as f:
                result = json.load(f)
            assert result == data
        finally:
            os.unlink(temp_path)


class TestProcessCommand:
    """Tests for process_command function."""

    def test_successful_processing(self):
        """Test successful end-to-end processing."""
        input_data = [
            {'id': 1, 'name': 'First', 'value': 10},
            {'id': 2, 'name': 'Second', 'value': 20},
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            exit_code = process_command(input_path, output_path)
            assert exit_code == 0

            with open(output_path, 'r') as f:
                result = json.load(f)
            assert len(result) == 2
            assert result[0]['processed'] is True
        finally:
            os.unlink(input_path)
            os.unlink(output_path)

    def test_invalid_input_returns_error(self):
        """Test that invalid input returns exit code 1."""
        input_data = [{'id': 1, 'name': '', 'value': 10}]  # Empty name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            exit_code = process_command(input_path, output_path)
            assert exit_code == 1
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestCLI:
    """Tests for CLI argument parsing."""

    def test_parser_creation(self):
        """Test that parser is created correctly."""
        parser = create_parser()
        assert parser is not None

    def test_process_command_parsing(self):
        """Test parsing of process command."""
        parser = create_parser()
        args = parser.parse_args(['process', '--input', 'in.json', '--output', 'out.json'])
        assert args.command == 'process'
        assert args.input_file == 'in.json'
        assert args.output_file == 'out.json'

    def test_missing_input_flag(self):
        """Test that missing --input flag raises error."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(['process', '--output', 'out.json'])

    def test_missing_output_flag(self):
        """Test that missing --output flag raises error."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(['process', '--input', 'in.json'])

    def test_verbose_flag_short(self):
        """Test parsing of verbose flag short form."""
        parser = create_parser()
        args = parser.parse_args(['process', '--input', 'in.json', '--output', 'out.json', '-v'])
        assert args.verbose is True

    def test_verbose_flag_long(self):
        """Test parsing of verbose flag long form."""
        parser = create_parser()
        args = parser.parse_args(
            ['process', '--input', 'in.json', '--output', 'out.json', '--verbose']
        )
        assert args.verbose is True

    def test_no_verbose_flag(self):
        """Test that verbose defaults to False."""
        parser = create_parser()
        args = parser.parse_args(['process', '--input', 'in.json', '--output', 'out.json'])
        assert args.verbose is False


class TestMainFunction:
    """Tests for main entry point."""

    def test_no_command(self):
        """Test that no command shows help and returns 1."""
        exit_code = main([])
        assert exit_code == 1

    def test_successful_run(self):
        """Test successful main function execution."""
        input_data = [{'id': 1, 'name': 'Test', 'value': 100}]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            exit_code = main(['process', '--input', input_path, '--output', output_path])
            assert exit_code == 0
        finally:
            os.unlink(input_path)
            os.unlink(output_path)


class TestIntegration:
    """Integration tests running the tool as a subprocess."""

    @pytest.fixture
    def project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def test_module_execution(self, project_root):
        """Test running as python -m src.task_processor."""
        input_data = [
            {'id': 1, 'name': 'Alpha', 'value': 100},
            {'id': 2, 'name': 'Beta', 'value': 200},
        ]

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            json.dump(input_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable, '-m', 'src.task_processor',
                    'process', '--input', input_path, '--output', output_path
                ],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0

            with open(output_path, 'r') as f:
                output_data = json.load(f)
            assert len(output_data) == 2
            assert output_data[0]['processed'] is True
        finally:
            os.unlink(input_path)
            os.unlink(output_path)

    def test_invalid_json_exit_code(self, project_root):
        """Test that invalid JSON returns exit code 1."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            f.write('{ not valid json')
            input_path = f.name

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable, '-m', 'src.task_processor',
                    'process', '--input', input_path, '--output', output_path
                ],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 1
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_duplicate_ids_exit_code(self, project_root):
        """Test that duplicate IDs return exit code 1."""
        input_data = [
            {'id': 1, 'name': 'First', 'value': 100},
            {'id': 1, 'name': 'Duplicate', 'value': 200},
        ]

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            json.dump(input_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable, '-m', 'src.task_processor',
                    'process', '--input', input_path, '--output', output_path
                ],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 1
            assert 'Duplicate id' in result.stderr
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_missing_field_exit_code(self, project_root):
        """Test that missing fields return exit code 1."""
        input_data = [{'id': 1, 'name': 'Test'}]  # Missing 'value'

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            json.dump(input_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable, '-m', 'src.task_processor',
                    'process', '--input', input_path, '--output', output_path
                ],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 1
            assert "missing required field 'value'" in result.stderr
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_wrong_type_exit_code(self, project_root):
        """Test that wrong types return exit code 1."""
        input_data = [{'id': '1', 'name': 'Test', 'value': 100}]  # id is string

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            json.dump(input_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, dir=project_root
        ) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [
                    sys.executable, '-m', 'src.task_processor',
                    'process', '--input', input_path, '--output', output_path
                ],
                cwd=project_root,
                capture_output=True,
                text=True
            )
            assert result.returncode == 1
            assert "'id' must be an integer" in result.stderr
        finally:
            os.unlink(input_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
