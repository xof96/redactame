# experiments/training/

QLoRA fine-tuning of a small base model (`qwen2.5:1.5b`) to specialize it for Redactame's
rewrite/translate task. Desktop-only, **not** part of the Android app. Runs on the dev machine's
GPU (an RTX 3060, 6 GB VRAM is enough for QLoRA on a ~1.5B model).

## Why a separate environment

The training libraries (PyTorch, bitsandbytes, ...) don't support Python 3.14 yet, and we don't
want to pollute the system Python. So everything lives in an isolated **virtual environment**
(`.venv`) built from Python 3.11. A venv is just a private folder with its own Python + packages.

## One-time setup

Create the venv (from Python 3.11) and install the dependencies:

```powershell
cd C:\Users\matia\Documents\Projects\redactame\experiments\training

# 1. isolated environment from Python 3.11
& "C:\Users\matia\AppData\Local\Programs\Python\Python311\python.exe" -m venv .venv

# 2. upgrade pip inside it
.\.venv\Scripts\python.exe -m pip install --upgrade pip

# 3. PyTorch with CUDA (GPU) — separate index, not on default PyPI
.\.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu124

# 4. verify PyTorch sees the GPU
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__, 'CUDA:', torch.cuda.is_available())"

# 5. the rest of the training stack
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Always run training scripts with the venv's Python: `.\.venv\Scripts\python.exe <script>.py`.

## What each dependency is for

See `requirements.txt`. In short: **torch** (compute engine) → **transformers** (model/tokenizer)
→ **bitsandbytes** (4-bit base) + **peft** (LoRA adapters) = QLoRA, driven by **trl**'s
SFTTrainer and **accelerate**.

## Full pipeline: from data to a testable model

These are the steps that take our training data to a model you can actually run in Ollama.

**1. Train the LoRA adapter on all datasets.**

```powershell
.\.venv\Scripts\python.exe train_qlora_handcrafted.py
```

Reads every file in `data/` (`train.jsonl`, `train_real.jsonl`, `train_synth.jsonl`,
`train_synth_gpt.jsonl`), concatenates and shuffles them, and trains a QLoRA adapter into
`output/<name>-lora/`. The base stays 4-bit and frozen, so only the small adapter (about 35 MB)
is saved.

**2. Merge the adapter into the base model.**

```powershell
.\.venv\Scripts\python.exe model_generator.py
```

Loads the base in fp16 on the CPU (to avoid VRAM spikes), attaches the adapter with PEFT, calls
`merge_and_unload()`, and saves a full standalone model to `output/<name>-lora/merged_model/`.
Ollama and llama.cpp cannot use a bare adapter, they need a complete model.

**3. Convert the merged model to GGUF with llama.cpp.**

GGUF is the file format Ollama and llama.cpp load. Clone `llama.cpp` once, then run its converter:

```powershell
python convert_hf_to_gguf.py <path-to>\merged_model --outfile redactame.gguf --outtype f16
```

Optional, quantize to 4-bit to shrink it for the phone:

```powershell
.\llama-quantize.exe redactame.gguf redactame-q4.gguf Q4_K_M
```

**4. Register the model in Ollama with a Modelfile.**

Create a file named `Modelfile` next to the gguf with a single line pointing at it:

```
FROM ./redactame.gguf
```

Then register it:

```powershell
ollama create redactame-v2:ft -f Modelfile
```

**5. Test the model.**

Quick manual check:

```powershell
ollama run redactame-v2:ft "<full prompt + text>"
```

Systematic check (the important one), through our eval harness:

```powershell
python ..\scripts\run_eval.py --model redactame-v2:ft
```

Do not judge a fine-tune from a single example. Measure on the whole eval set and compare against
the base model, because one hard case can look like failure while the average clearly improved.
