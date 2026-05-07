# llama-server Migration Summary

## ✅ What We Accomplished

### Step 1: Downloaded & Converted Gemma 4 E4B
- Downloaded official Gemma 4 E4B from Hugging Face
- Converted to GGUF format using llama.cpp tools
- Quantized to Q4_K_M (5GB, optimized for GPU)
- Model location: `~/models/gemma4-e4b-q4km.gguf`

### Step 2: Started llama-server with Vulkan GPU
- Running on: `http://127.0.0.1:8081`
- GPU acceleration: Intel Arc (Vulkan)
- All 99 layers offloaded to GPU
- OpenAI-compatible API

### Step 3: Updated Orchestrator
- Created: `voice-driven-orchestrator-mcp-llama-server.py`
- Replaced `ollama.chat()` with `call_llama_server()` HTTP calls
- Kept Ollama fallback for vision tasks (images not yet supported in llama-server)
- Updated all 4 inference locations:
  1. Command mode (tool calling) ✅
  2. Intent classifier ✅
  3. Conversation mode ✅
  4. Vision mode (still uses Ollama) ⚠️

## 📊 Performance Comparison

| Mode | Before (Ollama CPU) | After (llama-server GPU) | Speedup |
|------|---------------------|--------------------------|---------|
| Prompt | ~8 t/s | 57-164 t/s | **7-20×** |
| Generation | ~13 t/s | 8-9 t/s | 0.6× |
| **Total** | **~22s** | **~10-12s (estimated)** | **~2×** |

## 🚀 How to Use

### Start llama-server
```bash
cd ~/anthony
./start_llama_server.sh
```

Or manually:
```bash
~/llama.cpp/build/bin/llama-server \
    --model ~/models/gemma4-e4b-q4km.gguf \
    --ctx-size 4096 \
    --n-gpu-layers 99 \
    --device Vulkan0 \
    --port 8081 \
    --host 127.0.0.1 \
    --threads 6 \
    --parallel 1 \
    --cont-batching \
    --flash-attn auto
```

### Run Updated Orchestrator
```bash
cd ~/anthony
./voice-driven-orchestrator-mcp-llama-server.py
```

### Stop llama-server
```bash
pkill llama-server
```

## 🔧 Key Changes in Code

### Old (Ollama):
```python
import ollama

response = ollama.chat(
    model='gemma4:e4b',
    messages=[...],
    tools=[...],
    options={'temperature': 0.0, 'num_predict': 200}
)
```

### New (llama-server):
```python
import requests

response = call_llama_server(
    messages=[...],
    tools=[...],
    temperature=0.0,
    max_tokens=200
)
```

## 📁 Files Created

| File | Purpose | Size |
|------|---------|------|
| `~/models/gemma4-e4b-q4km.gguf` | Converted model (GPU-optimized) | 5GB |
| `~/models/gemma4-e4b-fp16.gguf` | Full precision (can delete) | 15GB |
| `voice-driven-orchestrator-mcp-llama-server.py` | Updated orchestrator | - |
| `start_llama_server.sh` | Server startup script | - |
| `download_and_convert_gemma4.sh` | Model conversion script | - |

## ⚠️ Known Limitations

1. **Vision tasks still use Ollama** - llama-server doesn't support image inputs yet
   - Vision commands (describe_desktop) fall back to Ollama CPU
   - This is fine for now since vision is rarely used

2. **llama-server must be running** - The orchestrator will fail if server is down
   - Check health: `curl http://127.0.0.1:8081/health`
   - Should return: `{"status":"ok"}`

3. **Port 8081 must be free** - If blocked, change port in both:
   - `start_llama_server.sh` (--port flag)
   - `voice-driven-orchestrator-mcp-llama-server.py` (LLAMA_SERVER_URL)

## 🧪 Testing

Test the server:
```bash
curl -s http://127.0.0.1:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Say hello"}],
    "temperature": 0.1,
    "max_tokens": 20
  }'
```

## 🎯 Next Steps (Step 3)

Now ready to test real-world performance with the voice orchestrator!

Expected improvements:
- Command mode: 22s → ~10-12s (**~2× faster**) 🚀
- Intent classification: Much faster
- Conversation: Faster responses
- Vision: Same (still uses Ollama)

## 🔄 Rollback Plan

If issues arise, switch back to original:
```bash
# Stop llama-server
pkill llama-server

# Use original orchestrator
./voice-driven-orchestrator-mcp-consolidated.py
```

## 💾 Disk Space

Current usage:
- Model (Q4_K_M): 5GB
- Model (FP16): 15GB (can delete to save space)
- HF download: ~16GB (can delete after conversion)

Cleanup to save 31GB:
```bash
rm ~/models/gemma4-e4b-fp16.gguf
rm -rf ~/models/gemma-4-E4B-it-hf/
```

## 🏁 Summary

✅ **Successfully migrated to llama-server with Vulkan GPU acceleration!**

- llama-server running on port 8081
- Orchestrator updated to use HTTP API
- Expected ~2× speedup in command mode
- Ready for real-world testing!
