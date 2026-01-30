"""
TrustLayer AI: PII Redaction Engine using Microsoft Presidio
"""
import asyncio
import json
import logging
from typing import Dict, List, Any, Tuple
import redis
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import RecognizerResult, OperatorConfig

logger = logging.getLogger(__name__)

class PII_Redactor:
    """
    Presidio-based NLP scrubbing logic with Redis-backed mapping system
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.entities = config["presidio"]["entities"]
        
        # Initialize Presidio engines
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Initialize Redis connection
        redis_config = config["redis"]
        self.redis_client = redis.Redis(
            host=redis_config["host"],
            port=redis_config["port"],
            db=redis_config["db"],
            decode_responses=True
        )
        self.session_ttl = redis_config["session_ttl"]
        
        logger.info("PII Redactor initialized with Presidio and Redis")
    
    def _generate_placeholder(self, entity_type: str, entity_value: str, session_id: str) -> str:
        """Generate a unique placeholder for the detected entity"""
        # Get existing count for this entity type in this session
        count_key = f"session:{session_id}:count:{entity_type}"
        count = self.redis_client.incr(count_key)
        self.redis_client.expire(count_key, self.session_ttl)
        
        placeholder = f"[CONFIDENTIAL_{entity_type}_{count}]"
        
        # Store the mapping
        mapping_key = f"session:{session_id}:mapping:{placeholder}"
        self.redis_client.setex(mapping_key, self.session_ttl, entity_value)
        
        return placeholder
    
    async def redact_text(self, text: str, session_id: str) -> Tuple[str, Dict[str, str]]:
        """
        Redact PII from text and return redacted text with mapping
        """
        if not text.strip():
            return text, {}
        
        try:
            # Analyze text for PII entities
            analyzer_results = self.analyzer.analyze(
                text=text,
                entities=self.entities,
                language='en'
            )
            
            if not analyzer_results:
                return text, {}
            
            # Sort results by start position (reverse order for replacement)
            analyzer_results.sort(key=lambda x: x.start, reverse=True)
            
            redacted_text = text
            mapping = {}
            
            # Replace each detected entity with a placeholder
            for result in analyzer_results:
                entity_value = text[result.start:result.end]
                placeholder = self._generate_placeholder(
                    result.entity_type, 
                    entity_value, 
                    session_id
                )
                
                # Replace in text
                redacted_text = (
                    redacted_text[:result.start] + 
                    placeholder + 
                    redacted_text[result.end:]
                )
                
                mapping[placeholder] = entity_value
            
            logger.info(f"Redacted {len(analyzer_results)} PII entities for session {session_id}")
            return redacted_text, mapping
            
        except Exception as e:
            logger.error(f"Error during PII redaction: {e}")
            return text, {}
    
    async def restore_pii(self, response_data: Any, mapping: Dict[str, str], session_id: str) -> Any:
        """
        Restore PII in AI response by replacing placeholders with original values
        """
        if not mapping:
            return response_data
        
        try:
            # Convert response to string for processing
            response_str = json.dumps(response_data) if not isinstance(response_data, str) else response_data
            
            # Get all mappings for this session from Redis
            session_mappings = {}
            for placeholder in mapping.keys():
                mapping_key = f"session:{session_id}:mapping:{placeholder}"
                original_value = self.redis_client.get(mapping_key)
                if original_value:
                    session_mappings[placeholder] = original_value
            
            # Replace placeholders with original values
            restored_text = response_str
            for placeholder, original_value in session_mappings.items():
                restored_text = restored_text.replace(placeholder, original_value)
            
            # Convert back to original format
            if isinstance(response_data, str):
                return restored_text
            else:
                return json.loads(restored_text)
                
        except Exception as e:
            logger.error(f"Error during PII restoration: {e}")
            return response_data
    
    async def restore_pii_text(self, text: str, mapping: Dict[str, str], session_id: str) -> str:
        """
        Restore PII in plain text response
        """
        if not mapping or not text:
            return text
        
        try:
            restored_text = text
            
            # Get all mappings for this session from Redis
            for placeholder in mapping.keys():
                mapping_key = f"session:{session_id}:mapping:{placeholder}"
                original_value = self.redis_client.get(mapping_key)
                if original_value:
                    restored_text = restored_text.replace(placeholder, original_value)
            
            return restored_text
            
        except Exception as e:
            logger.error(f"Error during text PII restoration: {e}")
            return text
    
    def cleanup_session(self, session_id: str):
        """
        Clean up Redis mappings for a session
        """
        try:
            # Get all keys for this session
            pattern = f"session:{session_id}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleaned up {len(keys)} keys for session {session_id}")
                
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
    
    async def get_session_stats(self, session_id: str) -> Dict[str, int]:
        """
        Get statistics for a session
        """
        try:
            stats = {}
            
            # Get counts for each entity type
            for entity_type in self.entities:
                count_key = f"session:{session_id}:count:{entity_type}"
                count = self.redis_client.get(count_key)
                if count:
                    stats[entity_type] = int(count)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting session stats: {e}")
            return {}