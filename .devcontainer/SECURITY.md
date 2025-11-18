# Docker Security Configuration

This document describes the security measures implemented in the Docker container setup for the Treasure Hunt Agent.

## Security Features

### 1. Non-Root User Execution

The agent runs as a non-privileged user (`agentuser` with UID 1000) instead of root:

- **User**: `agentuser`
- **UID**: 1000
- **GID**: 1000
- **Home**: `/home/agentuser`

This prevents privilege escalation attacks and limits the damage if the container is compromised.

### 2. Dropped Capabilities

The container drops all Linux capabilities by default and only adds back what's necessary:

```yaml
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE  # Only if binding to ports <1024 is needed
```

### 3. Security Options

- **no-new-privileges**: Prevents processes from gaining additional privileges
- **Resource limits**: CPU and memory constraints prevent resource exhaustion attacks

### 4. Read-Only Filesystem (Optional)

The root filesystem can be made read-only with specific writable mount points:

- `/tmp` - Temporary files (with noexec, nosuid flags)
- `/app/treasure_hunt` - Treasure hunt data directory

### 5. Network Restrictions

#### Trusted Domains

The agent requires access to these domains:

**Required**:
- `generativelanguage.googleapis.com` - Google Gemini API
- `*.googleapis.com` - Google API infrastructure

**Optional** (for development):
- `pypi.org` - Python packages
- `files.pythonhosted.org` - Python package hosting
- `github.com` - Git operations

#### Network Filtering Options

##### Option 1: Basic Port Restrictions (Default)

The docker-compose configuration uses a bridge network with isolated subnet.

##### Option 2: Advanced Domain Filtering (Optional)

For stricter control, run the network filter setup script:

```bash
sudo .devcontainer/setup-network-filter.sh
```

**Note**: This script uses iptables and requires root privileges.

##### Option 3: Proxy-Based Filtering (Production)

For production deployments, consider using a proxy server like Squid:

```bash
# Install squid
apt-get install squid

# Configure allowed domains in /etc/squid/squid.conf
acl allowed_sites dstdomain .googleapis.com .google.com
http_access allow allowed_sites
http_access deny all

# Set proxy in container
export HTTPS_PROXY=http://proxy:3128
```

## Verifying Security Settings

### Check User Privileges

```bash
# Inside container
whoami  # Should output: agentuser
id      # Should show uid=1000(agentuser) gid=1000(agentuser)
```

### Check Capabilities

```bash
# Inside container
capsh --print
```

### Test Network Restrictions

```bash
# Inside container - these should work
curl https://generativelanguage.googleapis.com
curl https://pypi.org

# If network filtering is enabled, this should fail
curl https://example.com
```

### Check File Permissions

```bash
# Inside container
ls -la /app
# Files should be owned by agentuser:agentuser
```

## Environment Variables

Sensitive data should be provided via environment variables:

```bash
# Set API key securely
export GOOGLE_API_KEY='your-api-key-here'
```

**Never commit API keys or secrets to the repository.**

## Resource Limits

Default limits in docker-compose.yml:

- **CPU**: 2 cores max, 0.5 cores reserved
- **Memory**: 2GB max, 512MB reserved
- **Temp space**: 100MB in /tmp

Adjust these based on your requirements and available resources.

## Security Best Practices

1. **API Keys**: Always use environment variables, never hardcode
2. **Updates**: Regularly update the base image and dependencies
3. **Logs**: Review logs for suspicious activity
4. **Scanning**: Use tools like `docker scan` or Trivy to check for vulnerabilities
5. **Isolation**: Run the container in an isolated network
6. **Monitoring**: Monitor resource usage and network connections

## Scanning for Vulnerabilities

```bash
# Using Docker's built-in scanner
docker scan treasure-hunt-agent

# Using Trivy
trivy image treasure-hunt-agent

# Using Snyk
snyk container test treasure-hunt-agent
```

## Incident Response

If you suspect a security breach:

1. Stop the container immediately: `docker-compose down`
2. Inspect logs: `docker-compose logs agent`
3. Check for unauthorized network connections
4. Review file system changes
5. Rotate all API keys and secrets
6. Report the incident to your security team

## Compliance

This configuration follows:

- Docker security best practices
- CIS Docker Benchmark guidelines
- OWASP Container Security principles

## Additional Resources

- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [OWASP Container Security](https://owasp.org/www-project-docker-top-10/)
