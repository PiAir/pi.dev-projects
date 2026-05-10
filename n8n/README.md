# 📑 n8n-skills + MCP Setup - Complete Guide Index

You have **pi-mcp-adapter** linked as a submodule! ✅ Both Claude Code and Pi.dev support MCP out of the box.

---

## 🚀 Start Here (Pick One)

### I want the fastest setup
→ **[QUICKSTART.md](QUICKSTART.md)** (5 minutes)

### I want full details
→ **[MCP_SETUP.md](MCP_SETUP.md)** (all options, both tools)

### I use Pi.dev and want pi-mcp-adapter details
→ **[PI_MCP_ADAPTER_GUIDE.md](PI_MCP_ADAPTER_GUIDE.md)** (advanced config, debugging)

### I need project context
→ **[CLAUDE.md](CLAUDE.md)** (skills overview, MCP tools reference)

---

## 📦 What You Have

This project uses git submodules to combine three powerful tools:

1. **`n8n-mcp`** (submodule): The actual MCP server providing data access (nodes, templates, validation).
2. **`n8n-skills`** (submodule in `.pi/n8n-skills`): 7 Expert n8n Skills that auto-activate based on user queries.
3. **`pi-mcp-adapter`** (submodule): An MCP proxy required for Pi.dev integration.

✅ **7 Expert n8n Skills** (auto-activating via `.pi/settings.json`)
- `n8n-expression-syntax` - Fix {{}} patterns
- `n8n-mcp-tools-expert` - ← Most important!
- `n8n-workflow-patterns` - Proven architectures
- `n8n-validation-expert` - Debug + autofix
- `n8n-node-configuration` - Operation-aware setup
- `n8n-code-javascript` - Code node JS patterns
- `n8n-code-python` - Code node Python patterns

✅ **39+ MCP Tools** (via `.mcp.json`)
- `search_nodes`, `get_node`, `validate_node`
- `n8n_create_workflow`, `n8n_update_partial_workflow`
- `n8n_manage_credentials`, `n8n_manage_datatable`
- ...and more

✅ **MCP Support in Both Tools**
- **Claude Code:** Native MCP support
- **Pi.dev:** Via the `pi-mcp-adapter` submodule

---

## ⚡ The Absolute Minimum

### Step 0: Initialize Submodules
If you just cloned this repository, ensure all submodules are loaded:
```bash
git submodule update --init --recursive
```

### Step 1: Fill in credentials
```bash
# Open .mcp.json and replace:
{{ N8N_INSTANCE_URL }}  →  https://your-instance.n8n.cloud
{{ N8N_API_KEY }}       →  sk_prod_xxxxxxxxxxxxx
```

### Step 2A: Claude Code
```bash
cd n8n
claude mcp add n8n-mcp --scope project
claude
```

### Step 2B: Pi.dev
The `.pi/settings.json` file automatically points Pi.dev to the skills inside the submodule.
```bash
pi
/mcp  # Verify n8n-mcp connects
```

### Step 3: Talk to it
```
"Find me a Slack node"
```
→ n8n-mcp-tools-expert skill activates! 🎉

---

## 📋 Files in This Directory

| File | Purpose | Read if... |
|------|---------|-----------|
| **QUICKSTART.md** | 5-minute setup | You want the fastest start |
| **MCP_SETUP.md** | Full setup guide | You want all details |
| **PI_MCP_ADAPTER_GUIDE.md** | Pi.dev specifics | You use pi.dev exclusively |
| **CLAUDE.md** | Project overview | You need context on skills/tools |
| **.mcp.json** | MCP config | You need to fill in credentials |
| **.env.mcp.example** | Environment template | You prefer .env management |
| **this file** | Navigation | You got lost! 🗺️ |

---

## 🎯 Common Workflows

### "Build me an n8n workflow from scratch"
1. Read → **QUICKSTART.md** (setup)
2. Open Claude Code or Pi.dev
3. Say → "Build me a webhook workflow for Slack notifications"
4. Skills + MCP tools work together automatically ✨

### "How do I fix n8n validation errors?"
1. Open your tool (Claude Code or Pi.dev)
2. Say → "Validate this workflow: `{ ... }`"
3. `n8n-validation-expert` skill activates
4. `validate_workflow` MCP tool checks config
5. Guidance + auto-fix options appear 🔧

### "Show me n8n expression examples"
1. Say → "Show me n8n expression examples for $json and $node"
2. `n8n-expression-syntax` skill activates
3. Get examples + common mistakes 📚

### "What n8n nodes are available?"
1. Say → "Find me nodes for sending emails"
2. `n8n-mcp-tools-expert` skill + `search_nodes` MCP tool
3. Get filtered list of relevant nodes 🔍

---

## 🔧 Setup Variations

### Scenario A: Team Project (Shared Config)
```bash
# Check in .mcp.json (shared via git)
# Store credentials in environment variables:
export N8N_INSTANCE_URL=https://...
export N8N_API_KEY=sk_prod_...
pi
```

