# Hybrid Namespace + Retrieval for Tool Selection

## Problem

The voice orchestrator was suffering from LLM hallucinations when presented with 43 tools:
- gemma4 (small model) would hallucinate non-existent tools like `google:search`
- Example failure: "Open screenshot.png in pictures folder" → `Unknown tool: google:search`
- Root cause: 43 tools overwhelming the model's function-calling capability

## Solution

Implemented hybrid namespace + semantic retrieval approach:

1. **Namespace Organization**: Organized 43 tools into 10 semantic namespaces
2. **Semantic Retrieval**: Use sentence-transformers to find relevant namespaces
3. **Dynamic Filtering**: Show LLM only tools from top-3 relevant namespaces

## Architecture

### Namespace Structure

```python
namespaces = {
    "app": ["launch_application", "list_installed_applications"],
    "file": ["open_file", "open_url", "search_files"],
    "window": ["maximize_window_by_name", "minimize_window_by_name", ...],
    "workspace": ["list_workspaces", "activate_workspace"],
    "input": ["type_text_in_window", "press_key_combo", "mouse_click", ...],
    "volume": ["set_volume", "mute_volume", "unmute_volume"],
    "media": ["media_play", "media_pause", "media_next", ...],
    "settings": ["toggle_dark_mode", "toggle_wifi", "toggle_bluetooth", ...],
    "vision": ["describe_desktop", "pick_color", "get_monitors"],
    "system": ["set_enabled", "send_notification", "cleanup_screenshots"]
}
```

Each namespace has:
- **description**: Semantic description for retrieval
- **tools**: List of tool names in that namespace

### Retrieval Flow

```
User: "Open screenshot.png in pictures folder"
  ↓
1. Encode query with sentence-transformers
  ↓
2. Compute cosine similarity with namespace descriptions
  ↓
3. Select top-3 namespaces: [vision, window, file]
  ↓
4. Build filtered schema with only those 15 tools
  ↓
5. Pass to gemma4 LLM
  ↓
6. LLM sees 15 tools instead of 43 (65% reduction)
```

### Key Functions

**`retrieve_relevant_namespaces(user_input, top_k=3)`**
- Embeds user input
- Computes similarity with namespace descriptions
- Returns top-k most relevant namespaces

**`build_filtered_tool_schema(relevant_namespaces)`**
- Collects tool names from selected namespaces
- Filters full schema to only include those tools
- Returns filtered schema for LLM

## Performance

### Tool Count Reduction

| Query | Before | After | Reduction |
|-------|--------|-------|-----------|
| "open screenshot.png in pictures" | 43 | 15 | 65% |
| "maximize firefox" | 43 | 19 | 56% |
| "set volume to 50" | 43 | 14 | 67% |
| "play next track" | 43 | 16 | 63% |
| "turn on dark mode" | 43 | 11 | 74% |
| "find all PDFs" | 43 | 9 | 79% |

**Average**: 43 → 14 tools (67% reduction)

### Retrieval Accuracy

Test results from `test_hybrid_retrieval.py`:

```
✓ "set volume to 50" → volume (0.412), media (0.233), settings (0.084)
✓ "play next track" → media (0.480), volume (0.094), input (0.085)
✓ "turn on dark mode" → settings (0.600), volume (0.229), vision (0.160)
✓ "maximize firefox" → window (0.314), input (0.167), file (0.156)
✓ "switch to workspace 2" → workspace (0.553), window (0.243), input (0.153)
```

## Implementation

### Modified Files

1. **voice-driven-orchestrator-mcp-conversational.py**
   - Added `sentence-transformers` import
   - Added namespace definitions with descriptions
   - Added embedding model loading
   - Added `retrieve_relevant_namespaces()` function
   - Added `build_filtered_tool_schema()` function
   - Modified command execution to use filtered tools

### New Test

**test_hybrid_retrieval.py** - Standalone test for retrieval system
- Tests 10 different query types
- Shows ranked namespace relevance scores
- Displays filtered tool lists

## Testing

### Run Retrieval Test

```bash
python3 test_hybrid_retrieval.py
```

Expected output:
- Query: "open screenshot.png in pictures folder"
- Selected namespaces: [vision, window, file]
- Total tools shown: 15
- Tools include: open_file, search_files, open_url

### Integration Test

To test with the full orchestrator:

```bash
# Start orchestrator
./voice-driven-orchestrator-mcp-conversational.py

# Say: "Open screenshot.png in pictures folder"
# Expected: Should call open_file tool (not hallucinate google:search)
```

## Benefits

1. **Reduced Hallucinations**: LLM sees fewer tools, less confusion
2. **Better Performance**: 67% fewer tools to process
3. **Semantic Matching**: Queries matched to relevant tool groups
4. **Maintains Coverage**: Retrieval ensures right tools are available
5. **Scalability**: Can add more tools without overwhelming LLM

## Future Improvements

1. **Adaptive top_k**: Vary number of namespaces based on query complexity
2. **Query expansion**: Handle multi-intent queries ("maximize firefox and set volume to 50")
3. **Namespace fusion**: Merge overlapping namespaces (window + input)
4. **Fallback to full schema**: If retrieval fails, show all tools as safety net
5. **Retrieval caching**: Cache embeddings for common queries

## Commit

```bash
git log --oneline -1
# ae4be73 Implement hybrid namespace + retrieval for tool selection
```

Branch: `feature/hybrid-tool-selection`

## Credits

- sentence-transformers: all-MiniLM-L6-v2 model for embeddings
- Inspired by RAG (Retrieval-Augmented Generation) patterns
- Combines namespace organization + semantic search

---

**Status**: ✅ Implemented and tested  
**Test coverage**: Standalone retrieval test passing  
**Next step**: Real-world testing with voice orchestrator
