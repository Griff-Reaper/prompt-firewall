"""
Data models for Prompt Firewall
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime


class ThreatLevel(Enum):
    """Threat severity levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Action(Enum):
    """Policy actions"""
    ALLOW = "allow"
    BLOCK = "block"
    SANITIZE = "sanitize"
    LOG = "log"
    ALERT = "alert"


@dataclass
class DetectionResult:
    """Result from threat detection"""
    threat_score: float  # 0-100
    threat_level: ThreatLevel
    is_malicious: bool
    categories: List[str] = field(default_factory=list)
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyMatch:
    """Matched policy rule"""
    policy_name: str
    action: Action
    severity: ThreatLevel
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FirewallRequest:
    """Incoming request to firewall"""
    prompt: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FirewallResponse:
    """Firewall decision"""
    action: Action
    allowed: bool
    original_prompt: str
    sanitized_prompt: Optional[str] = None
    threat_score: float = 0.0
    threat_level: ThreatLevel = ThreatLevel.SAFE
    detection: Optional[DetectionResult] = None
    policy_match: Optional[PolicyMatch] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "action": self.action.value,
            "allowed": self.allowed,
            "original_prompt": self.original_prompt,
            "sanitized_prompt": self.sanitized_prompt,
            "threat_score": self.threat_score,
            "threat_level": self.threat_level.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class AuditLog:
    """Audit log entry"""
    request_id: str
    timestamp: datetime
    user_id: Optional[str]
    session_id: Optional[str]
    prompt: str
    action: Action
    threat_score: float
    threat_level: ThreatLevel
    policy_matched: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "prompt": self.prompt,
            "action": self.action.value,
            "threat_score": self.threat_score,
            "threat_level": self.threat_level.value,
            "policy_matched": self.policy_matched,
            "metadata": self.metadata
        }
