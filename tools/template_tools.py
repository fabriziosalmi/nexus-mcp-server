# -*- coding: utf-8 -*-
# tools/template_tools.py
import logging
import json
import re
from datetime import datetime

def register_tools(mcp):
    """Registra i tool per template con l'istanza del server MCP."""
    logging.info("📋 Registrazione tool-set: Template Tools")

    @mcp.tool()
    def generate_dockerfile_template(base_image: str, language: str, port: int = 8000, additional_packages: str = "") -> str:
        """
        Genera un template Dockerfile per diverse tecnologie.
        
        Args:
            base_image: Immagine base (es. "node:18", "python:3.11", "openjdk:17")
            language: Linguaggio/tecnologia (node, python, java, go, nginx)
            port: Porta da esporre
            additional_packages: Pacchetti aggiuntivi da installare
        """
        try:
            packages_list = [pkg.strip() for pkg in additional_packages.split(',') if pkg.strip()] if additional_packages else []
            
            templates = {
                'node': f"""# Dockerfile per applicazione Node.js
FROM {base_image}

# Imposta directory di lavoro
WORKDIR /app

# Copia package.json e package-lock.json (se disponibile)
COPY package*.json ./

# Installa dipendenze
RUN npm ci --only=production

# Copia codice sorgente
COPY . .

# Crea utente non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Espone porta
EXPOSE {port}

# Comando di avvio
CMD ["npm", "start"]""",

                'python': f"""# Dockerfile per applicazione Python
FROM {base_image}

# Imposta directory di lavoro
WORKDIR /app

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copia requirements
COPY requirements.txt .

# Installa dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia codice sorgente
COPY . .

# Crea utente non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Espone porta
EXPOSE {port}

# Comando di avvio
CMD ["python", "app.py"]""",

                'java': f"""# Dockerfile per applicazione Java
FROM {base_image}

# Imposta directory di lavoro
WORKDIR /app

# Copia JAR file
COPY target/*.jar app.jar

# Crea utente non-root
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Espone porta
EXPOSE {port}

# Configurazione JVM
ENV JAVA_OPTS="-Xmx512m -Xms256m"

# Comando di avvio
CMD ["java", "-jar", "app.jar"]""",

                'go': f"""# Multi-stage build per applicazione Go
FROM golang:1.21 AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

# Final stage
FROM {base_image if 'alpine' in base_image else 'alpine:latest'}

RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/main .

# Espone porta
EXPOSE {port}

CMD ["./main"]""",

                'nginx': f"""# Dockerfile per sito statico con Nginx
FROM {base_image}

# Copia file statici
COPY . /usr/share/nginx/html

# Copia configurazione personalizzata (opzionale)
# COPY nginx.conf /etc/nginx/nginx.conf

# Espone porta
EXPOSE {port}

CMD ["nginx", "-g", "daemon off;"]"""
            }
            
            if language.lower() not in templates:
                available = ', '.join(templates.keys())
                return f"ERRORE: Linguaggio '{language}' non supportato. Disponibili: {available}"
            
            dockerfile = templates[language.lower()]
            
            # Aggiunge pacchetti aggiuntivi se specificati
            if packages_list:
                if language.lower() == 'python':
                    packages_section = "# Pacchetti aggiuntivi\nRUN pip install " + " ".join(packages_list)
                elif language.lower() == 'node':
                    packages_section = "# Pacchetti aggiuntivi\nRUN npm install -g " + " ".join(packages_list)
                else:
                    packages_section = f"# Pacchetti aggiuntivi: {', '.join(packages_list)}"
                
                dockerfile = dockerfile.replace("# Copia codice sorgente", packages_section + "\n\n# Copia codice sorgente")
            
            # Aggiunge .dockerignore
            dockerignore = f"""# .dockerignore per {language}
.git
.gitignore
README.md
Dockerfile
.dockerignore
node_modules
npm-debug.log
.coverage
.nyc_output
*.log
.DS_Store
.vscode
.idea"""
            
            if language.lower() == 'python':
                dockerignore += """
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.venv
venv/
.pytest_cache"""
            
            return f"""🐳 DOCKERFILE TEMPLATE GENERATO
Linguaggio: {language.title()}
Immagine base: {base_image}
Porta: {port}
Pacchetti extra: {len(packages_list)}

DOCKERFILE:
{dockerfile}

.DOCKERIGNORE:
{dockerignore}

COMANDI DOCKER:
# Build
docker build -t my-{language}-app .

# Run
docker run -p {port}:{port} my-{language}-app

# Run con volume per sviluppo
docker run -p {port}:{port} -v $(pwd):/app my-{language}-app"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_config_template(config_type: str, app_name: str, environment: str = "production") -> str:
        """
        Genera template di configurazione per diverse applicazioni.
        
        Args:
            config_type: Tipo di config (nginx, apache, docker-compose, kubernetes, env)
            app_name: Nome dell'applicazione
            environment: Ambiente (development, staging, production)
        """
        try:
            app_name_clean = re.sub(r'[^a-zA-Z0-9-]', '-', app_name.lower())
            
            templates = {
                'nginx': f"""# Configurazione Nginx per {app_name}
