#!/usr/bin/env python3
"""Generate comprehensive statistics for blog post about the Claude Code session."""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict


def analyze_conversation(json_path: str):
    """Extract statistics from the conversation JSON."""
    with open(json_path, 'r') as f:
        conversation = json.load(f)

    user_messages = 0
    assistant_messages = 0
    tool_calls_by_type = Counter()
    total_tool_calls = 0

    for entry in conversation:
        role = entry.get('role')
        if role == 'user':
            user_messages += 1
        elif role == 'assistant':
            assistant_messages += 1
            tools = entry.get('tools', [])
            for tool in tools:
                tool_calls_by_type[tool] += 1
                total_tool_calls += 1

    return {
        'total_entries': len(conversation),
        'user_messages': user_messages,
        'assistant_messages': assistant_messages,
        'total_tool_calls': total_tool_calls,
        'tool_calls_by_type': dict(tool_calls_by_type)
    }


def extract_timestamps():
    """Extract start and end timestamps from JSONL file."""
    first_line = subprocess.run(
        ['head', '-n', '1', 'claude-conversation/2025-11-07.jsonl'],
        capture_output=True,
        text=True
    ).stdout.strip()

    last_line = subprocess.run(
        ['tail', '-n', '1', 'claude-conversation/2025-11-07.jsonl'],
        capture_output=True,
        text=True
    ).stdout.strip()

    first_entry = json.loads(first_line)
    last_entry = json.loads(last_line)

    start_time_str = first_entry.get('timestamp') or first_entry.get('snapshot', {}).get('timestamp')
    end_time_str = last_entry.get('timestamp')

    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))

    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())

    return {
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
        'duration_seconds': total_seconds,
        'duration_hours': total_seconds // 3600,
        'duration_minutes': (total_seconds % 3600) // 60,
        'duration_str': str(duration)
    }


def count_lines(file_path):
    """Count lines in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except Exception:
        return 0


def analyze_project():
    """Analyze project structure and statistics."""
    exclude_dirs = {'.git', '__pycache__', '.pytest_cache', '.venv', 'venv',
                   'node_modules', '.devcontainer', 'treasure_hunt', 'scripts'}

    stats = {
        'total_files': 0,
        'python_files': 0,
        'test_files': 0,
        'source_files': 0,
        'python_lines': 0,
        'test_lines': 0,
        'source_lines': 0,
        'files_by_type': defaultdict(int),
        'lines_by_type': defaultdict(int),
    }

    for dirpath, dirnames, filenames in os.walk('.'):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.endswith('.egg-info')]

        for filename in filenames:
            if filename.startswith('.') or filename.endswith('.pyc'):
                continue

            file_path = Path(dirpath) / filename
            extension = file_path.suffix

            stats['total_files'] += 1
            stats['files_by_type'][extension if extension else 'no_extension'] += 1

            lines = count_lines(file_path)
            stats['lines_by_type'][extension if extension else 'no_extension'] += lines

            if extension == '.py':
                stats['python_files'] += 1
                stats['python_lines'] += lines

                if 'test' in str(file_path).lower() or filename.startswith('test_'):
                    stats['test_files'] += 1
                    stats['test_lines'] += lines
                else:
                    stats['source_files'] += 1
                    stats['source_lines'] += lines

    return stats


def generate_report():
    """Generate comprehensive blog statistics report."""
    print("=" * 80)
    print("CLAUDE CODE TREASURE HUNT PROJECT - COMPREHENSIVE STATISTICS")
    print("=" * 80)
    print()

    # Session timeline
    timeline = extract_timestamps()
    print("SESSION TIMELINE")
    print("-" * 80)
    print(f"Start time:      {timeline['start_time']}")
    print(f"End time:        {timeline['end_time']}")
    print(f"Total duration:  {timeline['duration_hours']}h {timeline['duration_minutes']}m")
    print()

    # Conversation stats
    conv_path = Path('claude-conversation/conversation_extracted.json')
    conversation = analyze_conversation(str(conv_path))
    print("CONVERSATION STATISTICS")
    print("-" * 80)
    print(f"User messages:          {conversation['user_messages']:4d}")
    print(f"Assistant messages:     {conversation['assistant_messages']:4d}")
    print(f"Total interactions:     {conversation['total_entries']:4d}")
    print(f"Total tool calls:       {conversation['total_tool_calls']:4d}")
    print()
    print("Tool Usage Breakdown:")
    for tool, count in sorted(conversation['tool_calls_by_type'].items(),
                             key=lambda x: x[1], reverse=True):
        percentage = (count / conversation['total_tool_calls']) * 100
        print(f"  {tool:20s}: {count:4d} ({percentage:5.1f}%)")
    print()

    # Project stats
    import os
    project = analyze_project()
    print("PROJECT CODEBASE")
    print("-" * 80)
    print(f"Total Python files:     {project['python_files']:4d}")
    print(f"  Source files:         {project['source_files']:4d} ({project['source_lines']:,} lines)")
    print(f"  Test files:           {project['test_files']:4d} ({project['test_lines']:,} lines)")
    print(f"Total Python lines:     {project['python_lines']:,}")
    print()
    print("All Files by Type:")
    for ext, count in sorted(project['files_by_type'].items(),
                            key=lambda x: x[1], reverse=True):
        lines = project['lines_by_type'][ext]
        if count > 0:
            print(f"  {ext:20s}: {count:4d} files, {lines:6,} lines")
    print()

    # Summary metrics
    print("KEY METRICS")
    print("-" * 80)
    print(f"Lines of code per hour:           {project['python_lines'] / timeline['duration_hours']:.0f}")
    print(f"Tool calls per user message:      {conversation['total_tool_calls'] / conversation['user_messages']:.1f}")
    print(f"Assistant msgs per user msg:      {conversation['assistant_messages'] / conversation['user_messages']:.1f}")
    print()


if __name__ == '__main__':
    import os
    generate_report()
