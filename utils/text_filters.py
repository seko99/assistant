"""
Text filtering utilities for cleaning LLM responses.

This module provides functions to filter out unwanted content from LLM responses,
such as thinking blocks, internal reasoning, and other meta-content.
"""

import re
from typing import Optional


# Global patterns for all thinking/reasoning tags that different LLM models might use
THINKING_PATTERNS = [
    r'<thinking>.*?</thinking>',
    r'<think>.*?</think>',
    r'<reasoning>.*?</reasoning>',
    r'<analysis>.*?</analysis>',
    r'<internal>.*?</internal>',
    r'<meta>.*?</meta>',
]


def filter_thinking_blocks(text: str, remove_empty_lines: bool = True) -> str:
    """
    Removes thinking/reasoning blocks from text.

    This function filters out reasoning blocks that different LLM models include
    in their responses. These blocks contain internal model reasoning that
    should not be included in final output like transcripts or TTS.

    Supports multiple tag formats: <thinking>, <think>, <reasoning>, <analysis>,
    <internal>, <meta> to accommodate different LLM model conventions.

    Args:
        text: Input text that may contain thinking blocks
        remove_empty_lines: Whether to clean up extra empty lines after filtering

    Returns:
        Cleaned text with thinking blocks removed

    Examples:
        >>> text = '''<thinking>
        ... This is internal reasoning...
        ... </thinking>
        ...
        ... This is the actual response.'''
        >>> filter_thinking_blocks(text)
        'This is the actual response.'

        >>> text = 'Normal text <reasoning>internal</reasoning> more text.'
        >>> filter_thinking_blocks(text)
        'Normal text  more text.'
    """
    if not text:
        return text

    cleaned_text = text

    # Apply all thinking/reasoning patterns to ensure comprehensive filtering
    for pattern in THINKING_PATTERNS:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)

    if remove_empty_lines:
        # Clean up multiple consecutive newlines
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)

        # Remove leading/trailing whitespace
        cleaned_text = cleaned_text.strip()

    return cleaned_text


def filter_reasoning_blocks(text: str, remove_empty_lines: bool = True) -> str:
    """
    Removes various types of reasoning/meta blocks from text.

    This function is now an alias for filter_thinking_blocks() since they
    both use the same comprehensive set of patterns. Kept for backward
    compatibility.

    Args:
        text: Input text that may contain reasoning blocks
        remove_empty_lines: Whether to clean up extra empty lines after filtering

    Returns:
        Cleaned text with reasoning blocks removed
    """
    # Use the unified filter_thinking_blocks function
    return filter_thinking_blocks(text, remove_empty_lines)


def clean_llm_response(text: str,
                      filter_thinking: bool = True,
                      filter_reasoning: bool = False,
                      max_length: Optional[int] = None) -> str:
    """
    Comprehensive cleaning of LLM responses.

    This function provides a one-stop solution for cleaning LLM responses
    before they are used in transcripts, TTS, or user-facing output.

    Args:
        text: Raw LLM response text
        filter_thinking: Whether to remove <thinking> blocks
        filter_reasoning: Whether to remove other reasoning blocks
        max_length: Optional maximum length for truncation

    Returns:
        Cleaned text ready for use
    """
    if not text:
        return text

    cleaned_text = text

    # Apply thinking block filter
    if filter_thinking:
        cleaned_text = filter_thinking_blocks(cleaned_text)

    # Apply broader reasoning filter
    if filter_reasoning:
        cleaned_text = filter_reasoning_blocks(cleaned_text)

    # Truncate if needed
    if max_length and len(cleaned_text) > max_length:
        # Try to truncate at sentence boundary
        sentences = cleaned_text.split('. ')
        truncated = ''
        for sentence in sentences:
            if len(truncated + sentence + '. ') <= max_length:
                truncated += sentence + '. '
            else:
                break

        if truncated:
            cleaned_text = truncated.rstrip('. ') + '.'
        else:
            # Fallback to hard truncation
            cleaned_text = cleaned_text[:max_length].rstrip() + '...'

    return cleaned_text


def has_thinking_blocks(text: str) -> bool:
    """
    Checks if text contains thinking/reasoning blocks.

    Checks for multiple tag formats: <thinking>, <think>, <reasoning>, <analysis>,
    <internal>, <meta> to accommodate different LLM model conventions.

    Args:
        text: Text to check

    Returns:
        True if any thinking blocks are found, False otherwise
    """
    if not text:
        return False

    # Check for any of the thinking/reasoning patterns
    for pattern in THINKING_PATTERNS:
        if re.search(pattern, text, flags=re.DOTALL | re.IGNORECASE):
            return True

    return False


def extract_thinking_content(text: str) -> list[str]:
    """
    Extracts the content of thinking/reasoning blocks without the tags.

    Extracts content from multiple tag formats: <thinking>, <think>, <reasoning>,
    <analysis>, <internal>, <meta> to accommodate different LLM model conventions.

    This can be useful for debugging or analysis purposes.

    Args:
        text: Text that may contain thinking blocks

    Returns:
        List of thinking block contents (without tags)
    """
    if not text:
        return []

    all_matches = []

    # Extract content from all thinking/reasoning patterns
    for pattern in THINKING_PATTERNS:
        # Convert pattern to capture group format
        # e.g., r'<thinking>.*?</thinking>' -> r'<thinking>(.*?)</thinking>'
        capture_pattern = pattern.replace('.*?', '(.*?)')
        matches = re.findall(capture_pattern, text, flags=re.DOTALL | re.IGNORECASE)
        all_matches.extend(matches)

    # Clean up the extracted content
    return [match.strip() for match in all_matches]