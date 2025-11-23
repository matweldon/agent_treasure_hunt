#!/usr/bin/env python3
"""Analyze the project structure and codebase statistics."""

import os
from pathlib import Path
from collections import defaultdict


def count_lines(file_path):
    """Count lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except Exception:
        return 0


def analyze_project(root_dir='.'):
    """Analyze project structure and statistics."""
    root = Path(root_dir)

    # Directories to exclude
    exclude_dirs = {
        '.git', '__pycache__', '.pytest_cache', '.venv', 'venv',
        'node_modules', '.tox', 'build', 'dist', '*.egg-info',
        '.devcontainer', 'treasure_hunt'  # Exclude generated treasure hunts
    }

    # Track statistics
    stats = {
        'total_files': 0,
        'python_files': 0,
        'test_files': 0,
        'source_files': 0,
        'total_lines': 0,
        'python_lines': 0,
        'test_lines': 0,
        'source_lines': 0,
        'files_by_type': defaultdict(int),
        'lines_by_type': defaultdict(int),
        'files_by_dir': defaultdict(int),
        'lines_by_dir': defaultdict(int),
    }

    # Walk the directory tree
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter out excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.endswith('.egg-info')]

        rel_dir = Path(dirpath).relative_to(root)

        for filename in filenames:
            # Skip hidden files and compiled files
            if filename.startswith('.') or filename.endswith('.pyc'):
                continue

            file_path = Path(dirpath) / filename
            extension = file_path.suffix

            # Count file
            stats['total_files'] += 1
            stats['files_by_type'][extension if extension else 'no_extension'] += 1
            stats['files_by_dir'][str(rel_dir)] += 1

            # Count lines
            lines = count_lines(file_path)
            stats['total_lines'] += lines
            stats['lines_by_type'][extension if extension else 'no_extension'] += lines
            stats['lines_by_dir'][str(rel_dir)] += lines

            # Python-specific stats
            if extension == '.py':
                stats['python_files'] += 1
                stats['python_lines'] += lines

                # Check if it's a test file
                if 'test' in str(file_path).lower() or filename.startswith('test_'):
                    stats['test_files'] += 1
                    stats['test_lines'] += lines
                else:
                    stats['source_files'] += 1
                    stats['source_lines'] += lines

    return stats


def print_stats(stats):
    """Print formatted statistics."""
    print("=" * 70)
    print("PROJECT STRUCTURE ANALYSIS")
    print("=" * 70)
    print()

    print("Overall Statistics:")
    print("-" * 70)
    print(f"  Total files:           {stats['total_files']:6,}")
    print(f"  Total lines of code:   {stats['total_lines']:6,}")
    print()

    print("Python Files:")
    print("-" * 70)
    print(f"  Total Python files:    {stats['python_files']:6,}")
    print(f"  Source files:          {stats['source_files']:6,} ({stats['source_lines']:,} lines)")
    print(f"  Test files:            {stats['test_files']:6,} ({stats['test_lines']:,} lines)")
    print(f"  Total Python lines:    {stats['python_lines']:6,}")
    print()

    print("Files by Type:")
    print("-" * 70)
    for ext, count in sorted(stats['files_by_type'].items(), key=lambda x: x[1], reverse=True):
        lines = stats['lines_by_type'][ext]
        print(f"  {ext:20s}: {count:4} files, {lines:6,} lines")
    print()

    print("Files by Directory (top 10):")
    print("-" * 70)
    for dir_path, count in sorted(stats['files_by_dir'].items(), key=lambda x: x[1], reverse=True)[:10]:
        lines = stats['lines_by_dir'][dir_path]
        # Truncate long paths
        display_path = dir_path if len(dir_path) <= 35 else '...' + dir_path[-32:]
        print(f"  {display_path:35s}: {count:3} files, {lines:6,} lines")
    print()


if __name__ == '__main__':
    stats = analyze_project()
    print_stats(stats)
