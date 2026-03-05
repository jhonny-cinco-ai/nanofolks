# Nanofolks Token Optimizer (NTO) - User Guide

## What is NTO?

**NTO (Nanofolks Token Optimizer)** automatically reduces token consumption by 50-90% on common operations. It works transparently in the background, compressing tool outputs before they reach the LLM context.

## How It Works

NTO integrates directly into nanofolks tools and automatically compresses outputs:

```
Agent calls tool → Tool executes → NTO compresses → Agent receives compressed output
```

**No action required from agents** - compression happens automatically!

## Token Savings by Tool

| Tool Type | Savings | Example |
|-----------|---------|---------|
| **Web Search** | 60-80% | 10 results → 5 results, truncated snippets |
| **Web Fetch** | 70-90% | Full HTML → Clean text, truncated |
| **Bot Responses** | 50-70% | Long reports → Compressed summaries |
| **Memory Search** | 70-85% | 20 results → Top 5, truncated content |

## Configuration

### Enable/Disable NTO

Edit your `~/.nanofolks/config.json`:

```json
{
  "tools": {
    "nto": {
      "enabled": true,
      "defaultLevel": "minimal"
    }
  }
}
```

### Compression Levels

- **`none`** - No compression (use for debugging)
- **`minimal`** - Light compression (default) - Truncate long text, limit results
- **`aggressive`** - Heavy compression - Maximum truncation, minimal results

### Per-Tool Settings

```json
{
  "tools": {
    "nto": {
      "enabled": true,
      "defaultLevel": "minimal",
      "webMaxResults": 10,
      "webMaxSnippetLength": 200,
      "botMaxResponseTokens": 500,
      "memoryTopK": 5
    }
  }
}
```

## Viewing Statistics

Check your token savings anytime:

```bash
nanofolks nto-stats
```

Example output:
```
📊 NTO (Nanofolks Token Optimizer) Statistics

Token Savings Summary
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Metric            ┃ Value    ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ Total Operations  │ 42       │
│ Original Tokens   │ 45,230   │
│ Compressed Tokens │ 12,890   │
│ Tokens Saved      │ 32,340   │
│ Average Savings   │ 71.5%    │
└───────────────────┴──────────┘
```

## Benefits

- **💰 Cost Reduction** - 50-90% fewer tokens = lower API costs
- **⚡ Faster Responses** - Smaller context = faster LLM processing
- **🔧 Zero Configuration** - Works out of the box
- **🎛️ Flexible** - Configure per-deployment, per-tool
- **🔍 Transparent** - View stats anytime, optional bypass

## Examples

### Before NTO

```
User: "Research AI developments"

Web search returns:
- 10 full results with long snippets
- Total: 3,500 tokens

Bot response:
- Full analysis report
- Total: 2,800 tokens

Memory search:
- 20 memory entries
- Total: 1,500 tokens

Total: 7,800 tokens
```

### After NTO

```
User: "Research AI developments"

Web search returns:
- 5 compressed results, truncated snippets
- Total: 800 tokens (77% savings)

Bot response:
- Compressed summary
- Total: 900 tokens (68% savings)

Memory search:
- Top 5 results, truncated content
- Total: 400 tokens (73% savings)

Total: 2,100 tokens (73% overall savings)
```

## Troubleshooting

### Getting "No NTO operations recorded yet"?

NTO only tracks operations when tools are actually used. Start a conversation and use tools like `web_search`, `invoke`, or `search_memory` to see statistics.

### Want to see full (uncompressed) output?

Most tools support `skip_compression=True` parameter (advanced use):

```python
# In REPL or custom code
results = web.search("query", skip_compression=True)
```

### Statistics not updating?

Statistics are stored in-memory during the session. They reset when nanofolks restarts. This is by design for simplicity.

## Advanced: Programmatic Access

Access NTO stats programmatically:

```python
from nanofolks.agent.tools.nto import create_nto_wrapper

nto = create_nto_wrapper()
stats = nto.get_stats()

print(f"Saved {stats['total_saved']} tokens!")
```

## Migration from RTK

If you were using RTK (Rust Token Killer) before:

- ✅ NTO replaces RTK for nanofolks-specific tools
- ✅ NTO is native Python (no binary dependency)
- ✅ NTO covers web, bot, and memory tools (RTK focused on CLI)
- ✅ NTO has better integration with nanofolks architecture

## Support

For issues or questions:
- Check `nanofolks nto-stats` for current savings
- Review configuration in `~/.nanofolks/config.json`
- File an issue on GitHub

---

**Start saving tokens today!** NTO is enabled by default and works automatically. Check your stats with `nanofolks nto-stats`.
