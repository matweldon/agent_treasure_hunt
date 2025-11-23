#!/usr/bin/env python3
"""Extract and analyze timestamps from the JSONL conversation file."""

import json
import subprocess
from datetime import datetime


def extract_timestamps():
    """Extract start and end timestamps from JSONL file."""
    # Get first line
    first_line = subprocess.run(
        ['head', '-n', '1', 'claude-conversation/2025-11-07.jsonl'],
        capture_output=True,
        text=True
    ).stdout.strip()

    # Get last line
    last_line = subprocess.run(
        ['tail', '-n', '1', 'claude-conversation/2025-11-07.jsonl'],
        capture_output=True,
        text=True
    ).stdout.strip()

    # Parse JSON
    first_entry = json.loads(first_line)
    last_entry = json.loads(last_line)

    # Extract timestamps
    start_time_str = first_entry.get('timestamp') or first_entry.get('snapshot', {}).get('timestamp')
    end_time_str = last_entry.get('timestamp')

    # Parse timestamps
    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))

    # Calculate duration
    duration = end_time - start_time

    # Print results
    print("=" * 70)
    print("SESSION TIMELINE")
    print("=" * 70)
    print()
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"End time:   {end_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print()
    print(f"Total duration: {duration}")
    print()

    # Break down duration
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    print(f"Duration breakdown:")
    print(f"  {hours} hours, {minutes} minutes, {seconds} seconds")
    print(f"  ({total_seconds:,} total seconds)")
    print()

    return {
        'start_time': start_time_str,
        'end_time': end_time_str,
        'duration_seconds': total_seconds,
        'duration_str': str(duration)
    }


if __name__ == '__main__':
    extract_timestamps()
