# Pi-MCP-Adapter Setup für n8n-mcp

Je hebt `pi-mcp-adapter` als submodule in dit project! Dit is de MCP support extension voor pi.dev.

## Quick Start

Jouw `.mcp.json` wordt automatisch gelezen. Gewoon `pi` openen:

```bash
pi
/mcp  # See n8n-mcp server status
```

---

## 🎯 Recommended Config

```json
{
  "settings": {
    "toolPrefix": "short",
    "idleTimeout": 10,
    "directTools": false
  },
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "N8N_API_URL": "https://your-instance.n8n.cloud",
        "N8N_API_KEY": "sk_prod_xxxxx"
      },
      "lifecycle": "lazy",
      "idleTimeout": 10
    }
  }
}
```

### Config Erklärung:

| Setting | Bedeutung |
|---------|-----------|
| `lifecycle: "lazy"` | Server connect nur wenn du MCP tools benutzt (sparent RAM) |
| `idleTimeout: 10` | Server disconnects nach 10 Minuten inactivity |
| `directTools: false` | Use proxy tool (saves 10k+ tokens in context) |
| `LOG_LEVEL: "error"` | Nur errors zeigen (keeps console clean) |

---

## 🔍 Usage in Pi

### Check Server Status
```
/mcp
```
→ Shows all MCP servers, connection status, tool count

### Search Tools
```
mcp({ search: "node" })
```
→ Find all tools matching "node" (fuzzy, case-insensitive)

### Describe a Tool
```
mcp({ describe: "get_node" })
```
→ Shows full tool details, parameters, description

### Call a Tool
```
mcp({ tool: "search_nodes", args: '{"nodeType": "slack"}' })
```
⚠️ Important: `args` is a JSON string, not an object!

### List All Server Tools
```
mcp({ server: "n8n-mcp" })
```

### Reconnect Server
```
/mcp reconnect n8n-mcp
```
→ Force reconnect (useful if connection drops)

### List All MCP Commands
```
/mcp
```
Then scroll through the interactive panel

---

## 💡 Pro Tips

### 1. Lazy Loading = Fast Startup
By default, n8n-mcp server only connects when you first use an MCP tool. This means `pi` starts instantly without waiting for server startup.

```bash
# Fast!
pi

# Later in conversation:
mcp({ search: "slack" })  # ← Server connects here for first time
```

### 2. Context Efficiency
Using `directTools: false` (proxy mode) costs ~200 tokens total instead of 10k+ for 39 individual tools.

**Trade-off:** You call `mcp({ tool: "..." })` instead of tools appearing directly in the tool list. But:
- Agent can still search/discover them
- Tools work exactly the same
- You save 10k+ tokens for your actual work

### 3. Tool Caching
Tool metadata is cached in `~/.pi/agent/mcp-cache.json`. This means:
- `mcp({ search: "..." })` works without server connection
- Fast tool discovery
- Server only connects when you actually call a tool

### 4. Idle Disconnect
After 10 minutes of inactivity, the server auto-disconnects:
- Frees up RAM
- Auto-reconnects on next tool call
- Total latency cost: ~1-2 seconds per reconnection

---

## 🛠️ Advanced: Direct Tools

If you want specific tools to show up directly (not via proxy), use `directTools`:

### Option A: All Tools Direct
```json
{
  "mcpServers": {
    "n8n-mcp": {
      ...
      "directTools": true
    }
  }
}
```
⚠️ Costs ~5k+ tokens (39 tools × 150-300 tokens each)

### Option B: Selected Tools Direct
```json
{
  "mcpServers": {
    "n8n-mcp": {
      ...
      "directTools": ["search_nodes", "get_node", "validate_node"]
    }
  }
}
```
✅ Only 3 tools = ~600 tokens. Much better!

### Option C: Exclude Specific Tools
```json
{
  "mcpServers": {
    "n8n-mcp": {
      ...
      "directTools": true,
      "excludeTools": ["n8n_test_workflow", "n8n_executions"]
    }
  }
}
```

After changing `directTools`, pi automatically reloads and refreshes tool registration. No restart needed!

---

## 🔐 Security

### API Key Management

**Option A: In .mcp.json (Shared Project)**
```json
{
  "mcpServers": {
    "n8n-mcp": {
      "env": {
        "N8N_API_URL": "${N8N_INSTANCE_URL}",
        "N8N_API_KEY": "${N8N_API_KEY}"
      }
    }
  }
}
```

