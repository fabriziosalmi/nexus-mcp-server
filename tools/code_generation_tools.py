# -*- coding: utf-8 -*-
# tools/code_generation_tools.py
import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
import re
from datetime import datetime, timezone
import hashlib
import uuid

def register_tools(mcp):
    """Registra i tool di generazione codice avanzata con l'istanza del server MCP."""
    logging.info("🚀 Registrazione tool-set: Code Generation Tools")

    @mcp.tool()
    def generate_python_class(class_name: str, attributes: List[str], methods: List[str] = [], parent_class: str = "") -> Dict[str, Any]:
        """
        Genera una classe Python con attributi e metodi specificati.
        
        Args:
            class_name: Nome della classe
            attributes: Lista degli attributi della classe
            methods: Lista dei metodi da generare
            parent_class: Classe genitore (opzionale)
        """
        try:
            if not class_name or not class_name.isidentifier():
                return {
                    "success": False,
                    "error": "Invalid class name"
                }
            
            # Header della classe
            inheritance = f"({parent_class})" if parent_class else ""
            class_code = f"class {class_name}{inheritance}:\n"
            class_code += f'    """\n    {class_name} class.\n    """\n\n'
            
            # Costruttore
            if attributes:
                class_code += "    def __init__(self"
                for attr in attributes:
                    if attr and attr.isidentifier():
                        class_code += f", {attr}=None"
                class_code += "):\n"
                class_code += f'        """\n        Initialize {class_name}.\n        """\n'
                
                for attr in attributes:
                    if attr and attr.isidentifier():
                        class_code += f"        self.{attr} = {attr}\n"
                class_code += "\n"
            else:
                class_code += "    def __init__(self):\n"
                class_code += f'        """\n        Initialize {class_name}.\n        """\n'
                class_code += "        pass\n\n"
            
            # Metodi
            for method in methods:
                if method and method.isidentifier():
                    class_code += f"    def {method}(self):\n"
                    class_code += f'        """\n        {method.replace("_", " ").title()} method.\n        """\n'
                    class_code += "        pass\n\n"
            
            # Metodi speciali comuni
            if attributes:
                # __str__ method
                class_code += "    def __str__(self):\n"
                class_code += f'        """\n        String representation of {class_name}.\n        """\n'
                attr_strs = [f"{attr}={{self.{attr}}}" for attr in attributes if attr.isidentifier()]
                class_code += f'        return f"{class_name}({", ".join(attr_strs)})"\n\n'
                
                # __repr__ method
                class_code += "    def __repr__(self):\n"
                class_code += f'        """\n        Representation of {class_name}.\n        """\n'
                class_code += "        return self.__str__()\n"
            
            return {
                "success": True,
                "class_name": class_name,
                "parent_class": parent_class,
                "attributes": attributes,
                "methods": methods,
                "generated_code": class_code,
                "lines_of_code": len(class_code.split('\n'))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_api_endpoints(resource_name: str, operations: List[str] = ["GET", "POST", "PUT", "DELETE"], framework: str = "flask") -> Dict[str, Any]:
        """
        Genera endpoint API REST per una risorsa.
        
        Args:
            resource_name: Nome della risorsa (es. "user", "product")
            operations: Lista delle operazioni HTTP da supportare
            framework: Framework web (flask, fastapi, django)
        """
        try:
            if not resource_name or not resource_name.isidentifier():
                return {
                    "success": False,
                    "error": "Invalid resource name"
                }
            
            resource_plural = resource_name + "s"  # Semplificazione
            
            if framework.lower() == "flask":
                code = f"from flask import Flask, request, jsonify\n\n"
                code += f"app = Flask(__name__)\n\n"
                code += f"# {resource_name.title()} API Endpoints\n\n"
                
                if "GET" in operations:
                    # GET all
                    code += f"@app.route('/{resource_plural}', methods=['GET'])\n"
                    code += f"def get_{resource_plural}():\n"
                    code += f'    """\n    Get all {resource_plural}.\n    """\n'
                    code += f"    # TODO: Implement get all {resource_plural}\n"
                    code += f"    return jsonify([]), 200\n\n"
                    
                    # GET by ID
                    code += f"@app.route('/{resource_plural}/<int:{resource_name}_id>', methods=['GET'])\n"
                    code += f"def get_{resource_name}({resource_name}_id):\n"
                    code += f'    """\n    Get a specific {resource_name}.\n    """\n'
                    code += f"    # TODO: Implement get {resource_name} by ID\n"
                    code += f"    return jsonify({{}}), 200\n\n"
                
                if "POST" in operations:
                    code += f"@app.route('/{resource_plural}', methods=['POST'])\n"
                    code += f"def create_{resource_name}():\n"
                    code += f'    """\n    Create a new {resource_name}.\n    """\n'
                    code += f"    data = request.get_json()\n"
                    code += f"    # TODO: Implement create {resource_name}\n"
                    code += f"    return jsonify({{}}), 201\n\n"
                
                if "PUT" in operations:
                    code += f"@app.route('/{resource_plural}/<int:{resource_name}_id>', methods=['PUT'])\n"
                    code += f"def update_{resource_name}({resource_name}_id):\n"
                    code += f'    """\n    Update a {resource_name}.\n    """\n'
                    code += f"    data = request.get_json()\n"
                    code += f"    # TODO: Implement update {resource_name}\n"
                    code += f"    return jsonify({{}}), 200\n\n"
                
                if "DELETE" in operations:
                    code += f"@app.route('/{resource_plural}/<int:{resource_name}_id>', methods=['DELETE'])\n"
                    code += f"def delete_{resource_name}({resource_name}_id):\n"
                    code += f'    """\n    Delete a {resource_name}.\n    """\n'
                    code += f"    # TODO: Implement delete {resource_name}\n"
                    code += f"    return '', 204\n\n"
                
                code += f"if __name__ == '__main__':\n"
                code += f"    app.run(debug=True)\n"
            
            elif framework.lower() == "fastapi":
                code = f"from fastapi import FastAPI, HTTPException\n"
                code += f"from pydantic import BaseModel\n"
                code += f"from typing import List, Optional\n\n"
                code += f"app = FastAPI()\n\n"
                code += f"# {resource_name.title()} Model\n"
                code += f"class {resource_name.title()}(BaseModel):\n"
                code += f"    id: Optional[int] = None\n"
                code += f"    # TODO: Add {resource_name} fields\n\n"
                code += f"# {resource_name.title()} API Endpoints\n\n"
                
                if "GET" in operations:
                    code += f"@app.get('/{resource_plural}', response_model=List[{resource_name.title()}])\n"
                    code += f"async def get_{resource_plural}():\n"
                    code += f'    """\n    Get all {resource_plural}.\n    """\n'
                    code += f"    # TODO: Implement get all {resource_plural}\n"
                    code += f"    return []\n\n"
                    
                    code += f"@app.get('/{resource_plural}/{{item_id}}', response_model={resource_name.title()})\n"
                    code += f"async def get_{resource_name}(item_id: int):\n"
                    code += f'    """\n    Get a specific {resource_name}.\n    """\n'
                    code += f"    # TODO: Implement get {resource_name} by ID\n"
                    code += f"    raise HTTPException(status_code=404, detail='{resource_name.title()} not found')\n\n"
                
                if "POST" in operations:
                    code += f"@app.post('/{resource_plural}', response_model={resource_name.title()})\n"
                    code += f"async def create_{resource_name}(item: {resource_name.title()}):\n"
                    code += f'    """\n    Create a new {resource_name}.\n    """\n'
                    code += f"    # TODO: Implement create {resource_name}\n"
                    code += f"    return item\n\n"
                
                if "PUT" in operations:
                    code += f"@app.put('/{resource_plural}/{{item_id}}', response_model={resource_name.title()})\n"
                    code += f"async def update_{resource_name}(item_id: int, item: {resource_name.title()}):\n"
                    code += f'    """\n    Update a {resource_name}.\n    """\n'
                    code += f"    # TODO: Implement update {resource_name}\n"
                    code += f"    return item\n\n"
                
                if "DELETE" in operations:
                    code += f"@app.delete('/{resource_plural}/{{item_id}}')\n"
                    code += f"async def delete_{resource_name}(item_id: int):\n"
                    code += f'    """\n    Delete a {resource_name}.\n    """\n'
                    code += f"    # TODO: Implement delete {resource_name}\n"
                    code += f"    return {{'message': '{resource_name.title()} deleted'}}\n"
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported framework. Use: flask, fastapi"
                }
            
            return {
                "success": True,
                "resource_name": resource_name,
                "framework": framework,
                "operations": operations,
                "generated_code": code,
                "endpoints_count": len(operations),
                "lines_of_code": len(code.split('\n'))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_dockerfile_template(base_image: str, language: str, port: int = 8000) -> Dict[str, Any]:
        """
        Genera un template Dockerfile per un linguaggio specifico.
        
        Args:
            base_image: Immagine base (es. "python:3.9", "node:16")
            language: Linguaggio di programmazione
            port: Porta da esporre
        """
        try:
            if not base_image:
                return {
                    "success": False,
                    "error": "Base image is required"
                }
            
            if port < 1 or port > 65535:
                return {
                    "success": False,
                    "error": "Port must be between 1 and 65535"
                }
            
            dockerfile = f"# Dockerfile for {language.title()} application\n"
            dockerfile += f"FROM {base_image}\n\n"
            
            if language.lower() == "python":
                dockerfile += "# Set working directory\n"
                dockerfile += "WORKDIR /app\n\n"
                dockerfile += "# Copy requirements first (for better caching)\n"
                dockerfile += "COPY requirements.txt .\n\n"
                dockerfile += "# Install dependencies\n"
                dockerfile += "RUN pip install --no-cache-dir -r requirements.txt\n\n"
                dockerfile += "# Copy application code\n"
                dockerfile += "COPY . .\n\n"
                dockerfile += "# Create non-root user\n"
                dockerfile += "RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app\n"
                dockerfile += "USER appuser\n\n"
                dockerfile += f"# Expose port\nEXPOSE {port}\n\n"
                dockerfile += "# Health check\n"
                dockerfile += f"HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\\n"
                dockerfile += f"  CMD curl -f http://localhost:{port}/health || exit 1\n\n"
                dockerfile += "# Run application\n"
                dockerfile += "CMD [\"python\", \"app.py\"]\n"
            
            elif language.lower() == "node" or language.lower() == "javascript":
                dockerfile += "# Set working directory\n"
                dockerfile += "WORKDIR /app\n\n"
                dockerfile += "# Copy package files first (for better caching)\n"
                dockerfile += "COPY package*.json ./\n\n"
                dockerfile += "# Install dependencies\n"
                dockerfile += "RUN npm ci --only=production\n\n"
                dockerfile += "# Copy application code\n"
                dockerfile += "COPY . .\n\n"
                dockerfile += "# Create non-root user\n"
                dockerfile += "RUN groupadd -r nodejs && useradd -m -r -g nodejs nodejs\n"
                dockerfile += "RUN chown -R nodejs:nodejs /app\n"
                dockerfile += "USER nodejs\n\n"
                dockerfile += f"# Expose port\nEXPOSE {port}\n\n"
                dockerfile += "# Health check\n"
                dockerfile += f"HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\\n"
                dockerfile += f"  CMD curl -f http://localhost:{port}/health || exit 1\n\n"
                dockerfile += "# Run application\n"
                dockerfile += "CMD [\"npm\", \"start\"]\n"
            
            elif language.lower() == "java":
                dockerfile += "# Set working directory\n"
                dockerfile += "WORKDIR /app\n\n"
                dockerfile += "# Copy Maven files first (for better caching)\n"
                dockerfile += "COPY pom.xml .\n"
                dockerfile += "COPY src ./src\n\n"
                dockerfile += "# Build application\n"
                dockerfile += "RUN mvn clean package -DskipTests\n\n"
                dockerfile += "# Create non-root user\n"
                dockerfile += "RUN groupadd -r javauser && useradd -m -r -g javauser javauser\n"
                dockerfile += "RUN chown -R javauser:javauser /app\n"
                dockerfile += "USER javauser\n\n"
                dockerfile += f"# Expose port\nEXPOSE {port}\n\n"
                dockerfile += "# Run application\n"
                dockerfile += "CMD [\"java\", \"-jar\", \"target/app.jar\"]\n"
            
            else:
                dockerfile += "# Set working directory\n"
                dockerfile += "WORKDIR /app\n\n"
                dockerfile += "# Copy application code\n"
                dockerfile += "COPY . .\n\n"
                dockerfile += "# Create non-root user\n"
                dockerfile += "RUN adduser --disabled-password --gecos '' appuser\n"
                dockerfile += "RUN chown -R appuser:appuser /app\n"
                dockerfile += "USER appuser\n\n"
                dockerfile += f"# Expose port\nEXPOSE {port}\n\n"
                dockerfile += "# TODO: Add build and run commands for your application\n"
                dockerfile += "CMD [\"echo\", \"Please configure the CMD instruction\"]\n"
            
            # Calcola metriche
            lines = dockerfile.split('\n')
            instruction_count = len([line for line in lines if line.strip() and not line.strip().startswith('#')])
            
            return {
                "success": True,
                "base_image": base_image,
                "language": language,
                "port": port,
                "dockerfile_content": dockerfile,
                "total_lines": len(lines),
                "instruction_count": instruction_count,
                "features": [
                    "Multi-stage caching optimization",
                    "Non-root user for security",
                    "Health check configuration",
                    "Working directory setup"
                ]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_test_template(test_type: str, class_name: str = "", methods: List[str] = [], framework: str = "unittest") -> Dict[str, Any]:
        """
        Genera template per test unitari.
        
        Args:
            test_type: Tipo di test (unit, integration, functional)
            class_name: Nome della classe da testare (per unit test)
            methods: Metodi da testare
            framework: Framework di test (unittest, pytest)
        """
        try:
            if framework.lower() == "unittest":
                test_code = "import unittest\n"
                if class_name:
                    test_code += f"from {class_name.lower()} import {class_name}\n"
                test_code += "\n\n"
                
                test_class_name = f"Test{class_name}" if class_name else "TestCase"
                test_code += f"class {test_class_name}(unittest.TestCase):\n"
                test_code += f'    """\n    Test cases for {class_name or "application"}.\n    """\n\n'
                
                test_code += "    def setUp(self):\n"
                test_code += f'        """\n        Set up test fixtures before each test method.\n        """\n'
                if class_name:
                    test_code += f"        self.instance = {class_name}()\n"
                else:
                    test_code += "        # TODO: Set up test fixtures\n"
                    test_code += "        pass\n"
                test_code += "\n"
                
                test_code += "    def tearDown(self):\n"
                test_code += f'        """\n        Clean up after each test method.\n        """\n'
                test_code += "        # TODO: Clean up test fixtures\n"
                test_code += "        pass\n\n"
                
                if methods:
                    for method in methods:
                        if method and method.isidentifier():
                            test_code += f"    def test_{method}(self):\n"
                            test_code += f'        """\n        Test {method} method.\n        """\n'
                            if class_name:
                                test_code += f"        # TODO: Test {class_name}.{method}()\n"
                                test_code += f"        result = self.instance.{method}()\n"
                                test_code += f"        self.assertIsNotNone(result)\n"
                            else:
                                test_code += f"        # TODO: Test {method}\n"
                                test_code += f"        self.assertTrue(True)  # Replace with actual test\n"
                            test_code += "\n"
                else:
                    test_code += "    def test_example(self):\n"
                    test_code += f'        """\n        Example test case.\n        """\n'
                    test_code += "        # TODO: Write your test\n"
                    test_code += "        self.assertTrue(True)\n\n"
                
                test_code += "\nif __name__ == '__main__':\n"
                test_code += "    unittest.main()\n"
            
            elif framework.lower() == "pytest":
                test_code = "import pytest\n"
                if class_name:
                    test_code += f"from {class_name.lower()} import {class_name}\n"
                test_code += "\n\n"
                
                test_code += "@pytest.fixture\n"
                test_code += "def setup():\n"
                test_code += f'    """\n    Setup test fixtures.\n    """\n'
                if class_name:
                    test_code += f"    instance = {class_name}()\n"
                    test_code += f"    return instance\n"
                else:
                    test_code += "    # TODO: Set up test fixtures\n"
                    test_code += "    return None\n"
                test_code += "\n\n"
                
                if methods:
                    for method in methods:
                        if method and method.isidentifier():
                            test_code += f"def test_{method}(setup):\n"
                            test_code += f'    """\n    Test {method} method.\n    """\n'
                            if class_name:
                                test_code += f"    # TODO: Test {class_name}.{method}()\n"
                                test_code += f"    result = setup.{method}()\n"
                                test_code += f"    assert result is not None\n"
                            else:
                                test_code += f"    # TODO: Test {method}\n"
                                test_code += f"    assert True  # Replace with actual test\n"
                            test_code += "\n\n"
                else:
                    test_code += "def test_example(setup):\n"
                    test_code += f'    """\n    Example test case.\n    """\n'
                    test_code += "    # TODO: Write your test\n"
                    test_code += "    assert True\n"
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported framework. Use: unittest, pytest"
                }
            
            test_count = len(methods) if methods else 1
            
            return {
                "success": True,
                "test_type": test_type,
                "class_name": class_name,
                "framework": framework,
                "methods_tested": methods,
                "test_code": test_code,
                "test_count": test_count,
                "lines_of_code": len(test_code.split('\n'))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_config_file(config_type: str, application_name: str, environment: str = "development") -> Dict[str, Any]:
        """
        Genera file di configurazione per diversi formati.
        
        Args:
            config_type: Tipo di configurazione (json, yaml, ini, env)
            application_name: Nome dell'applicazione
            environment: Ambiente (development, staging, production)
        """
        try:
            config_data = {
                "application": {
                    "name": application_name,
                    "version": "1.0.0",
                    "environment": environment
                },
                "server": {
                    "host": "0.0.0.0" if environment == "production" else "localhost",
                    "port": 8000,
                    "debug": environment == "development"
                },
                "database": {
                    "host": "db" if environment == "production" else "localhost",
                    "port": 5432,
                    "name": f"{application_name}_{environment}",
                    "username": "app_user",
                    "password": "change_me_in_production"
                },
                "logging": {
                    "level": "DEBUG" if environment == "development" else "INFO",
                    "file": f"/var/log/{application_name}.log" if environment == "production" else f"{application_name}.log"
                },
                "security": {
                    "secret_key": "your-secret-key-here",
                    "token_expiry": 3600,
                    "cors_enabled": environment == "development"
                }
            }
            
            if config_type.lower() == "json":
                config_content = json.dumps(config_data, indent=2)
                filename = f"config.{environment}.json"
            
            elif config_type.lower() == "yaml":
                # Generazione YAML manuale semplificata
                config_content = f"# {application_name} Configuration - {environment}\n"
                config_content += f"application:\n"
                config_content += f"  name: {config_data['application']['name']}\n"
                config_content += f"  version: {config_data['application']['version']}\n"
                config_content += f"  environment: {config_data['application']['environment']}\n\n"
                config_content += f"server:\n"
                config_content += f"  host: {config_data['server']['host']}\n"
                config_content += f"  port: {config_data['server']['port']}\n"
                config_content += f"  debug: {str(config_data['server']['debug']).lower()}\n\n"
                config_content += f"database:\n"
                config_content += f"  host: {config_data['database']['host']}\n"
                config_content += f"  port: {config_data['database']['port']}\n"
                config_content += f"  name: {config_data['database']['name']}\n"
                config_content += f"  username: {config_data['database']['username']}\n"
                config_content += f"  password: {config_data['database']['password']}\n\n"
                config_content += f"logging:\n"
                config_content += f"  level: {config_data['logging']['level']}\n"
                config_content += f"  file: {config_data['logging']['file']}\n\n"
                config_content += f"security:\n"
                config_content += f"  secret_key: {config_data['security']['secret_key']}\n"
                config_content += f"  token_expiry: {config_data['security']['token_expiry']}\n"
                config_content += f"  cors_enabled: {str(config_data['security']['cors_enabled']).lower()}\n"
                filename = f"config.{environment}.yml"
            
            elif config_type.lower() == "ini":
                config_content = f"; {application_name} Configuration - {environment}\n"
                config_content += f"[application]\n"
                config_content += f"name = {config_data['application']['name']}\n"
                config_content += f"version = {config_data['application']['version']}\n"
                config_content += f"environment = {config_data['application']['environment']}\n\n"
                config_content += f"[server]\n"
                config_content += f"host = {config_data['server']['host']}\n"
                config_content += f"port = {config_data['server']['port']}\n"
                config_content += f"debug = {config_data['server']['debug']}\n\n"
                config_content += f"[database]\n"
                config_content += f"host = {config_data['database']['host']}\n"
                config_content += f"port = {config_data['database']['port']}\n"
                config_content += f"name = {config_data['database']['name']}\n"
                config_content += f"username = {config_data['database']['username']}\n"
                config_content += f"password = {config_data['database']['password']}\n\n"
                config_content += f"[logging]\n"
                config_content += f"level = {config_data['logging']['level']}\n"
                config_content += f"file = {config_data['logging']['file']}\n\n"
                config_content += f"[security]\n"
                config_content += f"secret_key = {config_data['security']['secret_key']}\n"
                config_content += f"token_expiry = {config_data['security']['token_expiry']}\n"
                config_content += f"cors_enabled = {config_data['security']['cors_enabled']}\n"
                filename = f"config.{environment}.ini"
            
            elif config_type.lower() == "env":
                config_content = f"# {application_name} Environment Variables - {environment}\n"
                config_content += f"APP_NAME={config_data['application']['name']}\n"
                config_content += f"APP_VERSION={config_data['application']['version']}\n"
                config_content += f"APP_ENVIRONMENT={config_data['application']['environment']}\n"
                config_content += f"SERVER_HOST={config_data['server']['host']}\n"
                config_content += f"SERVER_PORT={config_data['server']['port']}\n"
                config_content += f"DEBUG={config_data['server']['debug']}\n"
                config_content += f"DB_HOST={config_data['database']['host']}\n"
                config_content += f"DB_PORT={config_data['database']['port']}\n"
                config_content += f"DB_NAME={config_data['database']['name']}\n"
                config_content += f"DB_USERNAME={config_data['database']['username']}\n"
                config_content += f"DB_PASSWORD={config_data['database']['password']}\n"
                config_content += f"LOG_LEVEL={config_data['logging']['level']}\n"
                config_content += f"LOG_FILE={config_data['logging']['file']}\n"
                config_content += f"SECRET_KEY={config_data['security']['secret_key']}\n"
                config_content += f"TOKEN_EXPIRY={config_data['security']['token_expiry']}\n"
                config_content += f"CORS_ENABLED={config_data['security']['cors_enabled']}\n"
                filename = f".env.{environment}"
            
            else:
                return {
                    "success": False,
                    "error": "Unsupported config type. Use: json, yaml, ini, env"
                }
            
            return {
                "success": True,
                "config_type": config_type,
                "application_name": application_name,
                "environment": environment,
                "filename": filename,
                "config_content": config_content,
                "sections": list(config_data.keys()),
                "lines_of_code": len(config_content.split('\n'))
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    @mcp.tool()
    def generate_database_schema(table_name: str, fields: List[Dict[str, Any]], 
                                database_type: str = "postgresql", 
                                include_migrations: bool = True) -> Dict[str, Any]:
        """
        Genera schema database con migrazioni per diversi DBMS.
        
        Args:
            table_name: Nome della tabella
            fields: Lista di campi con tipo, vincoli, ecc.
            database_type: Tipo di database (postgresql, mysql, sqlite, mongodb)
            include_migrations: Se includere script di migrazione
        """
        try:
            if not table_name or not table_name.isidentifier():
                return {"success": False, "error": "Invalid table name"}
            
            if not fields:
                return {"success": False, "error": "At least one field is required"}
            
            schema_sql = ""
            migration_up = ""
            migration_down = ""
            
            if database_type.lower() in ["postgresql", "postgres"]:
                schema_sql = _generate_postgresql_schema(table_name, fields)
                if include_migrations:
                    migration_up, migration_down = _generate_postgresql_migrations(table_name, fields)
            
            elif database_type.lower() == "mysql":
                schema_sql = _generate_mysql_schema(table_name, fields)
                if include_migrations:
                    migration_up, migration_down = _generate_mysql_migrations(table_name, fields)
            
            elif database_type.lower() == "sqlite":
                schema_sql = _generate_sqlite_schema(table_name, fields)
                if include_migrations:
                    migration_up, migration_down = _generate_sqlite_migrations(table_name, fields)
            
            elif database_type.lower() == "mongodb":
                schema_json = _generate_mongodb_schema(table_name, fields)
                return {
                    "success": True,
                    "database_type": database_type,
                    "collection_name": table_name,
                    "schema_definition": schema_json,
                    "validation_rules": _generate_mongodb_validation(table_name, fields),
                    "indexes": _generate_mongodb_indexes(fields)
                }
            
            else:
                return {"success": False, "error": f"Unsupported database type: {database_type}"}
            
            # Genera anche modelli ORM
            orm_models = {
                "sqlalchemy": _generate_sqlalchemy_model(table_name, fields),
                "django": _generate_django_model(table_name, fields),
                "sequelize": _generate_sequelize_model(table_name, fields)
            }
            
            result = {
                "success": True,
                "database_type": database_type,
                "table_name": table_name,
                "schema_sql": schema_sql,
                "fields_count": len(fields),
                "orm_models": orm_models
            }
            
            if include_migrations:
                result["migrations"] = {
                    "up": migration_up,
                    "down": migration_down,
                    "filename": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_create_{table_name}.sql"
                }
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_project_scaffold(project_name: str, project_type: str, 
                                 framework: str = "", features: List[str] = None) -> Dict[str, Any]:
        """
        Genera scaffolding completo per progetti con struttura directories e file base.
        
        Args:
            project_name: Nome del progetto
            project_type: Tipo progetto (web, api, cli, desktop, mobile)
            framework: Framework specifico (react, vue, flask, fastapi, etc.)
            features: Lista di feature da includere (auth, database, tests, docker)
        """
        try:
            if not project_name or not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', project_name):
                return {"success": False, "error": "Invalid project name"}
            
            features = features or []
            project_structure = {}
            generated_files = {}
            
            if project_type.lower() == "web" and framework.lower() == "react":
                project_structure, generated_files = _generate_react_project(project_name, features)
            
            elif project_type.lower() == "web" and framework.lower() == "vue":
                project_structure, generated_files = _generate_vue_project(project_name, features)
            
            elif project_type.lower() == "api" and framework.lower() == "fastapi":
                project_structure, generated_files = _generate_fastapi_project(project_name, features)
            
            elif project_type.lower() == "api" and framework.lower() == "flask":
                project_structure, generated_files = _generate_flask_project(project_name, features)
            
            elif project_type.lower() == "cli":
                project_structure, generated_files = _generate_cli_project(project_name, features)
            
            elif project_type.lower() == "microservice":
                project_structure, generated_files = _generate_microservice_project(project_name, framework, features)
            
            else:
                return {"success": False, "error": f"Unsupported project type/framework: {project_type}/{framework}"}
            
            # Aggiungi file comuni se richiesti
            if "docker" in features:
                generated_files.update(_generate_docker_files(project_name, project_type, framework))
            
            if "github_actions" in features:
                generated_files.update(_generate_github_actions(project_name, project_type))
            
            if "tests" in features:
                generated_files.update(_generate_test_structure(project_name, project_type, framework))
            
            # Genera documentazione
            generated_files["README.md"] = _generate_project_readme(project_name, project_type, framework, features)
            generated_files[".gitignore"] = _generate_gitignore(project_type, framework)
            
            return {
                "success": True,
                "project_name": project_name,
                "project_type": project_type,
                "framework": framework,
                "features": features,
                "project_structure": project_structure,
                "generated_files": generated_files,
                "files_count": len(generated_files),
                "setup_instructions": _generate_setup_instructions(project_name, project_type, framework, features)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_design_pattern(pattern_name: str, language: str = "python", 
                               class_names: List[str] = None, 
                               custom_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Genera implementazioni di design pattern comuni.
        
        Args:
            pattern_name: Nome del pattern (singleton, factory, observer, strategy, etc.)
            language: Linguaggio di programmazione
            class_names: Nomi delle classi personalizzati
            custom_params: Parametri aggiuntivi specifici del pattern
        """
        try:
            if not pattern_name:
                return {"success": False, "error": "Pattern name is required"}
            
            class_names = class_names or []
            custom_params = custom_params or {}
            
            pattern_code = ""
            pattern_description = ""
            usage_example = ""
            
            if pattern_name.lower() == "singleton":
                pattern_code, pattern_description, usage_example = _generate_singleton_pattern(language, class_names, custom_params)
            
            elif pattern_name.lower() == "factory":
                pattern_code, pattern_description, usage_example = _generate_factory_pattern(language, class_names, custom_params)
            
            elif pattern_name.lower() == "observer":
                pattern_code, pattern_description, usage_example = _generate_observer_pattern(language, class_names, custom_params)
            
            elif pattern_name.lower() == "strategy":
                pattern_code, pattern_description, usage_example = _generate_strategy_pattern(language, class_names, custom_params)
            
            elif pattern_name.lower() == "decorator":
                pattern_code, pattern_description, usage_example = _generate_decorator_pattern(language, class_names, custom_params)
            
            elif pattern_name.lower() == "adapter":
                pattern_code, pattern_description, usage_example = _generate_adapter_pattern(language, class_names, custom_params)
            
            elif pattern_name.lower() == "facade":
                pattern_code, pattern_description, usage_example = _generate_facade_pattern(language, class_names, custom_params)
            
            elif pattern_name.lower() == "command":
                pattern_code, pattern_description, usage_example = _generate_command_pattern(language, class_names, custom_params)
            
            else:
                return {"success": False, "error": f"Unsupported pattern: {pattern_name}"}
            
            return {
                "success": True,
                "pattern_name": pattern_name,
                "language": language,
                "pattern_code": pattern_code,
                "description": pattern_description,
                "usage_example": usage_example,
                "class_names_used": class_names,
                "benefits": _get_pattern_benefits(pattern_name),
                "use_cases": _get_pattern_use_cases(pattern_name)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_frontend_component(component_name: str, framework: str, 
                                  component_type: str = "functional", 
                                  props: List[Dict[str, Any]] = None,
                                  styling: str = "css") -> Dict[str, Any]:
        """
        Genera componenti frontend per diversi framework.
        
        Args:
            component_name: Nome del componente
            framework: Framework (react, vue, angular, svelte)
            component_type: Tipo componente (functional, class, hook)
            props: Lista di proprietà del componente
            styling: Tipo di styling (css, scss, styled-components, tailwind)
        """
        try:
            if not component_name or not re.match(r'^[A-Z][a-zA-Z0-9]*$', component_name):
                return {"success": False, "error": "Invalid component name (must be PascalCase)"}
            
            props = props or []
            component_files = {}
            
            if framework.lower() == "react":
                component_files = _generate_react_component(component_name, component_type, props, styling)
            
            elif framework.lower() == "vue":
                component_files = _generate_vue_component(component_name, component_type, props, styling)
            
            elif framework.lower() == "angular":
                component_files = _generate_angular_component(component_name, component_type, props, styling)
            
            elif framework.lower() == "svelte":
                component_files = _generate_svelte_component(component_name, component_type, props, styling)
            
            else:
                return {"success": False, "error": f"Unsupported framework: {framework}"}
            
            # Genera anche test per il componente
            if framework.lower() in ["react", "vue"]:
                component_files.update(_generate_component_tests(component_name, framework, props))
            
            # Genera Storybook se richiesto
            if "storybook" in styling:
                component_files.update(_generate_storybook_story(component_name, framework, props))
            
            return {
                "success": True,
                "component_name": component_name,
                "framework": framework,
                "component_type": component_type,
                "styling": styling,
                "props": props,
                "generated_files": component_files,
                "files_count": len(component_files),
                "usage_examples": _generate_component_usage_examples(component_name, framework, props)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_api_documentation(api_name: str, endpoints: List[Dict[str, Any]], 
                                 doc_format: str = "openapi", 
                                 include_examples: bool = True) -> Dict[str, Any]:
        """
        Genera documentazione API in diversi formati.
        
        Args:
            api_name: Nome dell'API
            endpoints: Lista di endpoint con metodi, parametri, risposte
            doc_format: Formato documentazione (openapi, postman, markdown)
            include_examples: Se includere esempi di request/response
        """
        try:
            if not api_name:
                return {"success": False, "error": "API name is required"}
            
            if not endpoints:
                return {"success": False, "error": "At least one endpoint is required"}
            
            documentation = ""
            
            if doc_format.lower() == "openapi":
                documentation = _generate_openapi_spec(api_name, endpoints, include_examples)
            
            elif doc_format.lower() == "postman":
                documentation = _generate_postman_collection(api_name, endpoints, include_examples)
            
            elif doc_format.lower() == "markdown":
                documentation = _generate_markdown_api_docs(api_name, endpoints, include_examples)
            
            elif doc_format.lower() == "insomnia":
                documentation = _generate_insomnia_collection(api_name, endpoints, include_examples)
            
            else:
                return {"success": False, "error": f"Unsupported documentation format: {doc_format}"}
            
            # Genera anche client SDK se richiesto
            client_sdks = {}
            if include_examples:
                client_sdks = {
                    "python": _generate_python_client(api_name, endpoints),
                    "javascript": _generate_js_client(api_name, endpoints),
                    "curl": _generate_curl_examples(endpoints)
                }
            print("client_sdks",client_sdks)
            return {
                "success": True,
                "api_name": api_name,
                "doc_format": doc_format,
                "endpoints_count": len(endpoints),
                "documentation": documentation,
                "client_sdks": client_sdks,
                "validation_schema": _generate_validation_schema(endpoints) if doc_format == "openapi" else None
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def generate_cicd_pipeline(project_name: str, platform: str, 
                              language: str, stages: List[str] = None,
                              deployment_target: str = "docker") -> Dict[str, Any]:
        """
        Genera pipeline CI/CD per diverse piattaforme.
        
        Args:
            project_name: Nome del progetto
            platform: Piattaforma CI/CD (github_actions, gitlab_ci, jenkins, azure_devops)
            language: Linguaggio di programmazione
            stages: Stages della pipeline (build, test, deploy, security)
            deployment_target: Target di deployment (docker, kubernetes, aws, heroku)
        """
        try:
            if not project_name:
                return {"success": False, "error": "Project name is required"}
            
            stages = stages or ["build", "test", "deploy"]
            pipeline_files = {}
            
            if platform.lower() == "github_actions":
                pipeline_files = _generate_github_actions_pipeline(project_name, language, stages, deployment_target)
            
            elif platform.lower() == "gitlab_ci":
                pipeline_files = _generate_gitlab_ci_pipeline(project_name, language, stages, deployment_target)
            
            elif platform.lower() == "jenkins":
                pipeline_files = _generate_jenkins_pipeline(project_name, language, stages, deployment_target)
            
            elif platform.lower() == "azure_devops":
                pipeline_files = _generate_azure_devops_pipeline(project_name, language, stages, deployment_target)
            
            else:
                return {"success": False, "error": f"Unsupported CI/CD platform: {platform}"}
            
            # Aggiungi configurazioni di sicurezza
            if "security" in stages:
                pipeline_files.update(_generate_security_configs(platform, language))
            
            return {
                "success": True,
                "project_name": project_name,
                "platform": platform,
                "language": language,
                "stages": stages,
                "deployment_target": deployment_target,
                "pipeline_files": pipeline_files,
                "setup_instructions": _generate_cicd_setup_instructions(platform, deployment_target)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    def modernize_legacy_code(legacy_code: str, source_language: str, 
                             target_language: str = "", 
                             modernization_type: str = "refactor") -> Dict[str, Any]:
        """
        Modernizza e refactorizza codice legacy.
        
        Args:
            legacy_code: Codice legacy da modernizzare
            source_language: Linguaggio sorgente
            target_language: Linguaggio target (se diverso, fa conversione)
            modernization_type: Tipo di modernizzazione (refactor, convert, optimize)
        """
        try:
            if not legacy_code.strip():
                return {"success": False, "error": "Legacy code is required"}
            
            target_language = target_language or source_language
            
            modernized_code = ""
            improvements = []
            conversion_notes = []
            
            if modernization_type.lower() == "refactor":
                modernized_code, improvements = _refactor_code(legacy_code, source_language)
            
            elif modernization_type.lower() == "convert":
                if source_language.lower() != target_language.lower():
                    modernized_code, conversion_notes = _convert_language(legacy_code, source_language, target_language)
                else:
                    return {"success": False, "error": "Source and target languages must be different for conversion"}
            
            elif modernization_type.lower() == "optimize":
                modernized_code, improvements = _optimize_code_performance(legacy_code, source_language)
            
            else:
                return {"success": False, "error": f"Unsupported modernization type: {modernization_type}"}
            
            # Analizza le metriche di miglioramento
            metrics = _calculate_improvement_metrics(legacy_code, modernized_code, source_language)
            
            return {
                "success": True,
                "source_language": source_language,
                "target_language": target_language,
                "modernization_type": modernization_type,
                "original_code": legacy_code,
                "modernized_code": modernized_code,
                "improvements": improvements,
                "conversion_notes": conversion_notes,
                "improvement_metrics": metrics,
                "recommendations": _generate_modernization_recommendations(legacy_code, source_language)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper functions for database schema generation
    def _generate_postgresql_schema(self, table_name: str, fields: List[Dict[str, Any]]) -> str:
        """Genera schema PostgreSQL."""
        sql = f"-- PostgreSQL Schema for {table_name}\n"
        sql += f"CREATE TABLE {table_name} (\n"
        
        field_definitions = []
        for field in fields:
            field_def = f"    {field['name']} {self._map_to_postgresql_type(field.get('type', 'VARCHAR'))}"
            
            if field.get('primary_key'):
                field_def += " PRIMARY KEY"
            if field.get('not_null'):
                field_def += " NOT NULL"
            if field.get('unique'):
                field_def += " UNIQUE"
            if field.get('default'):
                field_def += f" DEFAULT {field['default']}"
            
            field_definitions.append(field_def)
        
        sql += ",\n".join(field_definitions)
        sql += "\n);\n\n"
        
        # Aggiungi indici
        for field in fields:
            if field.get('index') and not field.get('primary_key'):
                sql += f"CREATE INDEX idx_{table_name}_{field['name']} ON {table_name}({field['name']});\n"
        
        return sql

    def _map_to_postgresql_type(self, field_type: str) -> str:
        """Mappa tipi generici a tipi PostgreSQL."""
        type_mapping = {
            'string': 'VARCHAR(255)',
            'text': 'TEXT',
            'integer': 'INTEGER',
            'bigint': 'BIGINT',
            'float': 'REAL',
            'decimal': 'DECIMAL(10,2)',
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'datetime': 'TIMESTAMP',
            'json': 'JSONB',
            'uuid': 'UUID'
        }
        return type_mapping.get(field_type.lower(), 'VARCHAR(255)')

    def _generate_sqlalchemy_model(self, table_name: str, fields: List[Dict[str, Any]]) -> str:
        """Genera modello SQLAlchemy."""
        model_name = table_name.title().replace('_', '')
        
        code = "from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text\n"
        code += "from sqlalchemy.ext.declarative import declarative_base\n"
        code += "from datetime import datetime\n\n"
        code += "Base = declarative_base()\n\n"
        code += f"class {model_name}(Base):\n"
        code += f"    __tablename__ = '{table_name}'\n\n"
        
        for field in fields:
            field_type = self._map_to_sqlalchemy_type(field.get('type', 'string'))
            field_def = f"    {field['name']} = Column({field_type}"
            
            if field.get('primary_key'):
                field_def += ", primary_key=True"
            if field.get('not_null'):
                field_def += ", nullable=False"
            if field.get('unique'):
                field_def += ", unique=True"
            
            field_def += ")\n"
            code += field_def
        
        return code

    def _map_to_sqlalchemy_type(self, field_type: str) -> str:
        """Mappa tipi a SQLAlchemy."""
        type_mapping = {
            'string': 'String(255)',
            'text': 'Text',
            'integer': 'Integer',
            'boolean': 'Boolean',
            'datetime': 'DateTime'
        }
        return type_mapping.get(field_type.lower(), 'String(255)')

    # Helper functions for project scaffolding
    def _generate_react_project(self, project_name: str, features: List[str]) -> Tuple[Dict, Dict]:
        """Genera struttura progetto React."""
        structure = {
            "src": {
                "components": {},
                "pages": {},
                "hooks": {},
                "utils": {},
                "services": {},
                "styles": {}
            },
            "public": {},
            "tests": {} if "tests" in features else None
        }
        
        files = {
            "package.json": self._generate_react_package_json(project_name, features),
            "src/App.js": self._generate_react_app_component(project_name),
            "src/index.js": self._generate_react_index(project_name),
            "src/components/Header.js": self._generate_react_header_component(),
            "public/index.html": self._generate_react_html(project_name)
        }
        
        if "typescript" in features:
            # Converti a TypeScript
            files = {k.replace('.js', '.tsx' if 'component' in k.lower() else '.ts'): v 
                    for k, v in files.items()}
            files["tsconfig.json"] = self._generate_react_tsconfig()
        
        return structure, files

    def _generate_react_package_json(self, project_name: str, features: List[str]) -> str:
        """Genera package.json per React."""
        dependencies = {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-scripts": "5.0.1"
        }
        
        if "router" in features:
            dependencies["react-router-dom"] = "^6.8.0"
        if "redux" in features:
            dependencies["@reduxjs/toolkit"] = "^1.9.0"
            dependencies["react-redux"] = "^8.0.5"
        if "styled-components" in features:
            dependencies["styled-components"] = "^5.3.6"
        
        package_data = {
            "name": project_name,
            "version": "0.1.0",
            "private": True,
            "dependencies": dependencies,
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            }
        }
        
        return json.dumps(package_data, indent=2)

    # Helper functions for design patterns
    def _generate_singleton_pattern(self, language: str, class_names: List[str], custom_params: Dict) -> Tuple[str, str, str]:
        """Genera pattern Singleton."""
        class_name = class_names[0] if class_names else "Singleton"
        
        if language.lower() == "python":
            code = f'''class {class_name}:
    """
    Singleton pattern implementation.
    Ensures only one instance of the class exists.
    """
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            # Initialize only once
            self.data = {{}}
            self.__class__._initialized = True
    
    def get_data(self, key):
        """Get data by key."""
        return self.data.get(key)
    
    def set_data(self, key, value):
        """Set data by key."""
        self.data[key] = value
'''
            
            description = "Singleton pattern ensures a class has only one instance and provides global access to it."
            
            usage = f'''# Usage Example
singleton1 = {class_name}()
singleton2 = {class_name}()

print(singleton1 is singleton2)  # True

singleton1.set_data("key", "value")
print(singleton2.get_data("key"))  # "value"
'''
        
        return code, description, usage

    def _generate_factory_pattern(self, language: str, class_names: List[str], custom_params: Dict) -> Tuple[str, str, str]:
        """Genera pattern Factory."""
        base_class = class_names[0] if class_names else "Product"
        factory_class = class_names[1] if len(class_names) > 1 else "Factory"
        
        if language.lower() == "python":
            code = f'''from abc import ABC, abstractmethod

class {base_class}(ABC):
    """Abstract product class."""
    
    @abstractmethod
    def operation(self):
        """Abstract operation method."""
        pass

class Concrete{base_class}A({base_class}):
    """Concrete product A."""
    
    def operation(self):
        return "Product A operation"

class Concrete{base_class}B({base_class}):
    """Concrete product B."""
    
    def operation(self):
        return "Product B operation"

class {factory_class}:
    """Factory class for creating products."""
    
    @staticmethod
    def create_product(product_type: str) -> {base_class}:
        """Create product based on type."""
        if product_type.lower() == "a":
            return Concrete{base_class}A()
        elif product_type.lower() == "b":
            return Concrete{base_class}B()
        else:
            raise ValueError(f"Unknown product type: {{product_type}}")
'''
            
            description = "Factory pattern creates objects without specifying their exact classes."
            
            usage = f'''# Usage Example
factory = {factory_class}()

product_a = factory.create_product("a")
product_b = factory.create_product("b")

print(product_a.operation())  # "Product A operation"
print(product_b.operation())  # "Product B operation"
'''
        
        return code, description, usage

    def _get_pattern_benefits(self, pattern_name: str) -> List[str]:
        """Restituisce i benefici del pattern."""
        benefits = {
            "singleton": [
                "Garantisce una sola istanza",
                "Accesso globale controllato",
                "Risparmio di memoria"
            ],
            "factory": [
                "Disaccoppia creazione da utilizzo",
                "Facilita aggiunta nuovi tipi",
                "Centralizza logica di creazione"
            ],
            "observer": [
                "Accoppiamento debole",
                "Comunicazione dinamica",
                "Supporta broadcast"
            ]
        }
        return benefits.get(pattern_name.lower(), [])

    # Helper functions for CI/CD pipeline generation
    def _generate_github_actions_pipeline(self, project_name: str, language: str, 
                                        stages: List[str], deployment_target: str) -> Dict[str, str]:
        """Genera pipeline GitHub Actions."""
        workflow = f'''name: {project_name} CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
'''
        
        if "build" in stages:
            workflow += self._generate_github_build_job(language)
        
        if "test" in stages:
            workflow += self._generate_github_test_job(language)
        
        if "security" in stages:
            workflow += self._generate_github_security_job()
        
        if "deploy" in stages:
            workflow += self._generate_github_deploy_job(deployment_target)
        
        return {".github/workflows/ci-cd.yml": workflow}

    def _generate_github_build_job(self, language: str) -> str:
        """Genera job di build per GitHub Actions."""
        if language.lower() == "python":
            return '''  build:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Build package
      run: |
        python setup.py build

'''
        elif language.lower() in ["javascript", "node"]:
            return '''  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Build
      run: npm run build

'''
        return ""

    def _generate_github_test_job(self, language: str) -> str:
        """Genera job di test per GitHub Actions."""
        if language.lower() == "python":
            return '''  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, '3.10']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m unittest discover -s tests

'''
        elif language.lower() in ["javascript", "node"]:
            return '''  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run tests
      run: npm test

'''
        return ""

    def _generate_github_security_job(self) -> str:
        """Genera job di sicurezza per GitHub Actions."""
        return '''  security:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Run security scan
      run: |
        # TODO: Aggiungi comandi per la scansione di sicurezza
        echo "Esecuzione scansione di sicurezza..."

'''

    def _generate_github_deploy_job(self, deployment_target: str) -> str:
        """Genera job di deploy per GitHub Actions."""
        if deployment_target.lower() == "docker":
            return '''  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Log in to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v2
      with:
        context: .
        dockerfile: Dockerfile
        tags: ${{ secrets.DOCKER_USERNAME }}/${{ github.repository }}:latest
    
    - name: Deploy to Docker
      run: |
        docker pull ${{ secrets.DOCKER_USERNAME }}/${{ github.repository }}:latest
        docker stop my_app || true
        docker rm my_app || true
        docker run -d --name my_app -p 8000:8000 ${{ secrets.DOCKER_USERNAME }}/${{ github.repository }}:latest

'''
        elif deployment_target.lower() == "kubernetes":
            return '''  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Kubeconfig
      run: |
        mkdir -p $HOME/.kube
        echo "${{ secrets.KUBE_CONFIG }}" | base64 --decode > $HOME/.kube/config
        kubectl config set-context --current --namespace=${{ secrets.KUBE_NAMESPACE }}
    
    - name: Deploy to Kubernetes
      run: |
        kubectl rollout restart deployment/my-app-deployment
        kubectl get pods -w

'''
        elif deployment_target.lower() == "aws":
            return '''  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v1
      with:
        aws_access_key_id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws_secret_access_key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws_region: ${{ secrets.AWS_REGION }}
    
    - name: Deploy to ECS
      run: |
        # TODO: Aggiungi comandi per il deploy su AWS ECS
        echo "Deploying to AWS ECS..."

'''
        elif deployment_target.lower() == "heroku":
            return '''  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.14.10
      with:
        heroku_app_name: ${{ secrets.HEROKU_APP_NAME }}
        heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
        heroku_email: ${{ secrets.HEROKU_EMAIL }}
        process_type: web
        docker_image: true

'''
        return ""

    # ...existing code...