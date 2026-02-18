"""Markdown cleaning utilities for token optimization.

Provides simple, safe cleaning of markdown content before sending to LLMs.
Preserves meaning while reducing token count.
"""

import re


def clean_markdown_content(raw_md: str, aggressive: bool = False) -> str:
    """Clean markdown content for LLM consumption.

    Performs safe, reversible transformations that preserve meaning
    while reducing token count.

    Args:
        raw_md: Raw markdown content
        aggressive: If True, applies more aggressive compression (may lose some formatting)

    Returns:
        Cleaned, compact text suitable for LLM context
    """
    if not raw_md:
        return ""

    text = raw_md

    # Step 1: Remove markdown syntax characters
    # Headers: # ## ### → remove but keep text
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)

    # Bold/italic: **text** or *text* → keep text only
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)

    # Code blocks: ```lang\ncode\n``` → keep code only, remove markers
    text = re.sub(r'```[\w]*\n?', '', text)
    text = re.sub(r'```', '', text)

    # Inline code: `code` → keep code
    text = re.sub(r'`([^`]+)`', r'\1', text)

    # Links: [text](url) → keep text only
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)

    # Images: ![alt](url) → keep alt text
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[image: \1]', text)

    # Horizontal rules: --- or *** → remove
    text = re.sub(r'^[\-*]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Step 2: Clean up list markers (keep content)
    # Convert bullet lists to inline format
    lines = text.split('\n')
    cleaned_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()

        # Check if it's a list item
        if re.match(r'^[-*•]\s+', stripped):
            # Remove bullet, keep content
            content = re.sub(r'^[-*•]\s+', '', stripped)
            if aggressive:
                cleaned_lines.append(f'• {content}')
            else:
                cleaned_lines.append(content)
            in_list = True
        elif re.match(r'^\d+\.\s+', stripped):
            # Numbered list - keep number
            content = re.sub(r'^(\d+)\.\s+', r'\1. ', stripped)
            cleaned_lines.append(content)
            in_list = True
        else:
            if in_list and stripped:
                # Continuation of list item or new paragraph
                cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
            in_list = False

    text = '\n'.join(cleaned_lines)

    # Step 3: Normalize whitespace
    # Replace multiple newlines with single newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)

    # Step 4: Compact formatting (aggressive mode)
    if aggressive:
        # Convert newlines to pipe separators for very compact format
        # But preserve paragraph breaks (double newlines)
        paragraphs = text.split('\n\n')
        compact_paragraphs = []
        for p in paragraphs:
            # Single newlines within paragraph become spaces
            p = p.replace('\n', ' ')
            # Remove extra spaces
            p = re.sub(r' +', ' ', p)
            if p.strip():
                compact_paragraphs.append(p.strip())
        text = '\n\n'.join(compact_paragraphs)

    # Step 5: Remove empty lines at start/end
    text = text.strip()

    return text


def compact_soul_content(raw_md: str) -> str:
    """Specialized cleaner for SOUL.md files.

    Preserves personality nuances while removing unnecessary formatting.
    """
    if not raw_md:
        return ""

    # Basic cleaning
    text = clean_markdown_content(raw_md, aggressive=False)

    # Remove decorative emojis if they appear alone on lines
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        # Skip lines that are just emojis or decorative symbols
        if stripped and not re.match(r'^[💼📊⚡📈💡💰🚀🔬🔧📡🌌🛡️🏴‍☠️🎸🎯🐱\-=*]+$', stripped):
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)


def compact_agents_content(raw_md: str) -> str:
    """Specialized cleaner for AGENTS.md files.

    Optimizes for instruction clarity and brevity.
    """
    if not raw_md:
        return ""

    # More aggressive cleaning for agents (instructions)
    text = clean_markdown_content(raw_md, aggressive=True)

    # Convert to numbered list format for better structure
    lines = text.split('\n')
    result_lines = []
    line_num = 1

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('•'):
            result_lines.append(f"{line_num}. {stripped}")
            line_num += 1
        elif stripped:
            result_lines.append(line)

    return '\n'.join(result_lines)


def compact_tools_content(raw_md: str) -> str:
    """Specialized cleaner for TOOLS.md files.

    Converts verbose tool descriptions to compact format.
    """
    if not raw_md:
        return ""

    text = clean_markdown_content(raw_md, aggressive=True)

    # Extract tool definitions and convert to compact format
    tools = []
    current_tool = {}

    lines = text.split('\n')
    for line in lines:
        stripped = line.strip()

        # Detect tool name (usually after ### or bold)
        if stripped and not current_tool.get('name'):
            current_tool['name'] = stripped
        elif stripped.startswith('Params:') or stripped.startswith('Parameters:'):
            current_tool['params'] = stripped.split(':', 1)[1].strip()
        elif stripped and current_tool.get('name') and not current_tool.get('desc'):
            current_tool['desc'] = stripped
            # Save this tool and reset
            tools.append(current_tool)
            current_tool = {}

    # Build compact format
    if tools:
        compact = "Tools:\n"
        for tool in tools:
            name = tool.get('name', 'unknown')
            desc = tool.get('desc', '')
            params = tool.get('params', '')
            compact += f"- {name}: {desc[:50]}"
            if params:
                compact += f" [{params}]"
            compact += "\n"
        return compact

    return text


def estimate_token_savings(original: str, cleaned: str) -> dict:
    """Estimate token savings from cleaning.

    Args:
        original: Original markdown text
        cleaned: Cleaned text

    Returns:
        Dict with original_length, cleaned_length, savings_percent
    """
    orig_chars = len(original)
    clean_chars = len(cleaned)

    # Rough estimate: ~4 characters per token for English text
    orig_tokens = orig_chars // 4
    clean_tokens = clean_chars // 4

    savings = orig_tokens - clean_tokens
    savings_percent = (savings / orig_tokens * 100) if orig_tokens > 0 else 0

    return {
        'original_chars': orig_chars,
        'cleaned_chars': clean_chars,
        'original_tokens_est': orig_tokens,
        'cleaned_tokens_est': clean_tokens,
        'tokens_saved': savings,
        'savings_percent': round(savings_percent, 1)
    }


# Convenience function for context builder
def prepare_md_for_context(file_path: str, file_type: str = 'generic') -> str:
    """Prepare a markdown file for inclusion in LLM context.

    Args:
        file_path: Path to the markdown file
        file_type: Type of file ('soul', 'agents', 'tools', 'identity', 'generic')

    Returns:
        Cleaned, token-optimized content
    """
    from pathlib import Path

    try:
        raw_content = Path(file_path).read_text(encoding='utf-8')
    except Exception as e:
        return f"[Error reading {file_path}: {e}]"

    # Select appropriate cleaner based on file type
    cleaners = {
        'soul': compact_soul_content,
        'agents': compact_agents_content,
        'tools': compact_tools_content,
        'identity': compact_soul_content,  # Similar to SOUL
        'generic': clean_markdown_content
    }

    cleaner = cleaners.get(file_type, clean_markdown_content)
    return cleaner(raw_content)