Then set environment variables:
```bash
export N8N_INSTANCE_URL=https://your-instance.n8n.cloud
export N8N_API_KEY=sk_prod_xxxxx
pi
```

**Option B: User Global Config**
Use `~/.config/mcp/mcp.json` with direct values (git-ignored by default).

**Option C: .env File**
```bash
# .env.mcp
N8N_INSTANCE_URL=https://your-instance.n8n.cloud
N8N_API_KEY=sk_prod_xxxxx
```

Then in shell:
```bash
source .env.mcp && pi
```

---

## 📊 Performance Characteristics

| Scenario | Time | Notes |
|----------|------|-------|
| `pi` startup | <1s | Server not started |
| First MCP call | 2-3s | Server starts, connects |
| Subsequent calls | <500ms | Server hot |
| After 10m idle | 1-2s | Reconnects on next use |
| `mcp({ search: "..." })` | <100ms | Uses cache, no connection |

---

## 🐛 Debugging

### Enable Debug Mode
```bash
# In .mcp.json:
{
  "mcpServers": {
    "n8n-mcp": {
      "debug": true,
      ...
    }
  }
}
```

Then in pi session:
```
/mcp reconnect n8n-mcp
```

Server stderr will now appear in pi logs.

### Check Server Process
```bash
ps aux | grep n8n-mcp
```

### View MCP Cache
```bash
cat ~/.pi/agent/mcp-cache.json | jq '.["n8n-mcp"]' | head -50
```

### View Pi-MCP-Adapter Logs
```bash
cat ~/.pi/logs/mcp.log  # May vary by pi version
```

---

## ⚡ Lifecycle Modes (Advanced)

### `lazy` (Default, Recommended)
```json
"lifecycle": "lazy"
```
- Server starts on first tool call
- Disconnects after `idleTimeout` minutes
- Perfect for occasional use
- Saves memory

### `eager`
```json
"lifecycle": "eager"
```
- Server starts at `pi` startup
- Stays connected until next pi session
- Good for heavy MCP use
- Higher memory cost

### `keep-alive`
```json
"lifecycle": "keep-alive"
```
- Server always connected
- Auto-reconnects if dropped
- Best for production/long-running tasks
- Highest memory cost

For n8n-mcp, `lazy` (default) is usually best:
- You don't need constant n8n connection
- Saves memory between sessions
- MCP tools are instant when you need them

---

## 🎓 Learning Path

1. **Basic:** Just use `mcp({ tool: "..." })` in conversations
2. **Intermediate:** Use `mcp({ search: "..." })` to discover tools
3. **Advanced:** Set `directTools: ["search_nodes", "get_node"]` for your favorites
4. **Expert:** Combine with skills + agents for powerful workflows

---

## 📚 More Resources

- **Pi MCP Adapter README:** (linked as submodule)
  ```bash
  cat pi-mcp-adapter/README.md | less
  ```

- **n8n-mcp Tools:** Check tools via `/mcp` or `mcp({ search: "..." })`

- **n8n Skills:** Already active - they trigger automatically!

---

## ✅ Verification Checklist

- [ ] `.mcp.json` has valid JSON (run `jq . .mcp.json`)
- [ ] `N8N_API_URL` and `N8N_API_KEY` are filled in
- [ ] `pi-mcp-adapter` submodule is initialized (`git submodule status`)
- [ ] Can run: `pi` without errors
- [ ] `/mcp` shows `n8n-mcp` server
- [ ] `mcp({ search: "node" })` returns results
- [ ] Try: `mcp({ tool: "search_nodes", args: '{"nodeType": "slack"}' })`
- [ ] Skills trigger on keywords (e.g., "find me a Slack node")

Everything working? You're golden! 🚀

---

## 🆘 Common Issues

### Server shows "disconnected"
```bash
/mcp reconnect n8n-mcp
# Wait 2-3 seconds
/mcp  # Should show "connected"
```

### "command not found: n8n-mcp"
```bash
which npx  # Make sure npx is available
npx n8n-mcp --help  # Should show help
```

### API key errors (401/403)
- Check n8n URL is correct
- Check API key is correct
- Verify API key has adequate permissions (Settings → API)
- Try: `curl -H "X-N8N-API-KEY: YOUR_KEY" https://your-instance/api/v1/workflows`

### Skills not activating
- Use English keywords: "How do I write n8n expressions?" (not "Hoe schrijf ik...")
- Type: "find me a Slack node"
- or: "build me a webhook workflow"

Skills trigger on keywords, language-specific keys may not work.

---

Happy workflows! 🎉
