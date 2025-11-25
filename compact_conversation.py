#!/usr/bin/env python3
"""Compact Claude Code JSONL conversation into readable YAML format."""

import json
import sys
import yaml
from datetime import datetime


def truncate_text(text, max_words):
    """Truncate text to max_words and add ellipsis if needed."""
    if not text:
        return ""
    words = text.split()
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]) + '...'


def format_tool_call(tool, max_words):
    """Format a tool call based on its type."""
    tool_name = tool.get('name', 'unknown')
    tool_input = tool.get('input', {})

    if tool_name == 'Bash':
        # Keep full command
        return {
            'tool': 'Bash',
            'command': tool_input.get('command', '')
        }
    elif tool_name == 'TodoWrite':
        # Just log the tool call
        return {'tool': 'TodoWrite'}
    elif tool_name in ['Edit', 'Write', 'Read']:
        # Just log the file
        return {
            'tool': tool_name,
            'file': tool_input.get('file_path', '')
        }
    elif tool_name in ['Grep', 'Glob']:
        # Log full call
        return {
            'tool': tool_name,
            'params': tool_input
        }
    elif tool_name == 'Task':
        # Sub-agent call - include description and truncated prompt
        return {
            'tool': 'Task (sub-agent)',
            'description': tool_input.get('description', ''),
            'prompt': truncate_text(tool_input.get('prompt', ''), max_words * 2)  # Give more space for Task prompts
        }
    else:
        # Other tools - log name and simplified params
        return {
            'tool': tool_name,
            'params': tool_input
        }


def format_tool_result(result, max_words):
    """Format a tool result - type and first few words."""
    content = result.get('content', '')
    is_error = result.get('is_error', False)

    if isinstance(content, str):
        truncated = truncate_text(content, max_words)
    else:
        truncated = str(content)[:100]

    result_obj = {'result': truncated}
    if is_error:
        result_obj['error'] = True
    return result_obj


def compact_conversation(input_file, output_file, max_words=20):
    """Extract and compact conversation into YAML format."""
    conversation = []
    last_timestamp_day = None
    last_cwd = None

    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                obj = json.loads(line)
                msg_type = obj.get('type')

                # Track timestamp changes (to day precision)
                timestamp = obj.get('timestamp')
                if timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    day = dt.strftime('%Y-%m-%d')
                    if day != last_timestamp_day:
                        conversation.append({
                            'type': 'context_change',
                            'timestamp': day
                        })
                        last_timestamp_day = day

                # Track cwd changes
                cwd = obj.get('cwd')
                if cwd and cwd != last_cwd:
                    conversation.append({
                        'type': 'context_change',
                        'cwd': cwd
                    })
                    last_cwd = cwd

                if msg_type == 'user':
                    # Extract user message or tool results
                    message = obj.get('message', {})
                    content = message.get('content', '')

                    if isinstance(content, list) and content:
                        # Check if this is tool results
                        if content[0].get('type') == 'tool_result':
                            # Extract tool results
                            tool_results = []
                            for item in content:
                                if item.get('type') == 'tool_result':
                                    tool_results.append(format_tool_result(item, max_words))

                            if tool_results:
                                conversation.append({
                                    'type': 'tool_results',
                                    'results': tool_results
                                })
                            continue

                        # Extract text from text blocks
                        text_parts = [
                            item.get('text', '')
                            for item in content
                            if isinstance(item, dict) and item.get('type') == 'text'
                        ]
                        text = '\n'.join(text_parts)
                    elif isinstance(content, str):
                        text = content
                    else:
                        continue

                    if text.strip():
                        conversation.append({
                            'type': 'user',
                            'text': text
                        })

                elif msg_type == 'queue-operation':
                    # User messages queued while Claude was working
                    operation = obj.get('operation')
                    if operation == 'enqueue':
                        text = obj.get('content', '')
                        if text.strip():
                            conversation.append({
                                'type': 'user',
                                'text': text,
                                'queued': True
                            })

                elif msg_type == 'assistant':
                    # Extract assistant message
                    # Check if this is a sub-agent (sidechain)
                    is_sidechain = obj.get('isSidechain', False)
                    message = obj.get('message', {})
                    content = message.get('content', [])

                    msg_parts = []

                    for item in content:
                        if not isinstance(item, dict):
                            continue

                        item_type = item.get('type')

                        if item_type == 'thinking':
                            # Keep first N words of thinking
                            thinking = item.get('thinking', '')
                            msg_parts.append({
                                'thinking': truncate_text(thinking, max_words)
                            })

                        elif item_type == 'text':
                            # Keep full text
                            msg_parts.append({
                                'text': item.get('text', '')
                            })

                        elif item_type == 'tool_use':
                            # Format tool call
                            msg_parts.append({
                                'tool_call': format_tool_call(item, max_words)
                            })

                    if msg_parts:
                        msg_obj = {
                            'type': 'assistant (sub-agent)' if is_sidechain else 'assistant',
                            'content': msg_parts
                        }
                        conversation.append(msg_obj)

                elif msg_type == 'system':
                    # Include system messages
                    text = obj.get('text', '')
                    if text.strip():
                        conversation.append({
                            'type': 'system',
                            'text': text
                        })

            except json.JSONDecodeError:
                print(f"Warning: Could not parse line {line_num}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Error on line {line_num}: {e}", file=sys.stderr)

    # Write as YAML
    with open(output_file, 'w') as f:
        yaml.dump(conversation, f,
                  default_flow_style=False,
                  allow_unicode=True,
                  sort_keys=False,
                  width=120)

    print(f"Compacted {len(conversation)} items to {output_file}")
    return conversation


if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'claude-conversation/2025-11-07.jsonl'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'conversation_compact.yaml'
    max_words = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    compact_conversation(input_file, output_file, max_words)
