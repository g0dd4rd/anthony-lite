#!/usr/bin/env python3
"""
Test llama.cpp performance with Vulkan GPU acceleration vs Ollama CPU
"""

import subprocess
import json
import time
import tempfile

# Test prompt - same as what orchestrator uses for tool calling
test_messages = [
    {
        "role": "system",
        "content": "You are a silent system orchestrator. Your ONLY job is to execute tool calls based on user intent."
    },
    {
        "role": "user",
        "content": "Take a screenshot of text editor window."
    }
]

# Simple tool schema (2 tools like filtered RAG)
test_tools = [
    {
        "type": "function",
        "function": {
            "name": "window_control",
            "description": "Unified window management: screenshot, focus, close, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "screenshot | focus | close"},
                    "window_name": {"type": "string", "description": "App name", "default": ""}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "vision_control",
            "description": "Screen analysis and screenshots",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "description": "screenshot | describe"}
                },
                "required": ["action"]
            }
        }
    }
]

MODEL_BLOB = "/home/jprajzne/models/gemma4-e4b-q4km.gguf"
LLAMA_CLI = "/home/jprajzne/llama.cpp/build/bin/llama-cli"

def test_ollama_cpu():
    """Test current Ollama CPU performance"""
    import ollama

    print("\n" + "="*60)
    print("TEST 1: Ollama (CPU) - Current Setup")
    print("="*60)

    start = time.time()
    response = ollama.chat(
        model='gemma4:e4b',
        messages=test_messages,
        tools=test_tools,
        options={
            'temperature': 0.0,
            'top_p': 0.1,
            'num_predict': 200
        }
    )
    elapsed = time.time() - start

    print(f"⏱️  Time: {elapsed:.2f}s")
    print(f"📊 Tokens: {response.get('eval_count', 'N/A')}")
    if response['message'].get('tool_calls'):
        tool = response['message']['tool_calls'][0]
        print(f"🔧 Tool: {tool['function']['name']}({tool['function']['arguments']})")

    return elapsed


