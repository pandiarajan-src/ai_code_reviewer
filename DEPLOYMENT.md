# AI Code Reviewer - Deployment Guide

This comprehensive guide covers all deployment scenarios for the AI Code Reviewer agent, from development setup to production deployment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Bitbucket Configuration](#bitbucket-configuration)
7. [LLM Provider Setup](#llm-provider-setup)
8. [Security Configuration](#security-configuration)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **Memory**: Minimum 2GB RAM, recommended 4GB+
- **Storage**: 10GB free space
- **Network**: Internet access for LLM APIs, internal network access to Bitbucket server

### Software Requirements

- **Docker**: Version 20.10+ and Docker Compose v2.0+
- **Python**: Version 3.12+ (for local development)
- **Git**: For cloning the repository

### Access Requirements

- **Bitbucket Enterprise Server**: Admin access to configure webhooks
- **Service Account**: Dedicated Bitbucket user account for the agent
- **LLM Provider**: OpenAI API key OR local Ollama installation
- **Email Service**: Azure Logic App configured for email delivery (or equivalent)

## Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd ai_code_reviewer
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r test_requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 4. Run Tests

```bash
# Run comprehensive test suite
python run_tests.py

# Run specific tests
pytest tests/test_config.py -v
```

### 5. Start Development Server

```bash
# Start the server
python main.py

# Server will be available at http://localhost:8000
```

## Docker Deployment

### Quick Start with Docker Compose

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your settings

# 2. Start services
docker-compose up -d

# 3. Check status
docker-compose ps
docker-compose logs -f ai-code-reviewer
```

### Custom Docker Build

```bash
# Build custom image
docker build -t my-ai-code-reviewer .

# Run with custom configuration
docker run -d \
  --name ai-code-reviewer \
  -p 8000:8000 \
  -e BITBUCKET_URL=https://your-bitbucket.com \
  -e BITBUCKET_TOKEN=your_token \
  -e LLM_PROVIDER=openai \
  -e LLM_API_KEY=your_api_key \
  my-ai-code-reviewer
```

### Docker Compose with Local LLM

```bash
# Start with Ollama included
docker-compose --profile local-llm up -d

# Pull models into Ollama
docker exec -it ai_code_reviewer_ollama_1 ollama pull qwen-coder
docker exec -it ai_code_reviewer_ollama_1 ollama pull llama3
```

## Production Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply group changes
```

### 2. Application Deployment

```bash
# Create application directory
sudo mkdir -p /opt/ai-code-reviewer
sudo chown $USER:$USER /opt/ai-code-reviewer
cd /opt/ai-code-reviewer

# Clone repository
git clone <repository-url> .

# Configure production environment
cp .env.example .env
nano .env
```

### 3. Production Environment Configuration

```bash
# Production .env file
BITBUCKET_URL=https://bitbucket.yourcompany.com
BITBUCKET_TOKEN=your_production_token

LLM_PROVIDER=openai
LLM_API_KEY=your_production_api_key
LLM_MODEL=gpt-4o

WEBHOOK_SECRET=your_secure_webhook_secret

# Production settings
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Email configuration
LOGIC_APP_EMAIL_URL=https://your-prod-logic-app-url
LOGIC_APP_FROM_EMAIL=noreply@yourcompany.com
EMAIL_OPTOUT=false
```

### 4. SSL/TLS Configuration

#### Option A: Reverse Proxy with Nginx

```bash
# Install Nginx
sudo apt install nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/ai-code-reviewer
```

```nginx
server {
    listen 80;
    server_name ai-code-reviewer.yourcompany.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ai-code-reviewer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Install SSL certificate (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ai-code-reviewer.yourcompany.com
```

#### Option B: Docker with SSL

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  ai-code-reviewer:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BITBUCKET_URL=${BITBUCKET_URL}
      - BITBUCKET_TOKEN=${BITBUCKET_TOKEN}
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_API_KEY=${LLM_API_KEY}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
    volumes:
      - ./logs:/app/logs
      - ./ssl:/app/ssl:ro
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - ai-code-reviewer
    restart: unless-stopped
```

### 5. Systemd Service (Alternative to Docker)

```bash
# Create systemd service
sudo nano /etc/systemd/system/ai-code-reviewer.service
```

```ini
[Unit]
Description=AI Code Reviewer Agent
After=network.target

[Service]
Type=simple
User=ai-reviewer
WorkingDirectory=/opt/ai-code-reviewer
Environment=PATH=/opt/ai-code-reviewer/venv/bin
ExecStart=/opt/ai-code-reviewer/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Create service user
sudo useradd -r -s /bin/false ai-reviewer
sudo chown -R ai-reviewer:ai-reviewer /opt/ai-code-reviewer

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ai-code-reviewer
sudo systemctl start ai-code-reviewer
sudo systemctl status ai-code-reviewer
```

## Kubernetes Deployment

### 1. Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ai-code-reviewer
```

### 2. Create Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-code-reviewer-secrets
  namespace: ai-code-reviewer
type: Opaque
stringData:
  bitbucket-token: "your_bitbucket_token"
  llm-api-key: "your_llm_api_key"
  webhook-secret: "your_webhook_secret"
  logic-app-email-url: "https://your-logic-app-url"
```

### 3. Create ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ai-code-reviewer-config
  namespace: ai-code-reviewer
data:
  BITBUCKET_URL: "https://bitbucket.yourcompany.com"
  LLM_PROVIDER: "openai"
  LLM_MODEL: "gpt-4o"
  LLM_ENDPOINT: "https://api.openai.com/v1/chat/completions"
  LOGIC_APP_FROM_EMAIL: "noreply@yourcompany.com"
  EMAIL_OPTOUT: "false"
  HOST: "0.0.0.0"
  PORT: "8000"
  LOG_LEVEL: "INFO"
```

### 4. Create Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-code-reviewer
  namespace: ai-code-reviewer
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-code-reviewer
  template:
    metadata:
      labels:
        app: ai-code-reviewer
    spec:
      containers:
      - name: ai-code-reviewer
        image: ai-code-reviewer:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: ai-code-reviewer-config
        env:
        - name: BITBUCKET_TOKEN
          valueFrom:
            secretKeyRef:
              name: ai-code-reviewer-secrets
              key: bitbucket-token
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: ai-code-reviewer-secrets
              key: llm-api-key
        - name: WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: ai-code-reviewer-secrets
              key: webhook-secret
        - name: LOGIC_APP_EMAIL_URL
          valueFrom:
            secretKeyRef:
              name: ai-code-reviewer-secrets
              key: logic-app-email-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### 5. Create Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-code-reviewer-service
  namespace: ai-code-reviewer
spec:
  selector:
    app: ai-code-reviewer
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
```

### 6. Create Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-code-reviewer-ingress
  namespace: ai-code-reviewer
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - ai-code-reviewer.yourcompany.com
    secretName: ai-code-reviewer-tls
  rules:
  - host: ai-code-reviewer.yourcompany.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-code-reviewer-service
            port:
              number: 80
```

### 7. Deploy to Kubernetes

```bash
# Apply all configurations
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Check deployment status
kubectl get pods -n ai-code-reviewer
kubectl logs -f deployment/ai-code-reviewer -n ai-code-reviewer
```

## Bitbucket Configuration

### 1. Create Service Account

1. Log into Bitbucket as an administrator
2. Create a new user account (e.g., `ai-code-reviewer`)
3. Add the account to relevant projects with appropriate permissions

### 2. Generate Access Token

1. Log in as the service account
2. Go to **Personal Settings > HTTP access tokens**
3. Create a new token with permissions:
   - **Repositories: Read**
   - **Pull requests: Write**
4. Copy the token securely

### 3. Configure Repository Webhooks

For each repository where you want AI code reviews:

1. Go to **Repository Settings > Webhooks**
2. Click **Create webhook**
3. Configure webhook:
   - **Name**: AI Code Reviewer
   - **URL**: `https://your-agent-server.com/webhook/code-review`
   - **Secret**: Your webhook secret (if configured)
   - **Events**: Select:
     - Pull request → Opened
     - Pull request → Source updated
     - Repository → Push (optional, for commit reviews)
4. **Save** and **Enable** the webhook

### 4. Test Webhook

```bash
# Test webhook delivery
curl -X POST https://your-agent-server.com/webhook/code-review \
  -H "Content-Type: application/json" \
  -d '{
    "eventKey": "pr:opened",
    "date": "2024-01-01T00:00:00Z",
    "repository": {
      "slug": "test-repo",
      "project": {"key": "TEST"}
    },
    "pullRequest": {"id": 123}
  }'
```

## LLM Provider Setup

### OpenAI Configuration

1. **Create OpenAI Account**: Sign up at https://platform.openai.com
2. **Generate API Key**: Go to API Keys section and create a new key
3. **Set Usage Limits**: Configure usage limits to control costs
4. **Configure Environment**:
   ```bash
   LLM_PROVIDER=openai
   LLM_API_KEY=sk-your-api-key-here
   LLM_MODEL=gpt-4o
   LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
   ```

### Local Ollama Setup

1. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

2. **Pull Models**:
   ```bash
   ollama pull qwen-coder
   ollama pull llama3
   ollama pull codellama
   ```

3. **Configure Environment**:
   ```bash
   LLM_PROVIDER=local_ollama
   OLLAMA_HOST=http://localhost:11434
   LLM_MODEL=qwen-coder
   ```

4. **Start Ollama Service**:
   ```bash
   # Start Ollama server
   ollama serve

   # Or as systemd service
   sudo systemctl enable ollama
   sudo systemctl start ollama
   ```

## Email Service Configuration

The agent uses Azure Logic Apps for email delivery. Configure your email service for review notifications.

### Azure Logic App Setup

1. **Create Logic App**:
   - Go to Azure Portal
   - Create a new Logic App in your resource group
   - Choose consumption plan for cost-effectiveness

2. **Configure HTTP Trigger**:
   ```json
   {
     "method": "POST",
     "relativePath": "/",
     "schema": {
       "type": "object",
       "properties": {
         "to": {"type": "string"},
         "cc": {"type": "string"},
         "subject": {"type": "string"},
         "mailbody": {"type": "string"}
       }
     }
   }
   ```

3. **Add Email Connector**:
   - Add Office 365 Outlook or SMTP connector
   - Configure authentication (service account recommended)
   - Map request body parameters to email fields

4. **Test Logic App**:
   ```bash
   curl -X POST "https://your-logic-app-url" \
     -H "Content-Type: application/json" \
     -d '{
       "to": "developer@company.com",
       "cc": "",
       "subject": "Test AI Code Review",
       "mailbody": "<h1>Test Email</h1><p>This is a test review.</p>"
     }'
   ```

### Alternative Email Services

#### SendGrid Configuration
```bash
# Install SendGrid SDK in your custom implementation
pip install sendgrid

# Configure environment
SENDGRID_API_KEY=your_sendgrid_api_key
EMAIL_SERVICE_TYPE=sendgrid
```

#### AWS SES Configuration
```bash
# Configure AWS credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
EMAIL_SERVICE_TYPE=ses
```

### Email Configuration Environment Variables

```bash
# Azure Logic App (default)
LOGIC_APP_EMAIL_URL=https://your-logic-app-url.azurewebsites.net/api/triggers/manual/invoke?code=your-code
LOGIC_APP_FROM_EMAIL=noreply@yourcompany.com
EMAIL_OPTOUT=false

# Email testing
EMAIL_OPTOUT=true  # Disables email sending for development
```

## Security Configuration

### 1. Webhook Security

```bash
# Generate secure webhook secret
openssl rand -hex 32

# Add to environment
WEBHOOK_SECRET=your_generated_secret
```

### 2. Network Security

```bash
# Configure firewall (UFW example)
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access to app port
sudo ufw enable
```

### 3. SSL/TLS Configuration

```bash
# Generate self-signed certificate (for testing)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Or use Let's Encrypt for production
sudo certbot certonly --standalone -d your-domain.com
```

### 4. Environment Security

```bash
# Secure environment file
chmod 600 .env
chown root:root .env

# Use Docker secrets in production
echo "your_secret" | docker secret create bitbucket_token -
```

## Monitoring and Maintenance

### 1. Health Monitoring

```bash
# Check application health
curl https://your-agent-server.com/health

# Monitor with systemd
sudo systemctl status ai-code-reviewer

# Monitor with Docker
docker-compose logs -f ai-code-reviewer
```

### 2. Log Management

```bash
# Configure log rotation
sudo nano /etc/logrotate.d/ai-code-reviewer
```

```
/opt/ai-code-reviewer/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ai-reviewer ai-reviewer
    postrotate
        systemctl reload ai-code-reviewer
    endscript
}
```

### 3. Backup Strategy

```bash
# Backup configuration
tar -czf ai-code-reviewer-backup-$(date +%Y%m%d).tar.gz \
  /opt/ai-code-reviewer/.env \
  /opt/ai-code-reviewer/config.py

# Automated backup script
#!/bin/bash
BACKUP_DIR="/backup/ai-code-reviewer"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/config-$DATE.tar.gz \
  /opt/ai-code-reviewer/.env \
  /opt/ai-code-reviewer/config.py

# Keep only last 30 days
find $BACKUP_DIR -name "config-*.tar.gz" -mtime +30 -delete
```

### 4. Update Procedure

```bash
# Update application
cd /opt/ai-code-reviewer
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Or for systemd
sudo systemctl restart ai-code-reviewer
```

## Troubleshooting

### Common Issues

#### 1. Webhook Not Received

**Symptoms**: No webhook events in logs
**Solutions**:
```bash
# Check network connectivity
curl -I https://your-agent-server.com/health

# Check webhook configuration in Bitbucket
# Verify webhook URL and events

# Check firewall rules
sudo ufw status
```

#### 2. LLM Connection Failed

**Symptoms**: Health check shows LLM connection failed
**Solutions**:
```bash
# For OpenAI
curl -H "Authorization: Bearer $LLM_API_KEY" \
  https://api.openai.com/v1/models

# For Ollama
curl http://localhost:11434/api/tags

# Check environment variables
env | grep LLM
```

#### 3. Bitbucket API Errors

**Symptoms**: Cannot fetch diffs or post comments
**Solutions**:
```bash
# Test Bitbucket API access
curl -H "Authorization: Bearer $BITBUCKET_TOKEN" \
  https://your-bitbucket.com/rest/api/1.0/application-properties

# Check token permissions
# Verify repository access
```

#### 4. High Memory Usage

**Symptoms**: Container or process using excessive memory
**Solutions**:
```bash
# Monitor memory usage
docker stats ai-code-reviewer

# Adjust Docker memory limits
# Optimize LLM model selection
# Implement request queuing
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
python main.py

# Or with Docker
docker-compose up ai-code-reviewer
```

### Performance Tuning

```bash
# Optimize for high load
# Increase worker processes
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Configure connection pooling
# Implement request caching
# Use async processing for webhooks
```

This deployment guide provides comprehensive instructions for all deployment scenarios. Choose the approach that best fits your infrastructure and security requirements.

