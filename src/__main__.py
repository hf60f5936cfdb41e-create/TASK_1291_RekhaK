#!/usr/bin/env python3
"""
Entry point for running task_processor as a module.

Usage: python -m src.task_processor process --input <file> --output <file>
"""

import sys
from .task_processor import main

if __name__ == '__main__':
    sys.exit(main())
