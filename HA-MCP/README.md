# 🏠 HA-MCP + Pi.dev Setup - Complete Guide

This directory configures **Home Assistant Automation** via Pi.dev / Claude Code using MCP (Model Context Protocol).

---

## 📦 Architecture

This project uses git submodules to combine three powerful components:

1. **`ha-mcp`** (submodule): The MCP server that securely connects to your Home Assistant instance, exposing entities, services, and areas.
2. **`pi-mcp-adapter`** (submodule): An MCP proxy required for Pi.dev integration.
3. **`ha-skills`** (submodule in `.pi/ha-skills`): Specialized skills that teach the AI how to interact with Home Assistant optimally.

✅ **Expert Skills** (auto-activating via `.pi/settings.json`)
The AI understands Home Assistant best practices, automation concepts, and how to write valid YAML configurations or use the MCP tools.

✅ **MCP Support**
- Works natively with Claude Code
- Works in Pi.dev via the `pi-mcp-adapter` submodule

---

## ⚡ Setup Instructions

### Step 1: Initialize Submodules
If you just cloned this repository (or pulled the latest changes), ensure all submodules are loaded:
```bash
git submodule update --init --recursive
```

### Step 2: Install Dependencies
Because we use submodules, you need to install the dependencies for both the MCP server and the adapter locally on your machine.

**For `ha-mcp` (requires `uv`):**
```bash
cd ha-mcp
uv sync
cd ..
```
*(This creates the `.venv` directory and installs all Python dependencies).*

**For `pi-mcp-adapter` (requires Node.js):**
```bash
cd pi-mcp-adapter
npm install
cd ..
```

### Step 3: Configure Credentials
1. Navigate to the `ha-mcp` folder.
2. Create or edit the `.env` file (you can copy from `.env.example`).
3. Fill in your Home Assistant URL and Long-Lived Access Token:

```env
# ha-mcp/.env
HOMEASSISTANT_URL=http://your-homeassistant.local:8123
HOMEASSISTANT_TOKEN=eyJhbGciOiJIUzI1NiIsIn...
```
*(Get your token from: Home Assistant -> Profile -> Security -> Long-Lived Access Tokens)*

### Step 4: Configure Pi.dev (or Claude)
Ensure that the main project's `.mcp.json` or `.cursor/mcp.json` is configured to point to the `ha-mcp` executable.
For Pi.dev, the `.pi/settings.json` in this directory automatically loads the skills.

---

## 🛡️ Security Note

- The `.venv` and `node_modules` directories are **NOT** synced to GitHub. They are ignored locally.
- Your `.env` file containing the `HOMEASSISTANT_TOKEN` is also safely ignored by git and will never be uploaded to your repository.

---

## 🚀 Usage

Start your agent (e.g., `pi` or `claude`) in the root or in this directory.

Try asking:
- *"What is the state of my living room lights?"*
- *"Create a Home Assistant automation to turn off the lights when I leave home."*
- *"List all available entities in my Home Assistant."*
