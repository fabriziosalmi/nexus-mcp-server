# -*- coding: utf-8 -*-
# enhanced_http_server.py - Enhanced HTTP API for Nexus MCP Server
"""
Enhanced HTTP wrapper that dynamically exposes ALL Nexus MCP tools via REST API.
This allows language-agnostic access to all Nexus functionality.
"""

import json
import logging
import asyncio
import sys
import traceback
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
import uvicorn

from multi_server import load_configuration, dynamically_register_tools
from mcp.server.fastmcp import FastMCP
from monitoring import get_monitoring
from monitoring_decorators import monitor_tool_execution

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)-8s] --- %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Pydantic models for API requests/responses
class ToolRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")

class ToolResponse(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    status: str
    execution_time: Optional[float] = None

class ToolInfo(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class ToolListResponse(BaseModel):
    tools: List[ToolInfo]
    count: int
    server_info: Dict[str, str]

class HealthResponse(BaseModel):
    status: str
    message: str
    tools_count: int
    server_info: Dict[str, str]

class ErrorResponse(BaseModel):
    error: str
    detail: str
    tool_name: Optional[str] = None

# Initialize FastAPI with comprehensive metadata
app = FastAPI(
    title="Nexus MCP Server - Enhanced REST API",
    description="""
    Enhanced HTTP wrapper for Nexus MCP Server that dynamically exposes ALL available tools.
    
    This API allows language-agnostic access to Nexus functionality including:
    - Mathematical calculations
    - Cryptographic operations
    - System information
    - Encoding/decoding
    - File operations
    - Network utilities
    - And many more tools...
    
    All tools are auto-discovered and exposed without manual configuration.
    """,
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Nexus MCP Server",
        "url": "https://github.com/fabriziosalmi/nexus-mcp-server",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Global variables
mcp_server = None
available_tools = {}
tools_list = []

async def get_mcp_server():
    """Dependency to get the initialized MCP server."""
    if not mcp_server:
        raise HTTPException(status_code=500, detail="MCP Server not initialized")
    return mcp_server

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP server and discover all available tools."""
    global mcp_server, available_tools, tools_list
    
    logging.info("🚀 Starting Enhanced Nexus MCP HTTP Server...")
    
    try:
        # Load configuration
        config = load_configuration()
        
        # Create FastMCP instance
        mcp_server = FastMCP("NexusServer-Enhanced")
        
        # Load tools dynamically
        dynamically_register_tools(mcp_server, config)
        
        # Discover all available tools
        tools = await mcp_server.list_tools()
        
        # Build tool registry with metadata
        available_tools = {}
        tools_list = []
        
        for tool in tools:
            tool_info = ToolInfo(
                name=tool.name,
                description=tool.description or "No description available",
                input_schema=tool.input_schema if hasattr(tool, 'input_schema') else {}
            )
            available_tools[tool.name] = tool_info
            tools_list.append(tool_info)
        
        logging.info(f"✅ Enhanced HTTP Server ready with {len(available_tools)} tools:")
        for tool_name in sorted(available_tools.keys()):
            logging.info(f"   • {tool_name}")
        
    except Exception as e:
        logging.error(f"❌ Error during initialization: {e}")
        logging.error(traceback.format_exc())
        sys.exit(1)

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with server status."""
    return HealthResponse(
        status="healthy",
        message="Nexus MCP Server Enhanced API is running",
        tools_count=len(available_tools),
        server_info={
            "name": "NexusServer-Enhanced",
            "version": "3.0.0",
            "type": "HTTP-MCP Bridge"
        }
    )

@app.get("/tools", response_model=ToolListResponse)
async def list_all_tools():
    """List all available tools with their metadata."""
    return ToolListResponse(
        tools=tools_list,
        count=len(tools_list),
        server_info={
            "name": "NexusServer-Enhanced",
            "version": "3.0.0"
        }
    )

@app.get("/tools/{tool_name}", response_model=ToolInfo)
async def get_tool_info(tool_name: str):
    """Get detailed information about a specific tool."""
    if tool_name not in available_tools:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available tools: {list(available_tools.keys())}"
        )
    return available_tools[tool_name]

@app.post("/tools/{tool_name}/execute", response_model=ToolResponse)
async def execute_tool(
    tool_name: str,
    request: ToolRequest,
    mcp: FastMCP = Depends(get_mcp_server)
):
    """Execute a specific tool with provided arguments."""
    import time
    start_time = time.time()
    monitoring = get_monitoring()
    
    if tool_name not in available_tools:
        raise HTTPException(
            status_code=404,
            detail=f"Tool '{tool_name}' not found. Available tools: {list(available_tools.keys())}"
        )
    
    try:
        # Execute the tool using the MCP server
        result = await mcp.call_tool(tool_name, request.arguments)
        
        # Handle the result format - FastMCP returns (content_blocks, result)
        if isinstance(result, tuple) and len(result) == 2:
            content_blocks, actual_result = result
            # Use the actual result if available, otherwise use content blocks
            formatted_result = actual_result if actual_result is not None else [
                block.text if hasattr(block, 'text') else str(block) 
                for block in content_blocks
            ]
        else:
            formatted_result = result
        
        execution_time = time.time() - start_time
        monitoring.record_tool_call(tool_name, "success", execution_time)
        
        return ToolResponse(
            tool_name=tool_name,
            arguments=request.arguments,
            result=formatted_result,
            status="success",
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        monitoring.record_tool_call(tool_name, "error", execution_time)
        
        error_detail = str(e)
        logging.error(f"Error executing tool '{tool_name}': {error_detail}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Error executing tool '{tool_name}': {error_detail}"
        )

@app.get("/tools/{tool_name}/execute")
async def execute_tool_get(
    tool_name: str,
    mcp: FastMCP = Depends(get_mcp_server)
):
    """Execute a tool without arguments via GET request."""
    request = ToolRequest(arguments={})
    return await execute_tool(tool_name, request, mcp)

@app.get("/metrics")
async def prometheus_metrics():
    """Prometheus metrics endpoint for monitoring."""
    monitoring = get_monitoring()
    metrics_data = monitoring.get_metrics()
    return Response(
        content=metrics_data,
        media_type=monitoring.get_content_type()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=f"HTTP {exc.status_code}",
            detail=exc.detail
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unexpected errors."""
    logging.error(f"Unexpected error: {exc}")
    logging.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred. Please check the server logs."
        ).dict()
    )

def custom_openapi():
    """Generate custom OpenAPI schema with tool-specific endpoints."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add tool-specific documentation
    if available_tools:
        openapi_schema["components"]["schemas"]["AvailableTools"] = {
            "type": "object",
            "properties": {
                tool_name: {
                    "type": "object",
                    "description": tool_info.description,
                    "properties": tool_info.input_schema.get("properties", {})
                }
                for tool_name, tool_info in available_tools.items()
            }
        }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    # Start the enhanced HTTP server
    uvicorn.run(
        "enhanced_http_server:app",
        host="0.0.0.0",
        port=9999,
        log_level="info",
        reload=False
    )