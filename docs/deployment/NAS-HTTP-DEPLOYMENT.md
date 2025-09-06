# NAS HTTP Deployment Guide

This guide explains how to deploy the German Language Learning Platform on NAS systems using HTTP connections while maintaining security.

## Quick Setup for NAS (HTTP)

### 1. Configuration
```bash
# Copy the NAS-specific environment file
cp .env.nas .env

# Edit .env with your settings:
# - Set your SECRET_KEY
# - Add your NAS IP to ALLOWED_HOSTS
# - Configure OpenAI API key
```

### 2. Environment Variables for NAS
```bash
# Required for HTTP deployment
HTTPS_ONLY=false          # Allows cookies over HTTP
SECRET_KEY=your-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add your NAS IP address
ALLOWED_HOSTS=http://192.168.1.100:8080,http://localhost:3000
```

### 3. Security Features Still Active
Even over HTTP, the following security features remain active:

✅ **httpOnly Cookies**: Prevents XSS attacks  
✅ **SameSite Protection**: CSRF attack prevention  
✅ **Rate Limiting**: Brute force protection  
✅ **Security Headers**: XSS, clickjacking protection  
✅ **Input Validation**: SQL injection prevention  
✅ **JWT Security**: Secure token validation  

### 4. What Changes for HTTP
- `secure=false` on cookies (allows HTTP transmission)
- Cookies still protected from JavaScript access
- All other security measures remain intact

## Deployment Types

### Production HTTPS
```bash
HTTPS_ONLY=true
ENVIRONMENT=production
```

### NAS/Local HTTP  
```bash
HTTPS_ONLY=false
ENVIRONMENT=development  # or production
```

### Development
```bash
HTTPS_ONLY=false
ENVIRONMENT=development
DEBUG=true
```

## Network Security Recommendations

For NAS deployments, consider these additional protections:

1. **Network Isolation**: Use VPN or local network only
2. **Firewall Rules**: Restrict access to trusted IPs
3. **Regular Updates**: Keep the platform updated
4. **Strong Passwords**: Use secure authentication
5. **Backup Strategy**: Regular data backups

## Testing HTTP Deployment

1. Start the application
2. Access via browser: `http://your-nas-ip:port`
3. Test login functionality
4. Verify cookies are set correctly
5. Confirm all features work

The authentication system automatically adapts to HTTP/HTTPS based on the `HTTPS_ONLY` setting.

## Troubleshooting

**Problem**: Login doesn't work over HTTP  
**Solution**: Ensure `HTTPS_ONLY=false` in your `.env` file

**Problem**: CORS errors  
**Solution**: Add your NAS IP to `ALLOWED_HOSTS`

**Problem**: Cookies not persisting  
**Solution**: Check that `secure=false` for HTTP deployments

## Security Note

While HTTP is supported for NAS deployments, HTTPS is always recommended for production internet-facing deployments. The HTTP support is designed for:

- Local network deployments
- NAS systems without SSL certificates
- Development and testing environments
- Internal corporate networks

For maximum security, consider setting up SSL certificates on your NAS if possible.