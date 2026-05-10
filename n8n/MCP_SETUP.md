# MCP Setup Guide voor Claude Code & Pi.dev

## ⚠️ Security First

**NEVER commit credentials to git!** This project includes:
- `.gitignore` - excludes `.mcp.json` and `.env.mcp` (ignored automatically)
- `.mcp.json.example` - template for GitHub (use as reference)
- `.env.mcp.example` - environment template

## Prerequisites

You need:
- n8n instance URL (e.g., `https://your-instance.n8n.cloud`)
- n8n API key (from Settings → n8n API → API Keys)
  - **NOT** the instance-level MCP key
  - Use a regular n8n API key
- `.mcp.json` file (local only, never commit)

## 📋 Setup Your Local Configuration

**Use `.mcp.json.example` as your template:**

```bash
# Copy template to local (ignored by git)
cp .mcp.json.example .mcp.json

# Edit with your credentials
# Replace:
#   https://your-instance.n8n.cloud/api/v1  → Your actual instance URL
#   sk_prod_YOUR_API_KEY_HERE               → Your actual API key

vim .mcp.json  # or your editor
```

**That's it!** This is all you need. Both Claude Code and pi.dev will auto-detect `.mcp.json`.

### Important: API URL Format

✅ **CORRECT:**
```
https://your-instance.n8n.cloud/api/v1
https://192.168.1.100/api/v1
```

❌ **WRONG (will fail):**
```
https://your-instance.n8n.cloud/mcp-server/http  ← Legacy, buggy
https://your-instance.n8n.cloud                    ← Missing /api/v1
```

See [Issue #594](https://github.com/czlonkowski/n8n-mcp/issues/594) for details.

---

## 🔌 CLAUDE CODE Setup

### Use Your Local `.mcp.json`

```bash
# From this project directory:
claude mcp add n8n-mcp --scope project
```

Claude will detect and use the local `.mcp.json` automatically.

**Verify:**
```bash
claude mcp list
claude mcp get n8n-mcp
```

**Troubleshooting:**
- If Claude doesn't detect `.mcp.json`, restart Claude Desktop
- Check that `.mcp.json` contains valid JSON (no trailing commas)
- Verify credentials are correct: `N8N_API_URL` and `N8N_API_KEY`

---

## 🔌 PI.DEV Setup

✅ **pi-mcp-adapter is installed!** pi.dev supports MCP out of the box.

Your local `.mcp.json` will be auto-detected when you run pi.

```bash
# First: Set up credentials in .mcp.json (see Step 1 above)
# Then:
pi

# In pi:
/mcp  # Check n8n-mcp server status
```

**How it works:**
- pi-mcp-adapter auto-detects your `.mcp.json`
- MCP servers start lazy (only when needed)
- Tools accessible via `mcp()` proxy (~200 tokens vs 10k+ for all tools)
- All skills activate automatically

**Verify connection:**
```bash
/mcp status
mcp({ search: "webhook" })  # Should return results
```

---

## 🛠️ Setup Preference Order

### Claude Code:
```
1. Set up .mcp.json with your credentials (Step 1)
2. Run: claude mcp add n8n-mcp --scope project
3. Restart Claude Desktop
4. Skills activate automatically
```

### Pi.dev:
```
1. Set up .mcp.json with your credentials (Step 1)
2. Run: pi
3. Verify: /mcp status
4. Skills activate automatically
```

**Both work now!** 🎉 pi-mcp-adapter handles MCP setup for pi.dev automatically

---

## ✅ Validation Checklist

### Claude Code:
- [ ] `.mcp.json` contains real `N8N_API_URL` and `N8N_API_KEY`
- [ ] `.mcp.json` is in `.gitignore` (never committed)
- [ ] `claude mcp list` shows `n8n-mcp` as "connected"
- [ ] Run: `claude mcp test` or test a skill manually
- [ ] Skills activate automatically

### Pi.dev:
- [ ] `.mcp.json` exists locally (copied from `.mcp.json.example`)
- [ ] `.mcp.json` contains real credentials
- [ ] `.mcp.json` is in `.gitignore`
- [ ] Run: `/mcp status` in pi
- [ ] Run: `mcp({ search: "webhook" })` returns results
- [ ] Skills activate automatically

### General Security:
- [ ] `.gitignore` is committed (protects credentials)
- [ ] `.mcp.json` is **NOT** in git history
- [ ] `.env.mcp` is **NOT** in git history
- [ ] Never share your `.mcp.json` or API keys
- [ ] API key is from Settings → n8n API (not instance-level MCP)

---

## 📚 Related Files

- `.mcp.json.example` ← Template (safe to share)
- `.env.mcp.example` ← Environment template (safe to share)
- `.gitignore` ← Protects credentials from git
- `.mcp.json` ← Your config (LOCAL, never commit)
- `.env.mcp` ← Your env vars (LOCAL, never commit)
- `CLAUDE.md` ← Claude Code user guide
- `AGENTS.md` ← pi.dev user guide
- `.pi/skills/` ← 7 n8n skills
- `n8n-mcp/` ← MCP server source

---

## 🚀 Quick Start Commands

```bash
# Clone and setup
git clone <repo>
cd n8n-skills
cp .mcp.json.example .mcp.json
# Edit .mcp.json with your credentials

# For Claude Code
claude mcp add n8n-mcp --scope project

# For pi.dev
pi
# Then in pi: /mcp status

# Test connection
mcp({ search: "webhook" })
```

---

## 🐛 Troubleshooting

### "response is not an object" error
**Cause:** N8N_API_URL uses wrong endpoint

**Fix:** Verify `.mcp.json` has:
```json
"N8N_API_URL": "https://your-instance/api/v1"
```
Not: `/mcp-server/http` (legacy, buggy)

See [GitHub Issue #594](https://github.com/czlonkowski/n8n-mcp/issues/594)

### MCP tools don't respond
**Steps:**
1. Check: `/mcp status` (pi.dev) or `claude mcp list` (Claude Code)
2. Run: `/mcp reconnect` (pi.dev)
3. Verify `.mcp.json` exists and contains valid JSON
4. Check `N8N_API_KEY` and `N8N_API_URL`
5. Test: `mcp({ search: "webhook" })`

### "401 Unauthorized" or authentication fails
**Verify:**
- Using a regular n8n API key (from Settings → n8n API)
- NOT the instance-level MCP key
- Key hasn't expired
- No extra whitespace in `.mcp.json`

### `.gitignore` not working
**If credentials were already committed:**
```bash
# Remove from git history
git rm --cached .mcp.json
git rm --cached .env.mcp
git commit -m "Remove credentials from git history"

# Then in GitHub, regenerate your API key (safety!)
```
