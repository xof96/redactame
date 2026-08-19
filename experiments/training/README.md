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
