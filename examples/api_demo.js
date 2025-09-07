/**
 * JavaScript/Node.js example for using Nexus MCP Server via REST API
 * Demonstrates language-agnostic access to all Nexus tools
 */

const https = require('https');
const http = require('http');

// Configuration
const NEXUS_BASE_URL = 'http://localhost:9999';

/**
 * Make HTTP request to Nexus API
 */
async function makeRequest(path, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const url = new URL(NEXUS_BASE_URL + path);
        const options = {
            hostname: url.hostname,
            port: url.port,
            path: url.pathname,
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(body);
                    resolve(parsed);
                } catch (e) {
                    resolve(body);
                }
            });
        });

        req.on('error', reject);

        if (data) {
            req.write(JSON.stringify(data));
        }
        req.end();
    });
}

/**
 * Call a Nexus tool
 */
async function callTool(toolName, args = {}) {
    const path = `/tools/${toolName}/execute`;
    const data = { arguments: args };
    return await makeRequest(path, 'POST', data);
}

/**
 * Main demonstration
 */
async function main() {
    console.log('🚀 Nexus MCP Server - JavaScript/Node.js Demo');
    console.log('================================================');

    try {
        // Check server health
        const health = await makeRequest('/');
        console.log(`✅ Server is ${health.status} with ${health.tools_count} tools`);

        console.log('\n📊 Mathematical Operations:');
        
        // Addition
        let result = await callTool('add', { a: 25, b: 17 });
        console.log(`25 + 17 = ${result.result.result}`);

        // Multiplication
        result = await callTool('multiply', { a: 8, b: 12 });
        console.log(`8 × 12 = ${result.result.result}`);

        console.log('\n🔐 Cryptographic Operations:');
        
        // Generate hash
        result = await callTool('generate_hash', { 
            text: 'Hello from JavaScript!', 
            algorithm: 'sha256' 
        });
        console.log(`Hash: ${result.result.result}`);

        // Generate UUID
        result = await callTool('generate_uuid4');
        console.log(`UUID: ${result.result.result}`);

        console.log('\n🔤 Encoding Operations:');
        
        // Base64 encoding
        const originalText = 'JavaScript ♥ Nexus';
        result = await callTool('base64_encode', { text: originalText });
        const encoded = result.result.result.split(': ')[1];
        console.log(`Original: ${originalText}`);
        console.log(`Base64: ${encoded}`);

        // Base64 decoding
        result = await callTool('base64_decode', { encoded_text: encoded });
        const decoded = result.result.result.split(': ')[1];
        console.log(`Decoded: ${decoded}`);

        console.log('\n✅ Data Validation:');
        
        // Email validation
        const emails = ['user@example.com', 'invalid.email', 'test@nexus.io'];
        for (const email of emails) {
            result = await callTool('validate_email', { email });
            const isValid = result.result.result.includes('✅ SI');
            console.log(`${email}: ${isValid ? '✅ VALID' : '❌ INVALID'}`);
        }

        console.log('\n⏰ Date/Time Operations:');
        
        // Current timestamp
        result = await callTool('current_timestamp');
        console.log('Current timestamp:');
        console.log(result.result.result);

        console.log('\n🔍 Tool Discovery:');
        
        // List available tools
        const tools = await makeRequest('/tools');
        console.log(`Total available tools: ${tools.count}`);
        
        // Show sample of available tools
        const sampleTools = tools.tools.slice(0, 10);
        console.log('\nSample tools:');
        sampleTools.forEach(tool => {
            console.log(`  • ${tool.name}: ${tool.description.substring(0, 50)}...`);
        });

        console.log('\n⚡ Performance Test:');
        
        // Measure performance
        const start = Date.now();
        await callTool('add', { a: 1, b: 1 });
        const end = Date.now();
        console.log(`Simple operation latency: ${end - start}ms`);

        console.log('\n🎉 JavaScript demo completed successfully!');
        console.log('This shows how Nexus tools can be used from any language with HTTP support.');

    } catch (error) {
        console.error('❌ Error:', error.message);
        console.log('Make sure the Nexus server is running on http://localhost:9999');
    }
}

// Run the demo
if (require.main === module) {
    main();
}

module.exports = { makeRequest, callTool };