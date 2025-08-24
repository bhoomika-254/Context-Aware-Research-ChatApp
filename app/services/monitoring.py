"""Monitoring and observability utilities for token usage and performance tracking."""

import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class ExecutionMetrics:
    """Track execution metrics for API calls."""
    request_id: str
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None
    token_usage: Dict[str, int] = field(default_factory=dict)
    node_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    error: Optional[str] = None
    
    def finish(self, error: Optional[str] = None):
        """Mark execution as finished and calculate duration."""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        self.error = error
    
    def add_node_metrics(self, node_name: str, duration: float, tokens_used: int = 0):
        """Add metrics for a specific node execution."""
        self.node_metrics[node_name] = {
            "duration_seconds": duration,
            "tokens_used": tokens_used,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update total token usage
        if tokens_used > 0:
            self.token_usage[node_name] = self.token_usage.get(node_name, 0) + tokens_used
    
    def get_total_tokens(self) -> int:
        """Get total tokens used across all nodes."""
        return sum(self.token_usage.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for logging/storage."""
        return {
            "request_id": self.request_id,
            "duration_seconds": self.duration_seconds,
            "total_tokens": self.get_total_tokens(),
            "token_breakdown": self.token_usage,
            "node_metrics": self.node_metrics,
            "error": self.error,
            "timestamp": datetime.now().isoformat()
        }

class MonitoringService:
    """Service for tracking and reporting execution metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger("monitoring")
        self.active_executions: Dict[str, ExecutionMetrics] = {}
    
    def start_execution(self, request_id: str) -> ExecutionMetrics:
        """Start tracking a new execution."""
        metrics = ExecutionMetrics(
            request_id=request_id,
            start_time=time.time()
        )
        self.active_executions[request_id] = metrics
        self.logger.info(f"Started tracking execution {request_id}")
        return metrics
    
    def finish_execution(self, request_id: str, error: Optional[str] = None) -> Optional[ExecutionMetrics]:
        """Finish tracking an execution and log metrics."""
        if request_id not in self.active_executions:
            self.logger.warning(f"No active execution found for {request_id}")
            return None
        
        metrics = self.active_executions[request_id]
        metrics.finish(error)
        
        # Log comprehensive metrics
        self._log_execution_metrics(metrics)
        
        # Clean up
        del self.active_executions[request_id]
        
        return metrics
    
    def add_node_metrics(self, request_id: str, node_name: str, duration: float, tokens_used: int = 0):
        """Add metrics for a node execution."""
        if request_id in self.active_executions:
            self.active_executions[request_id].add_node_metrics(node_name, duration, tokens_used)
    
    def _log_execution_metrics(self, metrics: ExecutionMetrics):
        """Log detailed execution metrics."""
        if metrics.error:
            self.logger.error(f"Execution {metrics.request_id} failed: {metrics.error}")
        else:
            self.logger.info(f"Execution {metrics.request_id} completed successfully")
        
        # Log performance metrics
        self.logger.info(
            f"Performance Metrics - Request: {metrics.request_id}, "
            f"Duration: {metrics.duration_seconds:.2f}s, "
            f"Total Tokens: {metrics.get_total_tokens()}"
        )
        
        # Log node-specific metrics
        for node_name, node_metrics in metrics.node_metrics.items():
            self.logger.info(
                f"Node Metrics - {node_name}: "
                f"Duration: {node_metrics['duration_seconds']:.2f}s, "
                f"Tokens: {node_metrics['tokens_used']}"
            )
        
        # Log token breakdown
        if metrics.token_usage:
            token_breakdown = ", ".join([f"{node}: {tokens}" for node, tokens in metrics.token_usage.items()])
            self.logger.info(f"Token Breakdown - {token_breakdown}")
    
    def get_execution_summary(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get current execution summary."""
        if request_id in self.active_executions:
            return self.active_executions[request_id].to_dict()
        return None

# Global monitoring service instance
monitoring_service = MonitoringService()

def estimate_token_usage(text: str, model_type: str = "gemini") -> int:
    """
    Estimate token usage for a given text.
    This is a rough estimation - actual usage may vary.
    """
    # Rough estimation: ~4 characters per token for most models
    base_tokens = len(text) // 4
    
    # Adjust based on model type
    if model_type.lower() == "gemini":
        # Gemini tends to be more efficient
        return int(base_tokens * 0.9)
    elif "gpt" in model_type.lower():
        # GPT models
        return base_tokens
    else:
        # Default estimation
        return base_tokens

def track_llm_call(request_id: str, node_name: str, prompt: str, response: str, model_type: str = "gemini"):
    """Track token usage for an LLM call."""
    input_tokens = estimate_token_usage(prompt, model_type)
    output_tokens = estimate_token_usage(response, model_type)
    total_tokens = input_tokens + output_tokens
    
    # Log the LLM call details
    logger = logging.getLogger("llm_tracking")
    logger.info(
        f"LLM Call - Request: {request_id}, Node: {node_name}, "
        f"Model: {model_type}, Input Tokens: {input_tokens}, "
        f"Output Tokens: {output_tokens}, Total: {total_tokens}"
    )
    
    return total_tokens
