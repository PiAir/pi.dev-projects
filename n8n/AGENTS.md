# AGENTS.md - For pi.dev Users

This file provides guidance to pi.dev agents and workflows when working with this n8n-skills repository.

## Quick Start

### 1. Install Skills
```bash
# In pi:
skill-installer
# → Select "n8n-skills" from the curated list
# OR specify your repo path
```

### 2. Verify MCP Connection
```bash
# In pi:
/mcp
# Should show n8n-mcp server with status "connected"
```

### 3. Test Configuration
```bash
# In pi:
mcp({ search: "webhook" })
# Should return webhook node results
```

### 4. Configure API Access
See `MCP_SETUP.md` for:
- Setting up `.mcp.json` with correct `N8N_API_URL` and `N8N_API_KEY`
- How to obtain a regular n8n API key (not MCP instance-level key)
- Troubleshooting common configuration issues

## Project Structure

```text
n8n/
├── README.md              # Overview and setup guide
├── CLAUDE.md              # Claude Code specific guidance
├── AGENTS.md              # This file - pi.dev guidance
├── MCP_SETUP.md           # MCP configuration & troubleshooting
├── .mcp.json.example      # Template for MCP server configuration
├── .pi/
│   ├── settings.json      # Pi.dev skills configuration
│   └── n8n-skills/        # Submodule: 7 n8n-specific skills
├── n8n-mcp/               # Submodule: MCP server
└── pi-mcp-adapter/        # Submodule: Pi.dev MCP adapter
```

## The 7 n8n Skills

All skills auto-activate based on query context in pi.dev:

| # | Skill | Triggers | Use When |
|---|-------|----------|----------|
| 1 | **n8n-expression-syntax** | "{{}} pattern", "expression", "mapping data" | Writing n8n expressions or fixing expression errors |
| 2 | **n8n-mcp-tools-expert** | "find a node", "search workflows", "MCP" | Using MCP tools, discovering nodes, or workflow queries |
| 3 | **n8n-workflow-patterns** | "build a workflow", "webhook", "automate" | Designing workflow architecture or planning structure |
| 4 | **n8n-validation-expert** | "validation error", "workflow won't run" | Interpreting errors and fixing workflow issues |
| 5 | **n8n-node-configuration** | "configure", "set up node", "operation" | Setting node parameters and operation-specific fields |
| 6 | **n8n-code-javascript** | "JavaScript", "Code node", "custom logic" | Writing JavaScript in n8n Code nodes |
| 7 | **n8n-code-python** | "Python", "Code node with Python" | Writing Python in n8n Code nodes |

## Using Skills in pi.dev

### Direct Skill Usage
```bash
# Skills activate automatically based on query
"Find me a Slack node"          → n8n-mcp-tools-expert activates
"Build a webhook workflow"      → n8n-workflow-patterns activates
"Write a JavaScript Code node"  → n8n-code-javascript activates
```

### With Subagents
```bash
# Delegate complex workflow building
subagent({
  chain: [
    {agent: "planner", task: "Plan a {task}"},
    {agent: "builder", task: "Build based on {previous}"},
    {agent: "validator", task: "Validate {previous}"}
  ]
})
```

### Skill Cross-Integration
Skills work together for complete workflow development:

```
1. n8n-workflow-patterns      → Identify overall structure
2. n8n-mcp-tools-expert       → Find nodes by service/trigger
3. n8n-node-configuration     → Configure node operations
4. n8n-expression-syntax      → Map data between nodes
5. n8n-code-javascript/python → Write custom logic
6. n8n-validation-expert      → Fix validation errors
```

## MCP Tools Available

All n8n-mcp tools are accessible via `mcp()`:

### Node Discovery
```bash
mcp({ search: "slack" })
mcp({ tool: "n8n_mcp_get_node", args: '{"nodeType": "nodes-base.slack"}' })
```

### Workflow Management
```bash
mcp({ tool: "n8n_mcp_n8n_list_workflows", args: "{}" })
mcp({ tool: "n8n_mcp_n8n_get_workflow", args: '{"id": "WORKFLOW_ID"}' })
```

### Validation
```bash
mcp({ tool: "n8n_mcp_validate_node", args: '{"nodeType": "nodes-base.webhook", "config": {}}' })
mcp({ tool: "n8n_mcp_n8n_validate_workflow", args: '{"id": "WORKFLOW_ID"}' })
```

**Full tool reference:** See `MCP_SETUP.md` or run `mcp({ search: "workflow" })` to discover tools.

## Building n8n Workflows in pi.dev

### Workflow: Get List of Active Workflows
```bash
# Query that activates n8n-mcp-tools-expert automatically:
"Get all active workflows from n8n"

# Manually:
mcp({ tool: "n8n_mcp_n8n_list_workflows", args: '{"active": true}' })
```

