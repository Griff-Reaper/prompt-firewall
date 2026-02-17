"""
Policy Engine - Rule-based decision making
"""
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path

from .models import Action, ThreatLevel, DetectionResult, PolicyMatch


class Policy:
    """Single policy rule"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize policy from config
        
        Args:
            config: Policy configuration dict
        """
        self.name = config.get("name", "unnamed")
        self.enabled = config.get("enabled", True)
        self.action = Action(config.get("action", "log"))
        self.severity = ThreatLevel(config.get("severity", "medium"))
        self.threshold = config.get("threshold", 0.5)
        self.description = config.get("description", "")
        self.conditions = config.get("conditions", {})
    
    def matches(self, detection: DetectionResult) -> bool:
        """
        Check if detection matches this policy
        
        Args:
            detection: Detection result to evaluate
        
        Returns:
            True if policy matches
        """
        if not self.enabled:
            return False
        
        # Check threat score threshold
        if detection.threat_score / 100 < self.threshold:
            return False
        
        # Check severity level
        severity_order = {
            ThreatLevel.SAFE: 0,
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4
        }
        
        if severity_order[detection.threat_level] < severity_order[self.severity]:
            return False
        
        # Check categories if specified
        if "categories" in self.conditions:
            required_cats = self.conditions["categories"]
            if not any(cat in detection.categories for cat in required_cats):
                return False
        
        return True
    
    def to_match(self, detection: DetectionResult) -> PolicyMatch:
        """Convert to PolicyMatch"""
        return PolicyMatch(
            policy_name=self.name,
            action=self.action,
            severity=self.severity,
            reason=self.description or f"Matched policy: {self.name}",
            metadata={
                "threshold": self.threshold,
                "detection_score": detection.threat_score
            }
        )


class PolicyEngine:
    """
    Policy Engine - Evaluates detection results against policies
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize policy engine
        
        Args:
            config_path: Path to YAML policy configuration
        """
        self.policies: List[Policy] = []
        
        if config_path:
            self.load_policies(config_path)
        else:
            self._load_default_policies()
    
    def load_policies(self, config_path: str):
        """Load policies from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.policies = []
            for policy_config in config.get("policies", []):
                policy = Policy(policy_config)
                self.policies.append(policy)
            
            print(f"[✓] Loaded {len(self.policies)} policies from {config_path}")
        
        except Exception as e:
            print(f"[!] Failed to load policies: {e}")
            self._load_default_policies()
    
    def _load_default_policies(self):
        """Load default hardcoded policies"""
        default_policies = [
            {
                "name": "block_critical_threats",
                "enabled": True,
                "action": "block",
                "severity": "critical",
                "threshold": 0.85,
                "description": "Block critical threats immediately"
            },
            {
                "name": "sanitize_high_threats",
                "enabled": True,
                "action": "sanitize",
                "severity": "high",
                "threshold": 0.65,
                "description": "Sanitize high-severity prompts"
            },
            {
                "name": "log_medium_threats",
                "enabled": True,
                "action": "log",
                "severity": "medium",
                "threshold": 0.40,
                "description": "Log medium-severity prompts"
            },
            {
                "name": "allow_safe_prompts",
                "enabled": True,
                "action": "allow",
                "severity": "safe",
                "threshold": 0.0,
                "description": "Allow safe prompts"
            }
        ]
        
        self.policies = [Policy(config) for config in default_policies]
        print(f"[✓] Loaded {len(self.policies)} default policies")
    
    def evaluate(self, detection: DetectionResult) -> Optional[PolicyMatch]:
        """
        Evaluate detection against all policies
        
        Args:
            detection: Detection result
        
        Returns:
            First matching PolicyMatch, or None
        """
        # Policies are evaluated in order - first match wins
        for policy in self.policies:
            if policy.matches(detection):
                return policy.to_match(detection)
        
        # Default: allow if no policy matches
        return PolicyMatch(
            policy_name="default_allow",
            action=Action.ALLOW,
            severity=ThreatLevel.SAFE,
            reason="No policy matched - default allow"
        )
    
    def add_policy(self, policy_config: Dict[str, Any]):
        """Add new policy dynamically"""
        policy = Policy(policy_config)
        self.policies.append(policy)
    
    def remove_policy(self, name: str) -> bool:
        """Remove policy by name"""
        original_len = len(self.policies)
        self.policies = [p for p in self.policies if p.name != name]
        return len(self.policies) < original_len


# Singleton instance
_policy_engine = None

def get_policy_engine(config_path: Optional[str] = None) -> PolicyEngine:
    """Get or create policy engine instance"""
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine(config_path=config_path)
    return _policy_engine
