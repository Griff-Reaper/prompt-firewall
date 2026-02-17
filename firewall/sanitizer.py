"""
Prompt Sanitizer - Clean prompts of malicious content and PII
"""
import re
from typing import Dict, List, Tuple


class PromptSanitizer:
    """
    Sanitize prompts by removing or replacing malicious patterns
    """
    
    def __init__(self):
        """Initialize sanitizer with patterns"""
        
        # Malicious instruction patterns
        self.instruction_patterns = [
            (r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", "[INSTRUCTION_REMOVED]"),
            (r"disregard\s+(all\s+)?(previous|prior|above)", "[INSTRUCTION_REMOVED]"),
            (r"forget\s+(everything|all|what)", "[INSTRUCTION_REMOVED]"),
            (r"new\s+instructions?:", "[INSTRUCTION_REMOVED]"),
            (r"system\s+prompt:", "[SYSTEM_REMOVED]"),
            (r"you\s+are\s+now\s+", "[ROLE_REMOVED] "),
            (r"roleplay\s+as", "[ROLEPLAY_REMOVED]"),
            (r"pretend\s+(you\s+are|to\s+be)", "[PRETEND_REMOVED]"),
            (r"DAN\s+mode", "[MODE_REMOVED]"),
            (r"developer\s+mode", "[MODE_REMOVED]"),
        ]
        
        # PII patterns
        self.pii_patterns = [
            # SSN
            (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]"),
            (r"\b\d{9}\b", "[SSN_REDACTED]"),
            
            # Credit card (simple pattern)
            (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[CARD_REDACTED]"),
            
            # Email
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL_REDACTED]"),
            
            # Phone
            (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "[PHONE_REDACTED]"),
            (r"\(\d{3}\)\s*\d{3}[-.]?\d{4}", "[PHONE_REDACTED]"),
            
            # API keys (common patterns)
            (r"sk-[a-zA-Z0-9]{32,}", "[API_KEY_REDACTED]"),
            (r"[a-zA-Z0-9_-]{32,}", "[TOKEN_REDACTED]"),  # Generic long tokens
        ]
        
        # SQL injection patterns
        self.sql_patterns = [
            (r"';?\s*(DROP|DELETE|INSERT|UPDATE|SELECT)\s+", "[SQL_REMOVED] "),
            (r"(OR|AND)\s+1\s*=\s*1", "[SQL_REMOVED]"),
            (r"--\s*$", ""),  # SQL comments
        ]
    
    def sanitize(self, prompt: str, remove_pii: bool = True, 
                 remove_sql: bool = True) -> Tuple[str, List[str]]:
        """
        Sanitize prompt
        
        Args:
            prompt: Original prompt
            remove_pii: Whether to remove PII
            remove_sql: Whether to remove SQL injection attempts
        
        Returns:
            Tuple of (sanitized_prompt, list_of_changes)
        """
        sanitized = prompt
        changes = []
        
        # Remove malicious instructions
        for pattern, replacement in self.instruction_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                sanitized = re.sub(pattern, replacement, sanitized, 
                                  flags=re.IGNORECASE)
                changes.append(f"Removed malicious instruction: {pattern}")
        
        # Remove PII
        if remove_pii:
            for pattern, replacement in self.pii_patterns:
                if re.search(pattern, sanitized):
                    sanitized = re.sub(pattern, replacement, sanitized)
                    changes.append(f"Redacted PII: {pattern[:20]}...")
        
        # Remove SQL injection
        if remove_sql:
            for pattern, replacement in self.sql_patterns:
                if re.search(pattern, sanitized, re.IGNORECASE):
                    sanitized = re.sub(pattern, replacement, sanitized, 
                                      flags=re.IGNORECASE)
                    changes.append(f"Removed SQL injection: {pattern[:20]}...")
        
        # Clean up multiple spaces and newlines
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        return sanitized, changes
    
    def contains_pii(self, prompt: str) -> bool:
        """Check if prompt contains PII"""
        for pattern, _ in self.pii_patterns:
            if re.search(pattern, prompt):
                return True
        return False
    
    def get_pii_types(self, prompt: str) -> List[str]:
        """Get types of PII found in prompt"""
        pii_types = []
        
        if re.search(r"\b\d{3}-\d{2}-\d{4}\b", prompt):
            pii_types.append("SSN")
        if re.search(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", prompt):
            pii_types.append("Credit Card")
        if re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", prompt):
            pii_types.append("Email")
        if re.search(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", prompt):
            pii_types.append("Phone")
        if re.search(r"sk-[a-zA-Z0-9]{32,}", prompt):
            pii_types.append("API Key")
        
        return pii_types


# Singleton instance
_sanitizer = None

def get_sanitizer() -> PromptSanitizer:
    """Get or create sanitizer instance"""
    global _sanitizer
    if _sanitizer is None:
        _sanitizer = PromptSanitizer()
    return _sanitizer
