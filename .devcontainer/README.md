# Devcontainer Configuration

This directory contains the Docker and devcontainer configuration for the Treasure Hunt Agent project.

## Files

- **`devcontainer.json`**: VS Code devcontainer configuration for GitHub Codespaces
- **`docker-compose.yml`**: Docker Compose configuration with security settings
- **`Dockerfile`**: (Located in project root) Container image definition
- **`SECURITY.md`**: Comprehensive security documentation
- **`setup-network-filter.sh`**: Optional network filtering script

## Quick Start

### GitHub Codespaces

1. Open this repository in GitHub
2. Click **Code** → **Codespaces** → **Create codespace**
3. Wait for the container to build and start
4. Set your API key: `export GOOGLE_API_KEY='your-key'`
5. Start coding!

### Local Development with Docker

```bash
# From project root
docker-compose -f .devcontainer/docker-compose.yml up -d
docker-compose -f .devcontainer/docker-compose.yml exec agent bash
```

### VS Code with Dev Containers Extension

1. Install the "Dev Containers" extension
2. Open this project in VS Code
3. Press `F1` → "Dev Containers: Reopen in Container"
4. VS Code will build and connect to the container

## Container Features

### Security

- Runs as non-root user (`agentuser`, UID 1000)
- Dropped capabilities (minimal permissions)
- Network isolated with configurable restrictions
- Resource limits (CPU, memory)
- No new privileges allowed

### Development Tools

- Python 3.13
- uv package manager (fast dependency installation)
- Git
- Zsh shell (optional)

### VS Code Extensions (Auto-installed)

- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)
- Black Formatter (ms-python.black-formatter)

## Environment Variables

Set these in your shell or in `.env`:

```bash
# Required for running the agent
export GOOGLE_API_KEY='your-gemini-api-key'
```

## Network Access

The container allows access to:

- Google Gemini API (generativelanguage.googleapis.com)
- PyPI (for package installation)
- GitHub (for git operations)

For additional network restrictions, see `SECURITY.md`.

## Troubleshooting

### Container won't start

```bash
# Check Docker logs
docker-compose -f .devcontainer/docker-compose.yml logs

# Rebuild from scratch
docker-compose -f .devcontainer/docker-compose.yml down -v
docker-compose -f .devcontainer/docker-compose.yml build --no-cache
docker-compose -f .devcontainer/docker-compose.yml up -d
```

### Permission issues

```bash
# Inside container, check current user
whoami  # Should be: agentuser
id      # Should show UID 1000

# Fix ownership (if needed)
sudo chown -R agentuser:agentuser /app
```

### Can't install packages

```bash
# Make sure you're using uv
uv sync

# If uv isn't found, check PATH
echo $PATH | grep cargo
```

### API calls failing

```bash
# Check environment variable
echo $GOOGLE_API_KEY

# Test connectivity
curl https://generativelanguage.googleapis.com

# Check network restrictions
# See SECURITY.md for network troubleshooting
```

## Customization

### Adding Python Packages

Edit `pyproject.toml` and run:

```bash
uv add package-name
uv sync
```

### Adding VS Code Extensions

Edit `devcontainer.json` → `customizations.vscode.extensions`

### Changing User ID

If you need a different UID (e.g., to match your host system):

1. Edit `Dockerfile`: Change `useradd -r -g agentuser -u 1000`
2. Edit `docker-compose.yml`: Update UID/GID references
3. Edit `devcontainer.json`: Update `userUid` and `userGid`

### Adjusting Resource Limits

Edit `docker-compose.yml` → `deploy.resources` section.

## Security

For comprehensive security information, see [`SECURITY.md`](SECURITY.md).

## Additional Resources

- [VS Code Dev Containers Documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
