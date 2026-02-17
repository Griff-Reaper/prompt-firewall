"""
Audit Logger - Track all firewall decisions and threats
"""
import json
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import AuditLog, Action, ThreatLevel, FirewallRequest, FirewallResponse


class AuditLogger:
    """
    Audit logger for compliance and threat tracking
    """
    
    def __init__(self, log_dir: str = "logs", log_to_file: bool = True):
        """
        Initialize audit logger
        
        Args:
            log_dir: Directory for log files
            log_to_file: Whether to write logs to files
        """
        self.log_dir = Path(log_dir)
        self.log_to_file = log_to_file
        
        if self.log_to_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create log files
            self.audit_log_path = self.log_dir / "audit.jsonl"
            self.threats_log_path = self.log_dir / "threats.jsonl"
            self.metrics_log_path = self.log_dir / "metrics.jsonl"
        
        # In-memory stats
        self.stats = {
            "total_requests": 0,
            "blocked": 0,
            "sanitized": 0,
            "allowed": 0,
            "threats_detected": 0
        }
    
    def log_request(self, request: FirewallRequest, 
                   response: FirewallResponse) -> str:
        """
        Log firewall request and response
        
        Args:
            request: Incoming request
            response: Firewall decision
        
        Returns:
            Request ID
        """
        request_id = str(uuid.uuid4())
        
        # Create audit log entry
        log_entry = AuditLog(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            user_id=request.user_id,
            session_id=request.session_id,
            prompt=request.prompt,
            action=response.action,
            threat_score=response.threat_score,
            threat_level=response.threat_level,
            policy_matched=response.policy_match.policy_name if response.policy_match else None,
            metadata={
                "processing_time_ms": response.processing_time_ms,
                "sanitized": response.sanitized_prompt is not None,
                "detection_details": response.detection.details if response.detection else {}
            }
        )
        
        # Write to file
        if self.log_to_file:
            self._write_log(self.audit_log_path, log_entry.to_dict())
            
            # Write threats to separate file
            if response.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                self._write_log(self.threats_log_path, {
                    **log_entry.to_dict(),
                    "threat_details": {
                        "categories": response.detection.categories if response.detection else [],
                        "confidence": response.detection.confidence if response.detection else 0.0
                    }
                })
        
        # Update stats
        self.stats["total_requests"] += 1
        
        if response.action == Action.BLOCK:
            self.stats["blocked"] += 1
        elif response.action == Action.SANITIZE:
            self.stats["sanitized"] += 1
        elif response.action == Action.ALLOW:
            self.stats["allowed"] += 1
        
        if response.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            self.stats["threats_detected"] += 1
        
        return request_id
    
    def _write_log(self, path: Path, data: Dict[str, Any]):
        """Write JSON line to log file"""
        try:
            with open(path, 'a') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            print(f"[!] Failed to write log: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics"""
        total = self.stats["total_requests"]
        
        return {
            **self.stats,
            "block_rate": (self.stats["blocked"] / total * 100) if total > 0 else 0,
            "sanitize_rate": (self.stats["sanitized"] / total * 100) if total > 0 else 0,
            "threat_rate": (self.stats["threats_detected"] / total * 100) if total > 0 else 0
        }
    
    def get_recent_threats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent threat entries"""
        if not self.log_to_file or not self.threats_log_path.exists():
            return []
        
        threats = []
        try:
            with open(self.threats_log_path, 'r') as f:
                lines = f.readlines()
                # Get last N lines
                for line in lines[-limit:]:
                    threats.append(json.loads(line))
        except Exception as e:
            print(f"[!] Failed to read threats: {e}")
        
        return threats
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent audit logs"""
        if not self.log_to_file or not self.audit_log_path.exists():
            return []
        
        logs = []
        try:
            with open(self.audit_log_path, 'r') as f:
                lines = f.readlines()
                for line in lines[-limit:]:
                    logs.append(json.loads(line))
        except Exception as e:
            print(f"[!] Failed to read logs: {e}")
        
        return logs
    
    def clear_logs(self):
        """Clear all log files (use with caution!)"""
        if self.log_to_file:
            for path in [self.audit_log_path, self.threats_log_path, self.metrics_log_path]:
                if path.exists():
                    path.unlink()
        
        # Reset stats
        self.stats = {
            "total_requests": 0,
            "blocked": 0,
            "sanitized": 0,
            "allowed": 0,
            "threats_detected": 0
        }


# Singleton instance
_logger = None

def get_logger(log_dir: str = "logs", log_to_file: bool = True) -> AuditLogger:
    """Get or create logger instance"""
    global _logger
    if _logger is None:
        _logger = AuditLogger(log_dir=log_dir, log_to_file=log_to_file)
    return _logger
