# Prometheus Monitoring for Nexus MCP Server

## Overview

This implementation adds comprehensive Prometheus monitoring to the Nexus MCP Server, making it production-ready with full observability capabilities.

## Features Implemented

### ✅ Required Metrics

1. **`mcp_tool_calls_total{tool_name, status}`** (Counter)
   - Tracks total number of tool executions
   - Labels: `tool_name` (e.g., "add", "fetch_url_content"), `status` ("success", "error")
   - Example: `mcp_tool_calls_total{tool_name="add", status="success"} 42`

2. **`mcp_tool_duration_seconds{tool_name}`** (Histogram)
   - Tracks execution duration of tools in seconds
   - Labels: `tool_name`
   - Buckets: 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, +Inf
   - Example: `mcp_tool_duration_seconds_sum{tool_name="fetch_url_content"} 1.234`

3. **`mcp_active_sessions`** (Gauge)
   - Tracks number of currently active MCP sessions
   - Example: `mcp_active_sessions 3`

### ✅ Prometheus Endpoint

- **`GET /metrics`** - Standard Prometheus scraping endpoint
- Returns metrics in Prometheus exposition format
- Content-Type: `text/plain; version=0.0.4; charset=utf-8`

## Implementation Details

### Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   HTTP Server   │    │  Monitoring  │    │   Prometheus    │
│  (http_server)  │◄──►│   Module     │◄───│    Client       │
└─────────────────┘    └──────────────┘    └─────────────────┘
         ▲                      ▲
         │                      │
┌─────────────────┐    ┌──────────────┐
│   MCP Server    │    │  Tool        │
│ (multi_server)  │    │ Execution    │
└─────────────────┘    └──────────────┘
```

### Files Added/Modified

1. **`monitoring.py`** - Core monitoring module with Prometheus metrics
2. **`monitoring_decorators.py`** - Decorators for easy monitoring integration
3. **`requirements.txt`** - Added `prometheus_client==0.21.1`
4. **`http_server.py`** - Added `/metrics` endpoint and tool execution monitoring
5. **`multi_server.py`** - Added session tracking for MCP server

### Key Features

- **Thread-safe metrics collection** using Prometheus client
- **Automatic error tracking** for failed tool executions
- **Session lifecycle tracking** for MCP server connections
- **Minimal performance overhead** with efficient metric recording
- **Production-ready configuration** with proper bucket sizing

## Usage Examples

### Starting the Server

```bash
# Start HTTP server with monitoring
python http_server.py
```

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'nexus-mcp-server'
    static_configs:
      - targets: ['localhost:9999']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Example Queries

```promql
# Tool execution rate
rate(mcp_tool_calls_total[5m])

# Average tool execution time
rate(mcp_tool_duration_seconds_sum[5m]) / rate(mcp_tool_duration_seconds_count[5m])

# Error rate by tool
rate(mcp_tool_calls_total{status="error"}[5m]) / rate(mcp_tool_calls_total[5m])

# Current active sessions
mcp_active_sessions

# Top slowest tools
topk(10, avg by (tool_name) (rate(mcp_tool_duration_seconds_sum[5m]) / rate(mcp_tool_duration_seconds_count[5m])))
```

### Grafana Dashboard Queries

```json
{
  "panels": [
    {
      "title": "Tool Execution Rate",
      "targets": [{"expr": "rate(mcp_tool_calls_total[5m])"}]
    },
    {
      "title": "Active Sessions",
      "targets": [{"expr": "mcp_active_sessions"}]
    },
    {
      "title": "Error Rate",
      "targets": [{"expr": "rate(mcp_tool_calls_total{status=\"error\"}[5m])"}]
    }
  ]
}
```

## Testing

### Manual Testing

```bash
# Test tool execution and monitoring
curl -X POST http://localhost:9999/execute \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "add", "arguments": {"a": 5, "b": 3}}'

# Check metrics
curl http://localhost:9999/metrics | grep mcp_tool
```

### Expected Output

```prometheus
# HELP mcp_tool_calls_total Total number of MCP tool calls
# TYPE mcp_tool_calls_total counter
mcp_tool_calls_total{status="success",tool_name="add"} 1.0

# HELP mcp_tool_duration_seconds Duration of MCP tool execution in seconds
# TYPE mcp_tool_duration_seconds histogram
mcp_tool_duration_seconds_bucket{le="0.005",tool_name="add"} 1.0
mcp_tool_duration_seconds_count{tool_name="add"} 1.0
mcp_tool_duration_seconds_sum{tool_name="add"} 0.001234

# HELP mcp_active_sessions Number of currently active MCP sessions
# TYPE mcp_active_sessions gauge
mcp_active_sessions 0.0
```

## Production Deployment

### Docker Integration

The monitoring is automatically included when using the provided Dockerfile:

```dockerfile
# Metrics endpoint exposed on port 9999
EXPOSE 9999
```

### Environment Variables

```bash
# Optional: Configure Prometheus metrics
export PROMETHEUS_REGISTRY_ENABLED=true
export METRICS_ENDPOINT_ENABLED=true
```

### Health Checks

```bash
# Monitor server health + metrics availability
curl -f http://localhost:9999/metrics || exit 1
```

## Benefits

1. **Full Observability** - Track all tool executions, errors, and performance
2. **Production Ready** - Industry-standard Prometheus metrics
3. **Performance Insights** - Identify slow tools and optimization opportunities  
4. **Error Monitoring** - Detect and alert on tool failures
5. **Capacity Planning** - Monitor active sessions and resource usage
6. **Dashboard Creation** - Build custom Grafana dashboards
7. **Alerting** - Set up alerts for error rates, slow performance, etc.

## Next Steps

1. **Set up Grafana dashboards** for visualization
2. **Configure alerting rules** for error rates and performance
3. **Add custom metrics** for specific business requirements
4. **Implement log correlation** with distributed tracing
5. **Monitor resource usage** (CPU, memory, disk) alongside tool metrics