server {{
    listen 80;
    server_name {app_name_clean}.example.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {app_name_clean}.example.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/{app_name_clean}.crt;
    ssl_certificate_key /etc/ssl/private/{app_name_clean}.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    location / {{
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}
    
    # Static files
    location /static/ {{
        alias /var/www/{app_name_clean}/static/;
        expires 1M;
        add_header Cache-Control "public, immutable";
    }}
}}""",

                'docker-compose': f"""# Docker Compose per {app_name}
version: '3.8'

services:
  {app_name_clean}-app:
    build: .
    container_name: {app_name_clean}-app
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV={environment}
      - DATABASE_URL=postgresql://user:password@db:5432/{app_name_clean}
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - {app_name_clean}-network

  db:
    image: postgres:15
    container_name: {app_name_clean}-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB={app_name_clean}
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - {app_name_clean}-network

  redis:
    image: redis:7-alpine
    container_name: {app_name_clean}-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - {app_name_clean}-network

  nginx:
    image: nginx:alpine
    container_name: {app_name_clean}-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./ssl:/etc/ssl
    depends_on:
      - {app_name_clean}-app
    networks:
      - {app_name_clean}-network

volumes:
  postgres_data:
  redis_data:

networks:
  {app_name_clean}-network:
    driver: bridge""",

                'kubernetes': f"""# Kubernetes manifests per {app_name}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name_clean}-deployment
  labels:
    app: {app_name_clean}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {app_name_clean}
  template:
    metadata:
      labels:
        app: {app_name_clean}
    spec:
      containers:
      - name: {app_name_clean}
        image: {app_name_clean}:latest
        ports:
        - containerPort: 3000
        env:
        - name: NODE_ENV
          value: "{environment}"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: {app_name_clean}-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: {app_name_clean}-service
spec:
  selector:
    app: {app_name_clean}
  ports:
    - protocol: TCP
      port: 80
      targetPort: 3000
  type: LoadBalancer
---
apiVersion: v1
kind: Secret
metadata:
  name: {app_name_clean}-secrets
type: Opaque
data:
  database-url: # Base64 encoded database URL""",

                'env': f"""# Environment configuration per {app_name}
# Generated for {environment} environment

# Application
APP_NAME={app_name}
APP_ENV={environment}
APP_PORT=3000
APP_URL=https://{app_name_clean}.example.com

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME={app_name_clean}
DB_USER=user
DB_PASSWORD=your_secure_password_here

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Security
JWT_SECRET=your_jwt_secret_here
ENCRYPTION_KEY=your_encryption_key_here
SESSION_SECRET=your_session_secret_here

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=your_smtp_password

# External Services
API_KEY=your_api_key_here
WEBHOOK_SECRET=your_webhook_secret

# Logging
LOG_LEVEL={'DEBUG' if environment == 'development' else 'INFO'}
LOG_FILE=./logs/{app_name_clean}.log

# Rate Limiting
RATE_LIMIT_WINDOW=15
RATE_LIMIT_MAX=100

# CORS
CORS_ORIGIN={'http://localhost:3000' if environment == 'development' else 'https://' + app_name_clean + '.example.com'}""",

                'apache': f"""# Apache Virtual Host per {app_name}
<VirtualHost *:80>
    ServerName {app_name_clean}.example.com
    DocumentRoot /var/www/{app_name_clean}/public
    
    # Redirect to HTTPS
    RewriteEngine On
    RewriteCond %{{HTTPS}} off
    RewriteRule ^(.*)$ https://%{{HTTP_HOST}}%{{REQUEST_URI}} [L,R=301]
</VirtualHost>

<VirtualHost *:443>
    ServerName {app_name_clean}.example.com
    DocumentRoot /var/www/{app_name_clean}/public
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/ssl/certs/{app_name_clean}.crt
    SSLCertificateKeyFile /etc/ssl/private/{app_name_clean}.key
    
    # Security headers
    Header always set X-Frame-Options DENY
    Header always set X-Content-Type-Options nosniff
    Header always set X-XSS-Protection "1; mode=block"
    
    # Proxy to application
    ProxyPreserveHost On
    ProxyPass / http://localhost:3000/
    ProxyPassReverse / http://localhost:3000/
    
    # Static files
    Alias /static /var/www/{app_name_clean}/static
    <Directory "/var/www/{app_name_clean}/static">
        Options -Indexes
        AllowOverride None
        Require all granted
        ExpiresActive On
        ExpiresDefault "access plus 1 month"
    </Directory>
    
    # Logging
    ErrorLog ${{APACHE_LOG_DIR}}/{app_name_clean}_error.log
    CustomLog ${{APACHE_LOG_DIR}}/{app_name_clean}_access.log combined
</VirtualHost>"""
            }
            
            if config_type.lower() not in templates:
                available = ', '.join(templates.keys())
                return f"ERRORE: Tipo config '{config_type}' non supportato. Disponibili: {available}"
            
            config_content = templates[config_type.lower()]
            
            # Suggerimenti per l'environment
            env_notes = {
                'development': "Per sviluppo: debug abilitato, CORS permissivo, log verbosi",
                'staging': "Per testing: simile a produzione ma con dati di test",
                'production': "Per produzione: sicurezza massima, log minimi, cache abilitata"
            }
            
            return f"""⚙️ TEMPLATE CONFIGURAZIONE GENERATO
Tipo: {config_type.upper()}
Applicazione: {app_name}
Ambiente: {environment}
Generato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CONFIGURAZIONE:
{config_content}

📝 NOTE AMBIENTE ({environment}):
{env_notes.get(environment, 'Configurazione personalizzata')}

🔧 PROSSIMI PASSI:
1. Personalizza le credenziali e URL
2. Adatta le porte alle tue esigenze
3. Configura SSL/TLS per produzione
4. Testa la configurazione in ambiente isolato
5. Implementa monitoring e logging appropriati"""
            
        except Exception as e:
            return f"ERRORE: {str(e)}"

    @mcp.tool()
    def generate_code_template(template_type: str, class_name: str, language: str = "python", features: str = "") -> str:
        """
        Genera template di codice per classi, API, test, etc.
        
        Args:
            template_type: Tipo di template (class, api, test, crud, model)
            class_name: Nome della classe/componente
            language: Linguaggio di programmazione (python, javascript, java, go)
            features: Funzionalità aggiuntive separate da virgola
        """
        try:
            class_name_clean = re.sub(r'[^a-zA-Z0-9_]', '', class_name)
            features_list = [f.strip().lower() for f in features.split(',') if f.strip()] if features else []
            
            templates = {
                'python': {
                    'class': f'''class {class_name_clean}:
    """
    Classe {class_name_clean} per [DESCRIZIONE].
    
    Attributi:
        name (str): Nome dell'istanza
    """
    
    def __init__(self, name: str):
        """
        Inizializza {class_name_clean}.
        
        Args:
            name: Nome dell'istanza
        """
        self.name = name
        self._created_at = datetime.now()
    
    def __str__(self) -> str:
        return f"{class_name_clean}({{self.name}})"
    
    def __repr__(self) -> str:
        return f"{class_name_clean}(name='{{self.name}}')"
    
    def get_info(self) -> dict:
        """Restituisce informazioni sull'istanza."""
        return {{
            "name": self.name,
            "created_at": self._created_at.isoformat(),
            "class": self.__class__.__name__
        }}''',
                    
                    'api': f'''from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

class {class_name_clean}API:
    """API REST per gestione {class_name_clean}."""
    
    def __init__(self):
        self.data = {{}}  # Simula database in memoria
        self.next_id = 1
    
    @app.route('/{class_name_clean.lower()}', methods=['GET'])
    def get_all():
        """Ottiene tutti gli elementi."""
        return jsonify({{
            "data": list(api.data.values()),
            "count": len(api.data)
        }})
    
    @app.route('/{class_name_clean.lower()}/<int:item_id>', methods=['GET'])
    def get_one(item_id: int):
        """Ottiene un elemento specifico."""
        if item_id not in api.data:
            return jsonify({{"error": "Not found"}}), 404
        return jsonify(api.data[item_id])
    
    @app.route('/{class_name_clean.lower()}', methods=['POST'])
    def create():
        """Crea un nuovo elemento."""
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({{"error": "Invalid data"}}), 400
        
        new_item = {{
            "id": api.next_id,
            "name": data['name'],
            "created_at": datetime.now().isoformat()
        }}
        
        api.data[api.next_id] = new_item
        api.next_id += 1
        
        return jsonify(new_item), 201

# Istanza globale
api = {class_name_clean}API()

if __name__ == '__main__':
    app.run(debug=True)''',
                },
                
                'javascript': {
                    'class': f'''class {class_name_clean} {{
    /**
     * Classe {class_name_clean} per [DESCRIZIONE].
     * @param {{string}} name - Nome dell'istanza
     */
    constructor(name) {{
        this.name = name;
        this._createdAt = new Date();
    }}
    
    /**
     * Ottiene informazioni sull'istanza.
     * @returns {{Object}} Informazioni dell'istanza
     */
    getInfo() {{
        return {{
            name: this.name,
            createdAt: this._createdAt.toISOString(),
            class: this.constructor.name
        }};
    }}
    
    /**
     * Rappresentazione stringa dell'oggetto.
     * @returns {{string}} Stringa rappresentativa
     */
    toString() {{
        return `{class_name_clean}(${{this.name}})`;
    }}
    
    /**
     * Serializza l'oggetto in JSON.
     * @returns {{Object}} Oggetto serializzato
     */
    toJSON() {{
        return this.getInfo();
    }}
}}

export default {class_name_clean};''',
                    
                    'api': f'''const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

class {class_name_clean}API {{
    constructor() {{
        this.data = new Map();
        this.nextId = 1;
    }}
    
    // GET /{class_name_clean.lower()}
    getAll(req, res) {{
        const items = Array.from(this.data.values());
        res.json({{
            data: items,
            count: items.length
        }});
    }}
    
    // GET /{class_name_clean.lower()}/:id
    getOne(req, res) {{
        const id = parseInt(req.params.id);
        const item = this.data.get(id);
        
        if (!item) {{
            return res.status(404).json({{ error: 'Not found' }});
        }}
        
        res.json(item);
    }}
    
    // POST /{class_name_clean.lower()}
    create(req, res) {{
        const {{ name }} = req.body;
        
        if (!name) {{
            return res.status(400).json({{ error: 'Name required' }});
        }}
        
        const newItem = {{
            id: this.nextId,
            name,
            createdAt: new Date().toISOString()
        }};
        
        this.data.set(this.nextId, newItem);
        this.nextId++;
        
        res.status(201).json(newItem);
    }}
}}

const api = new {class_name_clean}API();

// Routes
app.get('/{class_name_clean.lower()}', (req, res) => api.getAll(req, res));
app.get('/{class_name_clean.lower()}/:id', (req, res) => api.getOne(req, res));
app.post('/{class_name_clean.lower()}', (req, res) => api.create(req, res));

app.listen(port, () => {{
    console.log(`Server running on port ${{port}}`);
}});'''
                }
            }
            
            if language.lower() not in templates:
                available = ', '.join(templates.keys())
                return f"ERRORE: Linguaggio '{language}' non supportato. Disponibili: {available}"
            
            lang_templates = templates[language.lower()]
            
            if template_type.lower() not in lang_templates:
                available = ', '.join(lang_templates.keys())
                return f"ERRORE: Template '{template_type}' non disponibile per {language}. Disponibili: {available}"
            
            code = lang_templates[template_type.lower()]
            
            # Aggiunge features se richieste
            features_code = ""
            if 'validation' in features_list:
                if language.lower() == 'python':
                    features_code += """
    def validate(self) -> bool:
        \"\"\"Valida l'istanza.\"\"\"
        return bool(self.name and len(self.name.strip()) > 0)"""
                elif language.lower() == 'javascript':
                    features_code += """
    validate() {
        return Boolean(this.name && this.name.trim().length > 0);
    }"""
            
            if 'serialization' in features_list:
                if language.lower() == 'python':
                    features_code += """
    def to_dict(self) -> dict:
        \"\"\"Converte in dizionario.\"\"\"
        return self.get_info()
    
    @classmethod
    def from_dict(cls, data: dict):
        \"\"\"Crea istanza da dizionario.\"\"\"
        return cls(data['name'])"""
            
            if features_code:
                code = code.replace('    def get_info(self)', features_code + '\n\n    def get_info(self)')
                code = code.replace('    getInfo() {', features_code + '\n\n    getInfo() {')
            
            # File di supporto
            support_files = {}
            
            if template_type == 'api':
                if language.lower() == 'python':
                    support_files['requirements.txt'] = "flask==2.3.3\nflask-cors==4.0.0"
                    support_files['run.py'] = f"from {class_name_clean.lower()}_api import app\n\nif __name__ == '__main__':\n    app.run(debug=True, host='0.0.0.0', port=5000)"
                elif language.lower() == 'javascript':
                    support_files['package.json'] = f'''{{
  "name": "{class_name_clean.lower()}-api",
  "version": "1.0.0",
  "description": "API per {class_name_clean}",
  "main": "index.js",
  "scripts": {{
    "start": "node index.js",
    "dev": "nodemon index.js"
  }},
  "dependencies": {{
    "express": "^4.18.2"
  }},
  "devDependencies": {{
    "nodemon": "^3.0.1"
  }}
}}'''
            
            result = f"""💻 TEMPLATE CODICE GENERATO
Tipo: {template_type.title()}
Classe: {class_name_clean}
Linguaggio: {language.title()}
Features: {', '.join(features_list) if features_list else 'Nessuna'}

CODICE PRINCIPALE:
{code}"""
            
            if support_files:
                result += "\n\nFILE DI SUPPORTO:"
                for filename, content in support_files.items():
                    result += f"\n\n{filename}:\n{content}"
            
            result += f"""

📋 ISTRUZIONI:
1. Copia il codice in un file appropriato
2. Personalizza la [DESCRIZIONE] e i commenti
3. Installa le dipendenze se necessarie
4. Testa il codice in un ambiente di sviluppo
5. Aggiungi test unitari appropriati"""
            
            return result
            
        except Exception as e:
            return f"ERRORE: {str(e)}"