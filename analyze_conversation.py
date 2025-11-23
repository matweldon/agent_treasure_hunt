#!/usr/bin/env python3
"""Analyze Claude Code conversation for blog post material."""

import json
import re
from collections import defaultdict

def load_conversation(file_path):
    with open(file_path) as f:
        return json.load(f)

def analyze_conversation(messages):
    """Extract interesting patterns and quotes from conversation."""

    results = {
        'stats': {},
        'phases': [],
        'interesting_quotes': [],
        'design_discussions': [],
        'learning_moments': [],
        'fun_interactions': [],
        'tool_usage': defaultdict(int)
    }

    # Basic stats
    results['stats']['total_messages'] = len(messages)
    results['stats']['user_messages'] = sum(1 for m in messages if m['role'] == 'user')
    results['stats']['assistant_messages'] = sum(1 for m in messages if m['role'] == 'assistant')

    # Track phases of development
    current_phase = None
    phase_keywords = {
        'setup': ['setup', 'initialize', 'create directory', 'git init'],
        'generator': ['generator', 'treasure hunt generator', 'recursive', 'tree'],
        'testing': ['test', 'pytest', 'tdd', 'red/green'],
        'agent': ['agent', 'gemini', 'llm', 'api'],
        'game_loop': ['game loop', 'game', 'tool calling'],
        'docker': ['docker', 'container', 'security', 'sandbox'],
        'integration': ['integration', 'run', 'complete system']
    }

    # Analyze each message
    for i, msg in enumerate(messages):
        text = msg['text'].lower()

        # Track tool usage
        if msg['role'] == 'assistant' and msg.get('tools'):
            for tool in msg['tools']:
                results['tool_usage'][tool['name']] += 1

        # Detect phases
        for phase_name, keywords in phase_keywords.items():
            if any(kw in text for kw in keywords):
                if current_phase != phase_name:
                    results['phases'].append({
                        'phase': phase_name,
                        'start_index': i,
                        'sample_text': msg['text'][:200]
                    })
                    current_phase = phase_name

        # Look for fun interactions
        fun_patterns = [
            r'go chief', r'go for it', r'sounds good', r'nice!', r'great!',
            r'perfect', r'excellent', r'awesome', r'love it', r'brilliant'
        ]
        for pattern in fun_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                results['fun_interactions'].append({
                    'index': i,
                    'role': msg['role'],
                    'quote': msg['text'][:300],
                    'pattern': pattern
                })

        # Look for design discussions (longer messages with questions or reasoning)
        if len(msg['text']) > 200:
            if msg['role'] == 'assistant' and any(word in text for word in ['design', 'approach', 'architecture', 'consider', 'trade-off']):
                results['design_discussions'].append({
                    'index': i,
                    'summary': msg['text'][:500],
                    'full_text': msg['text']
                })
            elif msg['role'] == 'user' and '?' in msg['text']:
                # User asking questions
                results['design_discussions'].append({
                    'index': i,
                    'type': 'user_question',
                    'text': msg['text']
                })

        # Look for learning moments (user realizations or Claude explanations)
        learning_patterns = [
            r'i see', r'i understand', r'makes sense', r'didn\'t know',
            r'learned', r'interesting', r'good point', r'fair enough'
        ]
        if msg['role'] == 'user':
            for pattern in learning_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Get context (previous assistant message)
                    context = messages[i-1]['text'][:300] if i > 0 else ''
                    results['learning_moments'].append({
                        'index': i,
                        'user_text': msg['text'],
                        'context': context
                    })

    return results

def format_results(results):
    """Format analysis results for blog post."""

    output = []
    output.append("# CLAUDE CODE CONVERSATION ANALYSIS\n")
    output.append("=" * 60)
    output.append("")

    # Stats
    output.append("## STATISTICS")
    output.append("-" * 60)
    for key, value in results['stats'].items():
        output.append(f"{key}: {value}")
    output.append("")

    # Tool usage
    output.append("## TOOL USAGE")
    output.append("-" * 60)
    for tool, count in sorted(results['tool_usage'].items(), key=lambda x: -x[1]):
        output.append(f"{tool}: {count} times")
    output.append("")

    # Phases
    output.append("## DEVELOPMENT PHASES")
    output.append("-" * 60)
    for phase in results['phases']:
        output.append(f"\nPhase: {phase['phase'].upper()} (message #{phase['start_index']})")
        output.append(f"Sample: {phase['sample_text']}")
    output.append("")

    # Fun interactions
    output.append("## FUN INTERACTIONS & CASUAL MOMENTS")
    output.append("-" * 60)
    for interaction in results['fun_interactions'][:20]:  # Limit to 20
        output.append(f"\n[Message #{interaction['index']}] {interaction['role'].upper()}:")
        output.append(f"{interaction['quote']}")
        output.append("")

    # Design discussions
    output.append("## DESIGN DISCUSSIONS & DECISIONS")
    output.append("-" * 60)
    for discussion in results['design_discussions'][:15]:  # Limit to 15
        output.append(f"\n[Message #{discussion['index']}]")
        if discussion.get('type') == 'user_question':
            output.append(f"USER QUESTION: {discussion['text']}")
        else:
            output.append(f"DESIGN DISCUSSION:\n{discussion['summary']}")
        output.append("")

    # Learning moments
    output.append("## LEARNING MOMENTS")
    output.append("-" * 60)
    for moment in results['learning_moments'][:15]:  # Limit to 15
        output.append(f"\n[Message #{moment['index']}]")
        output.append(f"Context: {moment['context']}")
        output.append(f"User response: {moment['user_text']}")
        output.append("")

    return '\n'.join(output)

if __name__ == '__main__':
    messages = load_conversation('conversation_extracted.json')
    results = analyze_conversation(messages)

    formatted = format_results(results)

    with open('conversation_analysis.txt', 'w') as f:
        f.write(formatted)

    print("Analysis complete! Written to conversation_analysis.txt")
    print(f"Found {len(results['phases'])} development phases")
    print(f"Found {len(results['fun_interactions'])} fun interactions")
    print(f"Found {len(results['design_discussions'])} design discussions")
    print(f"Found {len(results['learning_moments'])} learning moments")