### Workflow: Build a New Webhook Workflow
```bash
# Query that triggers auto-activation:
"Build a webhook workflow that receives data and sends it to Slack"

# Skills activate in order:
# 1. n8n-workflow-patterns   → Suggests webhook + Slack structure
# 2. n8n-mcp-tools-expert    → Finds webhook & Slack nodes
# 3. n8n-node-configuration  → Shows how to configure each
# 4. n8n-expression-syntax   → Maps data correctly
```

### Workflow: Fix Validation Errors
```bash
# Query structure:
"I have a workflow with validation errors. Fix: {error_message}"

# Activates n8n-validation-expert to:
# 1. Interpret the error
# 2. Suggest fixes
# 3. Apply remediation via n8n_update_partial_workflow
```

## Configuration

### Environment Setup
1. **Get your API credentials:**
   - n8n instance URL (e.g., `https://your-instance.n8n.cloud`)
   - Regular n8n API key (from Settings → n8n API)
   - **NOT** the instance-level MCP key

2. **Create/update `.mcp.json`:**
   See `MCP_SETUP.md` for template and detailed instructions

3. **Verify connection:**
   ```bash
   /mcp
   /mcp status
   ```

### Key Configuration Points
- ✅ Use `/api/v1` as API endpoint suffix
- ❌ Do NOT use `/mcp-server/http` (legacy, buggy)
- ✅ API key should be from regular n8n API, not MCP instance-level
- ✅ Set `LOG_LEVEL=error` for cleaner output
- ❌ Never commit `.mcp.json` with real credentials to git

## Troubleshooting

### "n8n_list_workflows returns 'response is not an object'"
**Cause:** N8N_API_URL points to wrong endpoint (likely `/mcp-server/http`)

**Fix:** Ensure `.mcp.json` uses:
```
N8N_API_URL: "https://your-instance/api/v1"  ✅
NOT: "https://your-instance/mcp-server/http" ❌
```

See `MCP_SETUP.md` issue #594 for details.

### "MCP tools don't respond"
**Steps:**
1. Check `/mcp status` in pi
2. Run `/mcp reconnect` to refresh
3. Verify `.mcp.json` exists and is valid JSON
4. Check `N8N_API_KEY` and `N8N_API_URL` are set
5. Test: `mcp({ search: "webhook" })`

### "API key authentication fails"
**Verify:**
- You're using a regular n8n API key, not instance-level MCP key
- API key is from Settings → n8n API (not Settings → Instance-level MCP)
- Key has not expired
- No extra whitespace in `.mcp.json`

## Best Practices

### Do
- ✅ Use skills to guide workflow design before building
- ✅ Call n8n_validate_workflow after updates
- ✅ Use n8n-mcp-tools-expert before attempting manual tool calls
- ✅ Follow the cross-skill integration order (pattern → tools → config → expression → code → validate)
- ✅ Use subagent chains for complex multi-step workflows
- ✅ Check MCP_SETUP.md before reporting issues

### Don't
- ❌ Hardcode API keys in conversation history or notes
- ❌ Commit `.mcp.json` to git with credentials
- ❌ Use `/mcp-server/http` endpoint
- ❌ Try to use instance-level MCP key for API authentication
- ❌ Skip validation before deploying workflows

## Performance Tips

### Common Tool Patterns
```
search_nodes → get_node        (18s avg between steps)
validate_node → fix            (23s thinking, 58s fixing)
update_workflow → validate     (56s avg between edits)
```

### Efficiency
- Use `detail: "standard"` for get_node (not "full" unless needed)
- Validate early and often
- Build workflows iteratively (small edits, not one massive update)
- Use smart parameters (`branch="true"`, `case=0`) for clarity

## Related Documentation

- **README.md** - Project overview and setup
- **CLAUDE.md** - For Claude Code (claude.ai/code) users
- **MCP_SETUP.md** - Detailed MCP configuration and troubleshooting
- **Skill Files** - Each skill has detailed documentation in `.pi/n8n-skills/skills/*/SKILL.md`

## Support & Contributing

### For Issues
1. Check `MCP_SETUP.md` troubleshooting section
2. Review skill documentation in `.pi/n8n-skills/skills/*/SKILL.md`
3. See related GitHub issues (referenced in skills)

### For Contributions
- Add new skills following the structure in `n8n-skills/skills/`
- Update AGENTS.md if adding pi.dev specific features
- Test skills with both Claude Code and pi.dev

## Credits

Part of the **n8n-skills** project - a collection of Claude Code skills for building n8n workflows with MCP.

- **Repository**: https://github.com/czlonkowski/n8n-skills
- **MCP Server**: https://github.com/czlonkowski/n8n-mcp
- **n8n Docs**: https://docs.n8n.io

## License

MIT License - See LICENSE file for details.
