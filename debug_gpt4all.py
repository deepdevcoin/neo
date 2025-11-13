#!/usr/bin/env python3
"""
Debug script to check GPT4All available parameters
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from gpt4all import GPT4All
    print("✓ GPT4All imported successfully")

    # Try to find model
    import pathlib
    model_dir = pathlib.Path.home() / ".local" / "share" / "jarvis" / "models"
    model_path = model_dir / "Phi-3-mini-4k-instruct-q4.gguf"

    if not model_path.exists():
        # Try external path
        current_dir = pathlib.Path(__file__).parent
        model_path = current_dir / "models" / "Phi-3-mini-4k-instruct-q4.gguf"

    if model_path.exists():
        print(f"✓ Found model at: {model_path}")
        print("Loading model...")

        model = GPT4All(str(model_path), allow_download=False)
        print("✓ Model loaded successfully")

        # Check the generate method signature
        print("\nChecking GPT4All.generate method signature:")
        import inspect
        sig = inspect.signature(model.generate)
        print(f"Parameters: {list(sig.parameters.keys())}")

        for param_name, param in sig.parameters.items():
            if param.default != inspect.Parameter.empty:
                print(f"  {param_name}: default = {param.default}")
            else:
                print(f"  {param_name}: required")

        print("\nTesting basic generation...")
        try:
            response = model.generate("Hello", max_tokens=10, temp=0.7)
            print(f"✓ Basic generation works: '{response}'")
        except Exception as e:
            print(f"✗ Basic generation failed: {e}")

    else:
        print(f"✗ Model not found at: {model_path}")

except ImportError as e:
    print(f"✗ Failed to import GPT4All: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()