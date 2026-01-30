"""
TrustLayer AI: Master Builder - FastAPI Core with Dynamic Routing
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse

import httpx
import yaml
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .redactor import PII_Redactor
from .extractors import FileExtractor
from .telemetry import TelemetryCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

app = FastAPI(title="TrustLayer AI Proxy", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
redactor = PII_Redactor(config)
extractor = FileExtractor()
telemetry = TelemetryCollector(config)

class SecurityGuardrails:
    """Security checks for prompt injection and domain validation"""
    
    def __init__(self, config: Dict[str, Any]):
        self.allowed_domains = config["allowed_domains"]
        self.injection_patterns = config["security"]["prompt_injection_patterns"]
    
    def check_domain(self, host: str) -> bool:
        """Validate if the target domain is allowed"""
        return host in self.allowed_domains
    
    def check_prompt_injection(self, text: str) -> bool:
        """Check for prompt injection patterns"""
        text_lower = text.lower()
        for pattern in self.injection_patterns:
            if pattern in text_lower:
                logger.warning(f"Prompt injection detected: {pattern}")
                return True
        return False

security = SecurityGuardrails(config)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for telemetry"""
    start_time = asyncio.get_event_loop().time()
    
    response = await call_next(request)
    
    process_time = asyncio.get_event_loop().time() - start_time
    await telemetry.log_request(
        host=request.headers.get("host", "unknown"),
        path=request.url.path,
        method=request.method,
        latency=process_time,
        status_code=response.status_code
    )
    
    return response

async def extract_and_redact_content(request: Request) -> tuple[str, Dict[str, str]]:
    """Extract content from request and redact PII"""
    content_type = request.headers.get("content-type", "")
    
    if "multipart/form-data" in content_type:
        # Handle file uploads
        form = await request.form()
        extracted_text = ""
        
        for field_name, field_value in form.items():
            if hasattr(field_value, 'file'):
                # It's a file upload
                file_content = await field_value.read()
                filename = getattr(field_value, 'filename', '')
                
                if filename.endswith('.pdf'):
                    extracted_text += extractor.extract_pdf(file_content)
                elif filename.endswith(('.xlsx', '.xls', '.csv')):
                    extracted_text += extractor.extract_spreadsheet(file_content, filename)
                else:
                    extracted_text += file_content.decode('utf-8', errors='ignore')
        
        # Redact the extracted text
        redacted_text, mapping = await redactor.redact_text(extracted_text, request.client.host)
        return redacted_text, mapping
    
    else:
        # Handle JSON/text content
        body = await request.body()
        if body:
            try:
                json_data = json.loads(body)
                # Extract text from common AI API formats
                text_content = ""
                
                if "messages" in json_data:
                    # OpenAI/Anthropic format
                    for message in json_data["messages"]:
                        if isinstance(message.get("content"), str):
                            text_content += message["content"] + "\n"
                        elif isinstance(message.get("content"), list):
                            for content_item in message["content"]:
                                if content_item.get("type") == "text":
                                    text_content += content_item.get("text", "") + "\n"
                
                elif "prompt" in json_data:
                    # Other formats
                    text_content = json_data["prompt"]
                
                # Check for prompt injection
                if security.check_prompt_injection(text_content):
                    raise HTTPException(status_code=400, detail="Potential prompt injection detected")
                
                # Redact PII
                redacted_text, mapping = await redactor.redact_text(text_content, request.client.host)
                
                # Update the JSON with redacted content
                if "messages" in json_data:
                    for message in json_data["messages"]:
                        if isinstance(message.get("content"), str):
                            message["content"] = redacted_text
                elif "prompt" in json_data:
                    json_data["prompt"] = redacted_text
                
                return json.dumps(json_data), mapping
                
            except json.JSONDecodeError:
                # Treat as plain text
                text_content = body.decode('utf-8', errors='ignore')
                if security.check_prompt_injection(text_content):
                    raise HTTPException(status_code=400, detail="Potential prompt injection detected")
                
                redacted_text, mapping = await redactor.redact_text(text_content, request.client.host)
                return redacted_text, mapping
    
    return "", {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "TrustLayer AI Proxy"}

@app.get("/metrics")
async def get_metrics():
    """Get telemetry metrics"""
    return await telemetry.get_metrics()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_request(request: Request, path: str, background_tasks: BackgroundTasks):
    """
    Catch-all route that dynamically routes requests based on Host header
    """
    # Extract target host from headers
    host = request.headers.get("host")
    if not host:
        raise HTTPException(status_code=400, detail="Host header required")
    
    # Security check: validate allowed domains
    if not security.check_domain(host):
        logger.warning(f"Blocked request to unauthorized domain: {host}")
        raise HTTPException(status_code=403, detail=f"Domain {host} not allowed")
    
    # Build target URL
    scheme = "https"  # Always use HTTPS for AI APIs
    target_url = f"{scheme}://{host}/{path}"
    
    # Extract and redact content
    redacted_content, pii_mapping = await extract_and_redact_content(request)
    
    # Prepare headers (remove host header to avoid conflicts)
    headers = dict(request.headers)
    headers.pop("host", None)
    
    # Log PII redaction
    if pii_mapping:
        await telemetry.log_pii_redaction(len(pii_mapping), request.client.host)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Forward the request
            if request.method == "GET":
                response = await client.get(
                    target_url,
                    headers=headers,
                    params=request.query_params
                )
            else:
                response = await client.request(
                    method=request.method,
                    url=target_url,
                    headers=headers,
                    content=redacted_content.encode() if redacted_content else await request.body(),
                    params=request.query_params
                )
            
            # Process response and restore PII
            response_content = response.content
            if pii_mapping and response_content:
                try:
                    response_json = json.loads(response_content)
                    restored_response = await redactor.restore_pii(response_json, pii_mapping, request.client.host)
                    response_content = json.dumps(restored_response).encode()
                except json.JSONDecodeError:
                    # Handle non-JSON responses
                    response_text = response_content.decode('utf-8', errors='ignore')
                    restored_text = await redactor.restore_pii_text(response_text, pii_mapping, request.client.host)
                    response_content = restored_text.encode()
            
            # Return response
            return StreamingResponse(
                iter([response_content]),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )
            
    except httpx.RequestError as e:
        logger.error(f"Request failed: {e}")
        raise HTTPException(status_code=502, detail=f"Proxy request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal proxy error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config["proxy"]["host"],
        port=config["proxy"]["port"],
        reload=True
    )