# NAS Deployment Configuration
# Copy this to .env for HTTP-based NAS deployments

# Security Configuration
SECRET_KEY=your-secure-secret-key-here
ENVIRONMENT=development

# HTTP Deployment Settings (NAS-friendly)
HTTPS_ONLY=false
DEBUG=false

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Database
DATABASE_URL=sqlite:///./data/app.db

# CORS Configuration for ZeroTier NAS Deployment
# Add your ZeroTier network IPs here
# Find your ZeroTier IPs with: zerotier-cli listnetworks
# Example ZeroTier IP ranges: 10.147.x.x, 172.x.x.x, 192.168.x.x
# 
ADDITIONAL_ALLOWED_HOSTS=http://10.147.20.100:8080,http://10.147.20.101:3000
#
# Replace 10.147.20.x with your actual ZeroTier IPs:
# - 10.147.20.100 = Your NAS ZeroTier IP
# - 10.147.20.101 = Your client device ZeroTier IP (optional)
# - Add multiple devices: http://ip1:port,http://ip2:port,http://ip3:port

# Generate a secure secret key:
# python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"