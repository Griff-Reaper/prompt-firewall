"""
Threat Detection Engine - Wrapper for Prompt-Shield
"""
from typing import Optional, Dict, Any
import sys
import os

# Try to import prompt-shield (user's existing detection engine)
try:
    # This assumes prompt-shield is installed or in PYTHONPATH
    from prompt_shield import PromptShield
    PROMPT_SHIELD_AVAILABLE = True
except ImportError:
    PROMPT_SHIELD_AVAILABLE = False
    print("WARNING: prompt-shield not found. Using fallback detection.")

from .models import DetectionResult, ThreatLevel


class ThreatDetector:
    """
    Threat detection engine using Prompt-Shield
    
    Falls back to pattern matching if Prompt-Shield unavailable
    """
    
    def __init__(self, use_prompt_shield: bool = True):
        """
        Initialize detector
        
        Args:
            use_prompt_shield: Whether to use Prompt-Shield ML models
        """
        self.use_prompt_shield = use_prompt_shield and PROMPT_SHIELD_AVAILABLE
        
        if self.use_prompt_shield:
            try:
                self.shield = PromptShield()
                print("[✓] Prompt-Shield initialized successfully")
            except Exception as e:
                print(f"[!] Failed to initialize Prompt-Shield: {e}")
                self.use_prompt_shield = False
                self.shield = None
        else:
            self.shield = None
            print("[!] Using fallback pattern-based detection")
        
        # Fallback patterns for basic detection
        self.malicious_patterns = [
            "ignore previous instructions",
            "ignore all previous",
            "disregard",
            "forget everything",
            "new instructions",
            "system prompt",
            "you are now",
            "roleplay as",
            "jailbreak",
            "DAN mode",
            "developer mode"
        ]
    
    def detect(self, prompt: str, threshold: float = 0.5) -> DetectionResult:
        """
        Detect threats in prompt
        
        Args:
            prompt: User prompt to analyze
            threshold: Threat score threshold (0-1)
        
        Returns:
            DetectionResult with threat assessment
        """
        if self.use_prompt_shield and self.shield:
            return self._detect_with_shield(prompt, threshold)
        else:
            return self._detect_with_patterns(prompt)
    
    def _detect_with_shield(self, prompt: str, threshold: float) -> DetectionResult:
        """Use Prompt-Shield ML models for detection"""
        try:
            # Call Prompt-Shield's detection
            result = self.shield.detect(prompt)
            
            # Convert to our format
            threat_score = result.get("threat_score", 0.0)  # 0-1 scale
            is_malicious = threat_score >= threshold
            
            # Map score to threat level
            if threat_score >= 0.9:
                level = ThreatLevel.CRITICAL
            elif threat_score >= 0.7:
                level = ThreatLevel.HIGH
            elif threat_score >= 0.5:
                level = ThreatLevel.MEDIUM
            elif threat_score >= 0.3:
                level = ThreatLevel.LOW
            else:
                level = ThreatLevel.SAFE
            
            return DetectionResult(
                threat_score=threat_score * 100,  # Convert to 0-100
                threat_level=level,
                is_malicious=is_malicious,
                categories=result.get("categories", []),
                confidence=result.get("confidence", 0.0),
                details=result.get("details", {})
            )
        
        except Exception as e:
            print(f"[!] Prompt-Shield detection failed: {e}")
            return self._detect_with_patterns(prompt)
    
    def _detect_with_patterns(self, prompt: str) -> DetectionResult:
        """Fallback pattern-based detection"""
        prompt_lower = prompt.lower()
        
        # Count pattern matches
        matches = sum(1 for pattern in self.malicious_patterns 
                     if pattern in prompt_lower)
        
        # Calculate threat score based on matches
        threat_score = min(matches * 20, 100)  # Each match = 20 points, max 100
        
        # Determine threat level
        if threat_score >= 80:
            level = ThreatLevel.CRITICAL
        elif threat_score >= 60:
            level = ThreatLevel.HIGH
        elif threat_score >= 40:
            level = ThreatLevel.MEDIUM
        elif threat_score >= 20:
            level = ThreatLevel.LOW
        else:
            level = ThreatLevel.SAFE
        
        is_malicious = threat_score >= 40
        
        # Identify categories
        categories = []
        if "ignore" in prompt_lower or "disregard" in prompt_lower:
            categories.append("prompt_injection")
        if "roleplay" in prompt_lower or "you are now" in prompt_lower:
            categories.append("jailbreak")
        if "system" in prompt_lower:
            categories.append("system_manipulation")
        
        return DetectionResult(
            threat_score=threat_score,
            threat_level=level,
            is_malicious=is_malicious,
            categories=categories,
            confidence=0.7,  # Lower confidence for pattern matching
            details={"matches": matches, "method": "pattern_matching"}
        )


# Singleton instance
_detector = None

def get_detector(use_prompt_shield: bool = True) -> ThreatDetector:
    """Get or create detector instance"""
    global _detector
    if _detector is None:
        _detector = ThreatDetector(use_prompt_shield=use_prompt_shield)
    return _detector