def test_llama_cpp_cpu():
    """Test llama.cpp with CPU only (baseline)"""
    print("\n" + "="*60)
    print("TEST 2: llama.cpp (CPU) - Baseline")
    print("="*60)

    # Build prompt for llama.cpp (Gemma4 format)
    # Gemma4 uses specific tool format in prompt
    prompt = f"{test_messages[0]['content']}\n\nUser: {test_messages[1]['content']}\n\nAvailable tools:\n{json.dumps(test_tools, indent=2)}"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        start = time.time()
        result = subprocess.run([
            LLAMA_CLI,
            '--model', MODEL_BLOB,
            '--file', prompt_file,
            '--ctx-size', '4096',
            '--n-predict', '200',
            '--temp', '0.0',
            '--top-p', '0.1',
            '--gpu-layers', '0',  # CPU only
            '--log-disable',
            '--no-display-prompt'
        ], capture_output=True, text=True, timeout=120)
        elapsed = time.time() - start

        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"📊 Output length: {len(result.stdout)} chars")
        if result.returncode == 0:
            print(f"✅ Success")
            # Show last 200 chars of output
            print(f"📄 Output: ...{result.stdout[-200:]}")
        else:
            print(f"❌ Failed: {result.stderr[:200]}")

        return elapsed
    except subprocess.TimeoutExpired:
        print("❌ Timeout after 120s")
        return 120.0
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_llama_cpp_vulkan():
    """Test llama.cpp with Vulkan GPU acceleration"""
    print("\n" + "="*60)
    print("TEST 3: llama.cpp (Vulkan GPU) - FAST MODE 🚀")
    print("="*60)

    # Build prompt
    prompt = f"{test_messages[0]['content']}\n\nUser: {test_messages[1]['content']}\n\nAvailable tools:\n{json.dumps(test_tools, indent=2)}"

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        start = time.time()
        result = subprocess.run([
            LLAMA_CLI,
            '--model', MODEL_BLOB,
            '--file', prompt_file,
            '--ctx-size', '4096',
            '--n-predict', '200',
            '--temp', '0.0',
            '--top-p', '0.1',
            '--gpu-layers', 'all',  # Full GPU offload
            '--device', 'Vulkan0',   # Intel Arc GPU
            '--log-disable',
            '--no-display-prompt'
        ], capture_output=True, text=True, timeout=120)
        elapsed = time.time() - start

        print(f"⏱️  Time: {elapsed:.2f}s")
        print(f"📊 Output length: {len(result.stdout)} chars")
        if result.returncode == 0:
            print(f"✅ Success")
            # Show last 200 chars of output
            print(f"📄 Output: ...{result.stdout[-200:]}")
        else:
            print(f"❌ Failed: {result.stderr[:200]}")

        return elapsed
    except subprocess.TimeoutExpired:
        print("❌ Timeout after 120s")
        return 120.0
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    print("\n🧪 PERFORMANCE COMPARISON TEST")
    print("Testing gemma4:e4b inference speed\n")

    # Check if model blob exists
    import os
    if not os.path.exists(MODEL_BLOB):
        print(f"❌ Model not found at {MODEL_BLOB}")
        print("You may need to run with sudo or copy the model to a user-accessible location")
        return

    results = {}

    # Test 1: Current Ollama CPU
    try:
        results['ollama_cpu'] = test_ollama_cpu()
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        results['ollama_cpu'] = None

    # Test 2: llama.cpp CPU baseline
    try:
        results['llama_cpp_cpu'] = test_llama_cpp_cpu()
    except Exception as e:
        print(f"❌ llama.cpp CPU test failed: {e}")
        results['llama_cpp_cpu'] = None

    # Test 3: llama.cpp Vulkan GPU
    try:
        results['llama_cpp_vulkan'] = test_llama_cpp_vulkan()
    except Exception as e:
        print(f"❌ llama.cpp Vulkan test failed: {e}")
        results['llama_cpp_vulkan'] = None

    # Summary
    print("\n" + "="*60)
    print("📊 RESULTS SUMMARY")
    print("="*60)

    if results.get('ollama_cpu'):
        print(f"Ollama (CPU):          {results['ollama_cpu']:>6.2f}s  ← Current")

    if results.get('llama_cpp_cpu'):
        print(f"llama.cpp (CPU):       {results['llama_cpp_cpu']:>6.2f}s  ← Baseline")
        if results.get('ollama_cpu'):
            ratio = results['ollama_cpu'] / results['llama_cpp_cpu']
            print(f"                       {ratio:>6.2f}x vs Ollama")

    if results.get('llama_cpp_vulkan'):
        print(f"llama.cpp (Vulkan):    {results['llama_cpp_vulkan']:>6.2f}s  ← GPU 🚀")
        if results.get('ollama_cpu'):
            speedup = results['ollama_cpu'] / results['llama_cpp_vulkan']
            print(f"                       {speedup:>6.2f}x FASTER than Ollama!")
        if results.get('llama_cpp_cpu'):
            gpu_speedup = results['llama_cpp_cpu'] / results['llama_cpp_vulkan']
            print(f"                       {gpu_speedup:>6.2f}x GPU speedup")

    print("\n💡 Recommendation:")
    if results.get('llama_cpp_vulkan') and results.get('ollama_cpu'):
        if results['llama_cpp_vulkan'] < results['ollama_cpu'] / 2:
            print("   ✅ DEFINITELY switch to llama.cpp + Vulkan!")
            print(f"   You'll go from {results['ollama_cpu']:.1f}s → {results['llama_cpp_vulkan']:.1f}s")
        else:
            print("   ⚠️  Speedup is modest, may not be worth the migration effort")
    else:
        print("   ⚠️  Could not determine - check errors above")


if __name__ == "__main__":
    main()
