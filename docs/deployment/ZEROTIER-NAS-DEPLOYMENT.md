# ZeroTier NAS Deployment Guide

Complete guide for deploying the German Language Learning Platform on NAS with ZeroTier network access.

## 🌐 ZeroTier Network Setup

### Prerequisites
1. ZeroTier account and network created
2. NAS device joined to ZeroTier network
3. Client devices joined to same ZeroTier network
4. ZeroTier IPs assigned to all devices

### Step 1: Find Your ZeroTier IPs

**On NAS (server):**
```bash
# Check ZeroTier network status
sudo zerotier-cli listnetworks

# Find ZeroTier interface IP
ip addr show | grep zt
# or
ifconfig | grep zt
```

**On Client Devices:**
```bash
# Windows/Mac/Linux
zerotier-cli listnetworks

# Or check ZeroTier Central dashboard
# https://my.zerotier.com -> Your Network -> Members
```

**Example Output:**
```
200 listnetworks 1234567890abcdef 10.147.20.0/24 OK PRIVATE zt1234567890
Your ZeroTier IP: 10.147.20.100 (NAS)
Client ZeroTier IP: 10.147.20.101 (laptop)
```

## ⚙️ Configuration for ZeroTier

### Step 2: Configure Environment
```bash
# Copy ZeroTier NAS configuration
cp .env.nas .env

# Edit .env with your ZeroTier IPs
nano .env
```

### Step 3: Set ZeroTier CORS Hosts
```bash
# In .env file, replace with YOUR actual ZeroTier IPs:
ADDITIONAL_ALLOWED_HOSTS=http://10.147.20.100:8080,http://10.147.20.101:3000,http://10.147.20.102:3000

# Format explanation:
# http://[nas-zerotier-ip]:[backend-port],http://[client-zerotier-ip]:[frontend-port]
```

### Step 4: Complete Configuration Example
```bash
# Security
SECRET_KEY=AbCdEf123456789...  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
HTTPS_ONLY=false
ENVIRONMENT=production

# ZeroTier Network CORS
ADDITIONAL_ALLOWED_HOSTS=http://10.147.20.100:8080,http://10.147.20.101:3000,http://10.147.20.102:3000,http://10.147.20.103:3000

# OpenAI
OPENAI_API_KEY=your-openai-key-here
```

## 🚀 Deployment Steps

### 1. Backend Deployment (on NAS)
```bash
# Set environment
export ADDITIONAL_ALLOWED_HOSTS="http://10.147.20.100:8080,http://10.147.20.101:3000"
export HTTPS_ONLY=false
export SECRET_KEY="your-generated-key"

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8080
# or
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 2. Frontend Access (from any ZeroTier device)
```bash
# Access the application via ZeroTier IP
http://10.147.20.100:8080

# Or if running separate frontend:
# Frontend: http://10.147.20.100:3000
# Backend API: http://10.147.20.100:8080
```

## 📱 Multi-Device Access

### Add Multiple Client Devices
```bash
# In .env, add all your ZeroTier device IPs:
ADDITIONAL_ALLOWED_HOSTS=http://10.147.20.100:8080,http://10.147.20.101:3000,http://10.147.20.102:3000,http://10.147.20.103:3000,http://10.147.20.104:3000

# Device mapping example:
# 10.147.20.100 = NAS (server)
# 10.147.20.101 = Laptop
# 10.147.20.102 = Desktop
# 10.147.20.103 = Phone/Tablet
# 10.147.20.104 = Another device
```

### Dynamic Device Addition
If you add new devices to your ZeroTier network:

1. Check new device's ZeroTier IP
2. Add to `ADDITIONAL_ALLOWED_HOSTS` in .env
3. Restart the application
4. New device can now access the platform

## 🔐 Security Considerations

### ZeroTier Network Security
- **Encrypted Traffic**: ZeroTier provides end-to-end encryption
- **Network Isolation**: Only ZeroTier members can access
- **Access Control**: Manage device access via ZeroTier Central

### Application Security (maintained)
- ✅ httpOnly cookies (XSS protection)
- ✅ SameSite cookies (CSRF protection)
- ✅ Rate limiting
- ✅ Security headers
- ✅ Input validation
- ✅ JWT token security

### Network Access Control
```bash
# ZeroTier Central Dashboard Settings:
# 1. Set network to Private (not Public)
# 2. Manually authorize each device
# 3. Assign static IPs if needed
# 4. Use flow rules for additional security
```

## 🛠️ Troubleshooting

### Common Issues

**Problem**: "CORS error" when accessing from client
```bash
# Solution: Check ADDITIONAL_ALLOWED_HOSTS includes your client IP
ADDITIONAL_ALLOWED_HOSTS=http://10.147.20.100:8080,http://YOUR_CLIENT_IP:3000
```

**Problem**: Login doesn't work
```bash
# Solution: Ensure HTTPS_ONLY=false for HTTP
HTTPS_ONLY=false
```

**Problem**: Can't connect to NAS
```bash
# Check ZeroTier connection
zerotier-cli peers
ping 10.147.20.100  # Your NAS ZeroTier IP

# Check if service is running
netstat -an | grep 8080
```

**Problem**: New device can't access
```bash
# 1. Verify device is in ZeroTier network
zerotier-cli listnetworks

# 2. Add device IP to CORS
ADDITIONAL_ALLOWED_HOSTS=...previous_ips...,http://NEW_DEVICE_IP:3000

# 3. Restart application
```

### Debug Commands
```bash
# Check current CORS configuration
curl http://10.147.20.100:8080/debug/cors

# Test connectivity
curl -H "Origin: http://10.147.20.101:3000" http://10.147.20.100:8080/health

# Check ZeroTier status
sudo zerotier-cli info
sudo zerotier-cli peers
```

## 📋 Quick Setup Checklist

- [ ] ZeroTier network created and devices joined
- [ ] ZeroTier IPs identified for NAS and clients
- [ ] .env file configured with ZeroTier IPs
- [ ] HTTPS_ONLY=false set
- [ ] SECRET_KEY generated and set
- [ ] ADDITIONAL_ALLOWED_HOSTS includes all device IPs
- [ ] Application started on NAS
- [ ] Client devices can access via ZeroTier IP
- [ ] Login functionality tested
- [ ] All features working correctly

## 🌍 Remote Access Benefits

With ZeroTier + NAS deployment, you get:

1. **Global Access**: Access your platform from anywhere
2. **No Port Forwarding**: No router configuration needed
3. **Secure Tunnel**: Encrypted ZeroTier connection
4. **Multiple Devices**: Support for phones, tablets, laptops
5. **Dynamic IPs**: Easy device management
6. **LAN Performance**: Fast speeds within ZeroTier network

Your German Language Learning Platform is now accessible globally via your secure ZeroTier network! 🚀