"""
Prompt Firewall - Core Engine

Orchestrates detection, policy evaluation, sanitization, and logging
"""
import time
from typing import Optional

from .models import (
    FirewallRequest, FirewallResponse, Action, ThreatLevel
)
from .detector import get_detector
from .policy import get_policy_engine
from .sanitizer import get_sanitizer
from .logger import get_logger


class PromptFirewall:
    """
    Main Firewall Engine
    
    Coordinates threat detection, policy enforcement, and audit logging
    """
    
    def __init__(self, 
                 policy_config: Optional[str] = None,
                 use_prompt_shield: bool = True,
                 log_dir: str = "logs",
                 enable_logging: bool = True):
        """
        Initialize firewall
        
        Args:
            policy_config: Path to policy YAML file
            use_prompt_shield: Whether to use Prompt-Shield ML models
            log_dir: Directory for audit logs
            enable_logging: Whether to enable audit logging
        """
        # Initialize components
        self.detector = get_detector(use_prompt_shield=use_prompt_shield)
        self.policy_engine = get_policy_engine(config_path=policy_config)
        self.sanitizer = get_sanitizer()
        self.logger = get_logger(log_dir=log_dir, log_to_file=enable_logging)
        
        print("\n[✓] Prompt Firewall initialized")
        print(f"    - Detection: {'Prompt-Shield ML' if use_prompt_shield else 'Pattern matching'}")
        print(f"    - Policies: {len(self.policy_engine.policies)} loaded")
        print(f"    - Logging: {'Enabled' if enable_logging else 'Disabled'}\n")
    
    def check(self, prompt: str, 
             user_id: Optional[str] = None,
             session_id: Optional[str] = None) -> FirewallResponse:
        """
        Check prompt against firewall
        
        Args:
            prompt: User prompt to analyze
            user_id: Optional user identifier
            session_id: Optional session identifier
        
        Returns:
            FirewallResponse with decision
        """
        start_time = time.time()
        
        # Create request
        request = FirewallRequest(
            prompt=prompt,
            user_id=user_id,
            session_id=session_id
        )
        
        # Step 1: Detect threats
        detection = self.detector.detect(prompt)
        
        # Step 2: Evaluate against policies
        policy_match = self.policy_engine.evaluate(detection)
        
        # Step 3: Execute policy action
        response = self._execute_action(
            request=request,
            detection=detection,
            policy_match=policy_match
        )
        
        # Calculate processing time
        response.processing_time_ms = (time.time() - start_time) * 1000
        
        # Step 4: Log request
        request_id = self.logger.log_request(request, response)
        
        return response
    
    def _execute_action(self, request, detection, policy_match) -> FirewallResponse:
        """Execute policy action"""
        
        # Determine action
        action = policy_match.action
        
        # BLOCK
        if action == Action.BLOCK:
            return FirewallResponse(
                action=Action.BLOCK,
                allowed=False,
                original_prompt=request.prompt,
                sanitized_prompt=None,
                threat_score=detection.threat_score,
                threat_level=detection.threat_level,
                detection=detection,
                policy_match=policy_match,
                message="Request blocked due to security policy"
            )
        
        # SANITIZE
        elif action == Action.SANITIZE:
            sanitized, changes = self.sanitizer.sanitize(request.prompt)
            
            return FirewallResponse(
                action=Action.SANITIZE,
                allowed=True,
                original_prompt=request.prompt,
                sanitized_prompt=sanitized,
                threat_score=detection.threat_score,
                threat_level=detection.threat_level,
                detection=detection,
                policy_match=policy_match,
                message=f"Prompt sanitized: {len(changes)} changes made"
            )
        
        # ALLOW (or LOG - same behavior)
        else:
            return FirewallResponse(
                action=Action.ALLOW,
                allowed=True,
                original_prompt=request.prompt,
                sanitized_prompt=None,
                threat_score=detection.threat_score,
                threat_level=detection.threat_level,
                detection=detection,
                policy_match=policy_match,
                message="Request allowed"
            )
    
    def get_stats(self):
        """Get firewall statistics"""
        return self.logger.get_stats()
    
    def get_recent_threats(self, limit: int = 10):
        """Get recent threat detections"""
        return self.logger.get_recent_threats(limit=limit)


# Convenience function
def create_firewall(policy_config: Optional[str] = None,
                   use_prompt_shield: bool = True,
                   log_dir: str = "logs",
                   enable_logging: bool = True) -> PromptFirewall:
    """
    Create firewall instance
    
    Args:
        policy_config: Path to policy YAML
        use_prompt_shield: Use ML detection
        log_dir: Log directory
        enable_logging: Enable logging
    
    Returns:
        PromptFirewall instance
    """
    return PromptFirewall(
        policy_config=policy_config,
        use_prompt_shield=use_prompt_shield,
        log_dir=log_dir,
        enable_logging=enable_logging
    )
