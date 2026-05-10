# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **n8n** directory of the `pi.dev-projects` repository. It provides configuration and skills for building n8n workflows via Claude Code and Pi.dev.

**Purpose**: It combines three external components as git submodules to provide expert guidance on using n8n-mcp MCP tools effectively for building n8n workflows.

**Architecture**:
- **n8n-mcp MCP Server**: Provides data access (800+ nodes, validation, templates, workflow management). Linked as `n8n/n8n-mcp/` submodule.
- **Claude Skills**: Provides expert guidance on HOW to use MCP tools. Linked as `n8n/.pi/n8n-skills/` submodule.
- **pi-mcp-adapter**: MCP proxy for Pi.dev. Linked as `n8n/pi-mcp-adapter/` submodule.
- **Together**: Expert workflow builder with progressive disclosure.

## The 7 Skills (via n8n-skills)

The skills are located in `.pi/n8n-skills/skills/` and are made available to Pi.dev via `.pi/settings.json`.

1. **n8n Expression Syntax**: Teaches correct n8n expression syntax ({{}} patterns)
2. **n8n MCP Tools Expert** (HIGHEST PRIORITY): Teaches how to use n8n-mcp MCP tools effectively
3. **n8n Workflow Patterns**: Teaches proven workflow architectural patterns
4. **n8n Validation Expert**: Interprets validation errors and guides fixing
5. **n8n Node Configuration**: Operation-aware node configuration guidance
6. **n8n Code JavaScript**: Write JavaScript in n8n Code nodes
7. **n8n Code Python**: Write Python in n8n Code nodes

## Key MCP Tools

The n8n-mcp server provides these unified tools:

### Node Discovery
- `search_nodes` - Find nodes by keyword
- `get_node` - Unified node info with detail levels (minimal, standard, full) and modes (info, docs, search_properties, versions)

### Validation
- `validate_node` - Unified validation with modes (minimal, full) and profiles (runtime, ai-friendly, strict)
- `validate_workflow` - Complete workflow validation

### Workflow Management
- `n8n_create_workflow` - Create new workflows
- `n8n_update_partial_workflow` - Incremental updates (19 operation types including `patchNodeField`, `activateWorkflow`, `transferWorkflow`)
- `n8n_validate_workflow` - Validate by ID
- `n8n_autofix_workflow` - Auto-fix common issues
- `n8n_deploy_template` - Deploy template to n8n instance
- `n8n_workflow_versions` - Version history and rollback
- `n8n_test_workflow` - Test execution
- `n8n_executions` - Manage executions

### Data Tables
- `n8n_manage_datatable` - Manage data tables and rows (CRUD, filtering, dry-run)

### Credential Management
- `n8n_manage_credentials` - Full credential CRUD (list, get, create, update, delete) + schema discovery (`getSchema`)

### Security & Audit
- `n8n_audit_instance` - Security audit combining n8n built-in audit (5 risk categories) + custom deep scan (hardcoded secrets, unauthenticated webhooks, error handling, data retention)

### Templates
- `search_templates` - Multiple modes (keyword, by_nodes, by_task, by_metadata)
- `get_template` - Get template details

### Other Workflow Tools
- `n8n_list_workflows` - List workflows with filtering/pagination
- `n8n_get_workflow` - Get workflow details (full, structure, minimal modes)
- `n8n_delete_workflow` - Permanently delete workflows
- `n8n_update_full_workflow` - Full workflow replacement

### Guides
- `tools_documentation` - Meta-documentation for all tools
- `ai_agents_guide` - AI agent workflow guidance

## Important Patterns

### Most Common Tool Usage Pattern
```
search_nodes → get_node (18s avg between steps)
```

### Most Common Validation Pattern
```
n8n_update_partial_workflow → n8n_validate_workflow (7,841 occurrences)
Avg 23s thinking, 58s fixing
```

### Most Used Tool
```
n8n_update_partial_workflow (38,287 uses, 99.0% success)
Avg 56 seconds between edits
```

## Requirements

- n8n-mcp MCP server installed and configured (via `.mcp.json`)
- Claude Code, Claude.ai, or Claude API access
- Understanding of n8n workflow concepts

## Credits

Part of the n8n-mcp project. Conceived by Romuald Członkowski - [www.aiadvisors.pl/en](https://www.aiadvisors.pl/en)