### Scenario B: Local Development (Private Instance)
```bash
# .mcp.json with localhost
{
  "mcpServers": {
    "n8n-mcp": {
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "YOUR_LOCAL_KEY"
      }
    }
  }
}
```

### Scenario C: Multiple n8n Instances
```bash
# Make separate .mcp.json files:
# .mcp.production.json
# .mcp.staging.json
# .mcp.local.json

# Use environment variable to select:
cp .mcp.${ENV}.json .mcp.json
pi
```

---

## ⚠️ Important Notes

### Pi-mcp-adapter Benefits
✅ **Context Efficient:** ~200 tokens (vs 10k+ for all tools directly)
✅ **Lazy Loading:** Servers start only when you use them
✅ **Auto-Disconnect:** Idle servers disconnect after 10 minutes
✅ **Cached Metadata:** Search works without server connection

### Default Config
- `lifecycle: "lazy"` - Fast startup, connect on first use
- `idleTimeout: 10` - Disconnect after 10 minutes idle
- `directTools: false` - Use proxy tool (saves context)
- `LOG_LEVEL: "error"` - Quiet console

### When to Adjust
- **Slow network?** Set `idleTimeout: 1` to reconnect faster
- **Constant n8n use?** Set `lifecycle: "keep-alive"`
- **Want tools in tool list?** Set `directTools: ["search_nodes", "get_node"]`

---

## 🚨 Troubleshooting

### MCP server not connecting?
1. Check credentials in `.mcp.json`
2. Test manually:
   ```bash
   curl -H "X-N8N-API-KEY: YOUR_KEY" https://your-instance/api/v1/workflows
   ```
3. In Claude Code: `claude mcp list` → should show "connected"
4. In Pi.dev: `/mcp` → should show "connected"

### Skills not activating?
- Use English keywords (e.g., "Find me a Slack node" not "Vind me een Slack node")
- Try: "How do I write n8n expressions?"
- or: "Build me a webhook workflow"

### Performance sluggish?
- First MCP call takes 2-3s (server startup) — this is normal
- Subsequent calls <500ms
- If slow every time: check network to n8n instance

---

## 🎓 Learning Resources

### Official Docs
- **n8n:** https://docs.n8n.io
- **MCP:** https://modelcontextprotocol.io
- **Pi:** https://github.com/badlogic/pi-mono
- **pi-mcp-adapter:** https://github.com/badlogic/pi-mono/tree/main/packages/pi-mcp-adapter
- **n8n-mcp:** https://github.com/czlonkowski/n8n-mcp
- **n8n-skills:** https://github.com/czlonkowski/n8n-skills

### Skill Documentation
All 7 skills have full docs in `.pi/n8n-skills/skills/[skill-name]/`:
- README.md - Overview
- SKILL.md - Instructions
- Reference files (EXAMPLES, PATTERNS, etc.)

---

## ✅ Verification Checklist

Before you start:

- [ ] `.mcp.json` has valid JSON (`jq . .mcp.json` works)
- [ ] `N8N_INSTANCE_URL` is filled in (not `{{ ... }}`)
- [ ] `N8N_API_KEY` is filled in (not `{{ ... }}`)
- [ ] Submodules are initialized (`n8n-mcp`, `pi-mcp-adapter`, `.pi/n8n-skills` exist)

After setup:

- [ ] Claude Code: `claude mcp list` shows `n8n-mcp`
- [ ] Pi.dev: `pi` starts without errors
- [ ] `/mcp` panel shows n8n-mcp server
- [ ] `mcp({ search: "node" })` returns results (any MCP)
- [ ] Skills trigger on keywords ("find me a Slack node")

---

## 🚀 Next Steps

1. **Choose your tool** (Claude Code or Pi.dev or both)
2. **Read QUICKSTART.md** (5 minutes)
3. **Fill in .mcp.json** with your credentials
4. **Start using it** - talk naturally, skills + MCP tools handle the rest!

---

## 💬 Questions?

- **Setup issues?** Check MCP_SETUP.md or PI_MCP_ADAPTER_GUIDE.md
- **n8n questions?** Skills will activate automatically
- **MCP tool details?** Use `/mcp` panel or `mcp({ search: "..." })`

---

**You're all set!** Happy workflow building! 🎉

```
      ___  ___  _   _        __  __  ___   ___   __  __  ___
     / _ \|_ _|| \ | |      |  \/  |/ _ \ |_ _| |  \/  ||_ _|
    | | | || | |  \| |      | |\/| || | | | | |  | |\/| | | |
    | |_| || | | |\  |      | |  | || |_| | | |  | |  | | | |
     \___/|___||_| \_|      |_|  |_| \___/  |_|  |_|  |_| |_|

    🚀 n8n Workflow Expert + MCP Tools = Superpowers!
```
