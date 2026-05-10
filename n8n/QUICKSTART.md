# 🚀 n8n-skills + n8n-mcp Quick Start

**TL;DR:** Vul je n8n API-gegevens in, run één commando (Claude Code) of gewoon `pi` (Pi.dev), en je hebt expert n8n workflow guidance met MCP tools.

---

## ⚡ 5 Minute Setup

### 1. Verzamel je n8n credentials
```
n8n URL:    https://your-instance.n8n.cloud  (OF http://localhost:5678)
API Key:    sk_prod_xxxxx (van n8n → Settings → API)
```

### 2. Configureer .mcp.json
```bash
# Open .mcp.json in editor en vervang:
# {{ N8N_INSTANCE_URL }}  → je n8n URL
# {{ N8N_API_KEY }}       → je API key
```

### 3A. Claude Code ✅
```bash
cd C:\Temp\Projecten\n8n
claude mcp add n8n-mcp --scope project
claude  # Start
```

### 3B. Pi.dev ✅ (je hebt pi-mcp-adapter!)
```bash
pi  # Start Pi
/mcp  # See n8n-mcp status
```

### 4. Done! 🎉
Type in either: "Vind me een Slack node"
→ n8n-mcp-tools-expert skill activates automatically!

---

## 📚 Je hebt nu:

✅ **7 Expert Skills** (auto-activating):
- `n8n-expression-syntax` - {{}} patterns
- `n8n-mcp-tools-expert` - ← Meest waardevol!
- `n8n-workflow-patterns` - Architecture
- `n8n-validation-expert` - Fix errors
- `n8n-node-configuration` - Setup guidance
- `n8n-code-javascript` - JS in Code nodes
- `n8n-code-python` - Python in Code nodes

✅ **39+ MCP Tools** (via proxy of direct):
- `search_nodes` - Find nodes
- `get_node` - Node details
- `validate_node` - Check config
- `n8n_update_partial_workflow` - Edit workflows
- `n8n_list_workflows` - List workflows
- `n8n_manage_credentials` - Credential CRUD
- ...en meer

---

## 🎯 Common Tasks

### "Build me a webhook workflow"
→ Auto-uses `n8n-workflow-patterns` skill
→ You get proven architecture + MCP tools
→ `search_nodes` → `get_node` → `n8n_create_workflow`

### "Fix this validation error"
→ Auto-uses `n8n-validation-expert` skill
→ Shows error patterns + auto-fix options
→ `validate_workflow` → `n8n_autofix_workflow`

### "How do I write n8n expressions?"
→ Auto-uses `n8n-expression-syntax` skill
→ Covers {{}} patterns, $json, $node, gotchas

---

## 🔌 MCP Basics

### In Claude Code:
```bash
/mcp  # See status and tools
```

### In Pi.dev (pi-mcp-adapter):
```
/mcp              # See status and tools
/mcp tools        # List all tools
mcp({ })          # Check server status
mcp({ search: "node" })  # Find tools
mcp({ tool: "tool_name", args: '{"param": "value"}' })  # Call tool
```

---

## 📁 Directory Structure

```
C:\Temp\Projecten\n8n\
├── .mcp.json                 ← MCP configuration (edit this!)
├── .env.mcp.example          ← Optional: env template
├── CLAUDE.md                 ← Project guide
├── MCP_SETUP.md              ← Detailed setup
├── QUICKSTART.md             ← This file
├── .pi/
│   └── skills/               ← 7 n8n expert skills
│       ├── n8n-code-javascript/
│       ├── n8n-code-python/
│       ├── n8n-expression-syntax/
│       ├── n8n-mcp-tools-expert/
│       ├── n8n-node-configuration/
│       ├── n8n-validation-expert/
│       └── n8n-workflow-patterns/
└── n8n-mcp/                  ← MCP server source
```

---

## 🔧 Troubleshooting

### MCP server niet connect?

**Check 1: n8n API credentials**
```bash
curl -H "X-N8N-API-KEY: YOUR_KEY" https://your-instance/api/v1/workflows
# Haust 200 OK, not 401/403
```

**Check 2: .mcp.json syntax**
```bash
cat .mcp.json | jq .  # Should be valid JSON
```

**Check 3: Claude Code MCP status**
```bash
claude mcp list
claude mcp get n8n-mcp
```

**Check 4: Pi.dev pi-mcp-adapter**
```bash
npm list -g pi-mcp-adapter  # Should be installed
```

In pi:
```
/mcp reconnect n8n-mcp
```

### Skills activeren niet?
- Type in Engels: "How do I write JavaScript in n8n?"
- oder: "Find me a Slack node"
- eller: "Build me a webhook workflow"

Skills triggeren op keywords, niet op exact phrases!

---

## 📖 Next Steps

1. **Read CLAUDE.md** - Project overview (7 skills explained)
2. **Read MCP_SETUP.md** - Detailed setup for both tools
3. **Try it:**
   - Claude Code: `claude` → "Create a webhook workflow for Slack"
   - Pi.dev: `pi` → "Create a webhook workflow for Slack"
4. **Explore:** 
   - Claude Code: `/help` voor alle commands
   - Pi.dev: `/help` en `/mcp` voor MCP commands

---

## ❓ Questions?

- **GitHub:** https://github.com/czlonkowski/n8n-skills
- **n8n Docs:** https://docs.n8n.io
- **MCP Docs:** https://modelcontextprotocol.io
- **pi-mcp-adapter:** https://github.com/badlogic/pi-mono/tree/main/packages/pi-mcp-adapter

---

## 🎯 What's Different?

### Claude Code
- Native MCP support
- Tools show in tool list
- Full integration

### Pi.dev (with pi-mcp-adapter)
- MCP tools via proxy tool (saves context!)
- Servers lazy-load (only when you use them)
- Tool metadata cached (search works offline)
- Same capabilities, better token efficiency

**Both are great. Pick your favorite!** ✨

Happy workflow building! 🚀
