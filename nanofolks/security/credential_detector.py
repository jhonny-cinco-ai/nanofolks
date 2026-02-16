"""Credential detection and symbolic reference conversion.

This module provides automatic detection of credentials in user messages
and converts them to symbolic references that are resolved at execution time.

Example:
    >>> detector = CredentialDetector()
    >>> text = "Create repo with token ghp_abc123..."
    >>> credentials = detector.detect(text)
    >>> # credentials = [{'type': 'github_token', 'value': 'ghp_abc123', 'start': 21, 'end': 30}]
"""

import re
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass
class CredentialMatch:
    """A detected credential in text."""
    credential_type: str
    value: str
    start: int
    end: int
    service: str


# Credential patterns for common services
CREDENTIAL_PATTERNS = [
    # GitHub
    (r'ghp_[a-zA-Z0-9]{36,}', 'github_token', 'github'),
    (r'github_pat_[a-zA-Z0-9_]{22,}', 'github_pat', 'github'),
    (r'gho_[a-zA-Z0-9]{36,}', 'github_oauth', 'github'),
    
    # AWS
    (r'AKIA[0-9A-Z]{16}', 'aws_access_key', 'aws'),
    (r'aws_access_key_id[=:\s]+[A-Z0-9]{20}', 'aws_access_key', 'aws'),
    
    # OpenAI
    (r'sk-[a-zA-Z0-9]{20,}', 'openai_api_key', 'openai'),
    
    # Anthropic
    (r'sk-ant-[a-zA-Z0-9]{48,}', 'anthropic_api_key', 'anthropic'),
    
    # Google
    (r'AIza[0-9A-Za-z_-]{35}', 'google_api_key', 'google'),
    
    # Slack
    (r'xox[baprs]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24,}', 'slack_token', 'slack'),
    
    # Discord
    (r'[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}', 'discord_token', 'discord'),
    
    # Stripe
    (r'sk_live_[0-9a-zA-Z]{24,}', 'stripe_secret', 'stripe'),
    (r'sk_test_[0-9a-zA-Z]{24,}', 'stripe_test', 'stripe'),
    
    # Database connection strings
    (r'(?:postgres|mysql|mongodb)://[^:]+:[^@]+@', 'db_connection', 'database'),
    
    # Generic high-entropy API keys (fallback)
    (r'(?:api[_-]?key|apikey|secret|token)[=:\s]+["\']?([a-zA-Z0-9_-]{32,})["\']?', 'generic_api_key', 'unknown'),
]

# Known service keywords for context-based detection
SERVICE_KEYWORDS = {
    'github': ['github', 'gh ', 'git hub', 'repository', 'repo', 'pull request', 'pr '],
    'aws': ['aws', 'amazon', 's3 ', 'ec2', 'lambda'],
    'openai': ['openai', 'gpt', 'chatgpt'],
    'anthropic': ['anthropic', 'claude', 'api.anthropic'],
    'google': ['google', 'gcp', 'cloud ', 'bigquery'],
    'slack': ['slack', 'slack.com'],
    'discord': ['discord', 'discord.com'],
    'stripe': ['stripe', 'payment', 'billing'],
    'database': ['database', 'db ', 'postgres', 'mysql', 'mongodb', 'postgresql'],
}


class CredentialDetector:
    """Detects credentials in text using pattern matching and context analysis."""
    
    def __init__(self):
        """Initialize the detector with compiled patterns."""
        self.patterns = [
            (re.compile(pattern, re.IGNORECASE), cred_type, service)
            for pattern, cred_type, service in CREDENTIAL_PATTERNS
        ]
    
    def detect(self, text: str) -> list[CredentialMatch]:
        """Detect all credentials in the given text.
        
        Args:
            text: The text to scan for credentials
            
        Returns:
            List of CredentialMatch objects found in the text
        """
        if not text:
            return []
        
        matches = []
        
        # Pattern-based detection
        for pattern, cred_type, service in self.patterns:
            for match in pattern.finditer(text):
                # For patterns with groups, extract the group
                if match.groups():
                    value = match.group(1)
                    start = match.start(1)
                    end = match.end(1)
                else:
                    value = match.group(0)
                    start = match.start()
                    end = match.end()
                
                # Try to infer service from context if unknown
                if service == 'unknown':
                    service = self._infer_service(text, start, end)
                
                matches.append(CredentialMatch(
                    credential_type=cred_type,
                    value=value,
                    start=start,
                    end=end,
                    service=service
                ))
        
        # Remove overlaps (keep longer matches)
        matches = self._remove_overlaps(matches)
        
        return matches
    
    def _infer_service(self, text: str, start: int, end: int) -> str:
        """Infer the service from surrounding text context.
        
        Args:
            text: Full text
            start: Start of credential
            end: End of credential
            
        Returns:
            Inferred service name or 'unknown'
        """
        # Look at surrounding context (100 chars before and after)
        context_start = max(0, start - 100)
        context_end = min(len(text), end + 100)
        context = text[context_start:context_end].lower()
        
        for service, keywords in SERVICE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in context:
                    return service
        
        return 'unknown'
    
    def _remove_overlaps(self, matches: list[CredentialMatch]) -> list[CredentialMatch]:
        """Remove overlapping matches, keeping longer ones.
        
        Args:
            matches: List of credential matches
            
        Returns:
            List with overlaps removed
        """
        if not matches:
            return []
        
        # Sort by position, then by length (longer first)
        matches.sort(key=lambda m: (m.start, -(m.end - m.start)))
        
        result = []
        last_end = -1
        
        for match in matches:
            if match.start >= last_end:
                result.append(match)
                last_end = match.end
        
        return result
    
    def has_credentials(self, text: str) -> bool:
        """Check if text contains any credentials.
        
        Args:
            text: The text to check
            
        Returns:
            True if credentials are found
        """
        return len(self.detect(text)) > 0
    
    def get_credential_types(self, text: str) -> list[str]:
        """Get list of credential types found in text.
        
        Args:
            text: The text to check
            
        Returns:
            List of unique credential types found
        """
        matches = self.detect(text)
        return list(set(m.credential_type for m in matches))
    
    def get_services(self, text: str) -> list[str]:
        """Get list of services detected in text.
        
        Args:
            text: The text to check
            
        Returns:
            List of unique services found
        """
        matches = self.detect(text)
        return list(set(m.service for m in matches))


# Global detector instance
_detector: Optional[CredentialDetector] = None


def get_credential_detector() -> CredentialDetector:
    """Get the global credential detector instance.
    
    Returns:
        The global CredentialDetector instance
    """
    global _detector
    if _detector is None:
        _detector = CredentialDetector()
    return _detector


def detect_credentials(text: str) -> list[CredentialMatch]:
    """Convenience function to detect credentials in text.
    
    Args:
        text: The text to scan
        
    Returns:
        List of credentials found
    """
    return get_credential_detector().detect(text)


def has_credentials(text: str) -> bool:
    """Convenience function to check if text has credentials.
    
    Args:
        text: The text to check
        
    Returns:
        True if credentials found
    """
    return get_credential_detector().has_credentials(text)
