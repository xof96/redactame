import json
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# ---- CONSTANTS ----
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from prompt import build_messages  # noqa: E402

BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"  # ej: "meta-llama/Llama-3.2-3B"
ADAPTER_PATH = HERE / "output" / "qwen2.5-1.5b-redactame-v2-lora"         # where the LoRA adapter is stored
OUTPUT_DIR = HERE / "output" / "qwen2.5-1.5b-redactame-v2-lora" / "merged_model"  # where the merged model will be saved

# Load the base model in float16/bfloat16 (without quantization)
base_model = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.float16,
    device_map="cpu",  # Use "cpu" to avoid VRAM spikes when merging
)

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

# Load the QLoRA adapter on top of the base model
model = PeftModel.from_pretrained(base_model, ADAPTER_PATH)

# Merge weights and save the final complete model
merged_model = model.merge_and_unload()
merged_model.save_pretrained(OUTPUT_DIR, safe_serialization=True)
tokenizer.save_pretrained(OUTPUT_DIR)

print(f"Merged model saved to: {OUTPUT_DIR}")