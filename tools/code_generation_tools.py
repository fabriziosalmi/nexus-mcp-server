# -*- coding: utf-8 -*-
# tools/code_generation_tools.py
import os
import json
import logging
from typing import Dict, List, Any, Optional
import re

def register_tools(mcp):
    """Registra i tool di generazione codice con l'istanza del server MCP."""
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