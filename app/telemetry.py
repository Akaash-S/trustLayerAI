"""
TrustLayer AI: Telemetry and Metrics Collection
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import redis

logger = logging.getLogger(__name__)

class TelemetryCollector:
    """
    Collect and store telemetry data for the dashboard
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize Redis connection
        redis_config = config["redis"]
        self.redis_client = redis.Redis(
            host=redis_config["host"],
            port=redis_config["port"],
            db=redis_config["db"],
            decode_responses=True
        )
        
        logger.info("Telemetry Collector initialized")
    
    async def log_request(self, host: str, path: str, method: str, latency: float, status_code: int):
        """
        Log a request for telemetry tracking
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Store request data
            request_data = {
                'timestamp': timestamp,
                'host': host,
                'path': path,
                'method': method,
                'latency': latency,
                'status_code': status_code
            }
            
            # Add to requests list (keep last 1000 requests)
            self.redis_client.lpush('requests', json.dumps(request_data))
            self.redis_client.ltrim('requests', 0, 999)
            
            # Update counters
            self.redis_client.incr('total_requests')
            self.redis_client.incr(f'requests_by_host:{host}')
            self.redis_client.incr(f'requests_by_status:{status_code}')
            
            # Update latency stats
            self.redis_client.lpush('latencies', latency)
            self.redis_client.ltrim('latencies', 0, 999)
            
        except Exception as e:
            logger.error(f"Error logging request: {e}")
    
    async def log_pii_redaction(self, entities_count: int, session_id: str):
        """
        Log PII redaction event
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Store PII redaction data
            pii_data = {
                'timestamp': timestamp,
                'session_id': session_id,
                'entities_redacted': entities_count
            }
            
            # Add to PII events list
            self.redis_client.lpush('pii_events', json.dumps(pii_data))
            self.redis_client.ltrim('pii_events', 0, 999)
            
            # Update PII counters
            self.redis_client.incr('total_pii_entities_blocked')
            self.redis_client.incr(f'pii_events_by_session:{session_id}')
            
        except Exception as e:
            logger.error(f"Error logging PII redaction: {e}")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics for the dashboard
        """
        try:
            # Basic counters
            total_requests = int(self.redis_client.get('total_requests') or 0)
            total_pii_blocked = int(self.redis_client.get('total_pii_entities_blocked') or 0)
            
            # Recent requests (last 100)
            recent_requests_raw = self.redis_client.lrange('requests', 0, 99)
            recent_requests = [json.loads(req) for req in recent_requests_raw]
            
            # Recent PII events
            recent_pii_raw = self.redis_client.lrange('pii_events', 0, 99)
            recent_pii_events = [json.loads(event) for event in recent_pii_raw]
            
            # Latency statistics
            latencies_raw = self.redis_client.lrange('latencies', 0, 999)
            latencies = [float(lat) for lat in latencies_raw]
            
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            max_latency = max(latencies) if latencies else 0
            min_latency = min(latencies) if latencies else 0
            
            # Requests by host
            host_stats = {}
            for key in self.redis_client.keys('requests_by_host:*'):
                host = key.split(':', 1)[1]
                count = int(self.redis_client.get(key) or 0)
                host_stats[host] = count
            
            # Status code distribution
            status_stats = {}
            for key in self.redis_client.keys('requests_by_status:*'):
                status = key.split(':', 1)[1]
                count = int(self.redis_client.get(key) or 0)
                status_stats[status] = count
            
            # Calculate compliance status (based on PII blocking effectiveness)
            compliance_score = min(100, (total_pii_blocked / max(total_requests, 1)) * 100)
            
            return {
                'summary': {
                    'total_requests': total_requests,
                    'total_pii_entities_blocked': total_pii_blocked,
                    'compliance_score': round(compliance_score, 2),
                    'avg_latency_ms': round(avg_latency * 1000, 2),
                    'max_latency_ms': round(max_latency * 1000, 2),
                    'min_latency_ms': round(min_latency * 1000, 2)
                },
                'traffic': {
                    'by_host': host_stats,
                    'by_status': status_stats,
                    'recent_requests': recent_requests[:20]  # Last 20 requests
                },
                'security': {
                    'recent_pii_events': recent_pii_events[:20],
                    'pii_blocking_rate': round((total_pii_blocked / max(total_requests, 1)) * 100, 2)
                },
                'performance': {
                    'latency_distribution': latencies[:100],  # Last 100 latencies
                    'avg_latency': avg_latency,
                    'latency_percentiles': self._calculate_percentiles(latencies)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return {
                'error': str(e),
                'summary': {
                    'total_requests': 0,
                    'total_pii_entities_blocked': 0,
                    'compliance_score': 0,
                    'avg_latency_ms': 0
                }
            }
    
    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """
        Calculate latency percentiles
        """
        if not values:
            return {'p50': 0, 'p90': 0, 'p95': 0, 'p99': 0}
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        return {
            'p50': sorted_values[int(n * 0.5)] if n > 0 else 0,
            'p90': sorted_values[int(n * 0.9)] if n > 0 else 0,
            'p95': sorted_values[int(n * 0.95)] if n > 0 else 0,
            'p99': sorted_values[int(n * 0.99)] if n > 0 else 0
        }
    
    async def get_real_time_stats(self) -> Dict[str, Any]:
        """
        Get real-time statistics for live dashboard updates
        """
        try:
            # Get requests from last 5 minutes
            five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
            
            recent_requests_raw = self.redis_client.lrange('requests', 0, 999)
            recent_requests = []
            
            for req_raw in recent_requests_raw:
                req = json.loads(req_raw)
                req_time = datetime.fromisoformat(req['timestamp'])
                if req_time >= five_minutes_ago:
                    recent_requests.append(req)
            
            # Calculate real-time metrics
            current_rps = len(recent_requests) / 300  # requests per second over 5 minutes
            
            # Get active sessions (sessions with activity in last hour)
            hour_ago = datetime.utcnow() - timedelta(hours=1)
            active_sessions = set()
            
            recent_pii_raw = self.redis_client.lrange('pii_events', 0, 999)
            for event_raw in recent_pii_raw:
                event = json.loads(event_raw)
                event_time = datetime.fromisoformat(event['timestamp'])
                if event_time >= hour_ago:
                    active_sessions.add(event['session_id'])
            
            return {
                'current_rps': round(current_rps, 2),
                'active_sessions': len(active_sessions),
                'recent_activity': len(recent_requests),
                'last_update': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting real-time stats: {e}")
            return {
                'current_rps': 0,
                'active_sessions': 0,
                'recent_activity': 0,
                'last_update': datetime.utcnow().isoformat(),
                'error': str(e)
            }