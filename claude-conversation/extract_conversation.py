#!/usr/bin/env python3
"""Extract conversation from Claude Code JSONL log, excluding thinking blocks."""

import json
import sys

def extract_conversation(input_file, output_file):
    """Extract user and assistant messages, excluding thinking and tool results."""
    messages = []

    with open(input_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                obj = json.loads(line)
                msg_type = obj.get('type')

                if msg_type == 'user':
                    # Extract user message (skip tool results)
                    message = obj.get('message', {})
                    content = message.get('content', '')

                    # Skip if this is a tool result (not actual user text)
                    if isinstance(content, list) and content:
                        if content[0].get('type') == 'tool_result':
                            continue
                        # Extract text from text blocks
                        text_parts = [
                            item.get('text', '')
                            for item in content
                            if isinstance(item, dict) and item.get('type') == 'text'
                        ]
                        text = ' '.join(text_parts)
                    elif isinstance(content, str):
                        text = content
                    else:
                        continue

                    # Only add if we have actual text
                    if text.strip():
                        messages.append({
                            'role': 'user',
                            'text': text,
                            'line': line_num
                        })

                elif msg_type == 'queue-operation':
                    # These are user messages queued while Claude was working
                    operation = obj.get('operation')
                    if operation == 'enqueue':
                        text = obj.get('content', '')
                        if text.strip():
                            messages.append({
                                'role': 'user',
                                'text': text,
                                'line': line_num,
                                'queued': True
                            })

                elif msg_type == 'assistant':
                    # Extract assistant message, filtering out thinking
                    message = obj.get('message', {})
                    content = message.get('content', [])
                    texts = []
                    tool_names = []

                    for item in content:
                        if isinstance(item, dict):
                            if item.get('type') == 'text':
                                texts.append(item.get('text', ''))
                            elif item.get('type') == 'tool_use':
                                # Just capture tool name, not full input/output
                                tool_names.append(item.get('name'))
                            # Skip 'thinking' type

                    # Only add if we have text or tools
                    if texts or tool_names:
                        msg = {
                            'role': 'assistant',
                            'text': '\n\n'.join(texts) if texts else '',
                            'line': line_num
                        }
                        if tool_names:
                            msg['tools'] = tool_names
                        messages.append(msg)

                elif msg_type == 'system':
                    # Include system messages for context
                    text = obj.get('text', '')
                    if text.strip():
                        messages.append({
                            'role': 'system',
                            'text': text,
                            'line': line_num
                        })

            except json.JSONDecodeError:
                print(f"Warning: Could not parse line {line_num}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Error on line {line_num}: {e}", file=sys.stderr)

    # Write to output
    with open(output_file, 'w') as f:
        json.dump(messages, f, indent=2)

    print(f"Extracted {len(messages)} messages to {output_file}")
    return messages

if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'claude-conversation/2025-11-07.jsonl'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'conversation_extracted.json'

    extract_conversation(input_file, output_file)
