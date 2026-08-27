"""QLoRA fine-tuning of Qwen2.5-1.5B-Instruct for Redactame's professional rewrite task.

The recipe, in one picture:

    base model (1.5B)  --load in 4-bit (bitsandbytes)-->  frozen, tiny in VRAM
                       --attach LoRA adapter (peft)---->  only these ~few M params train
                       --SFTTrainer (trl) on our pairs->  learn (informal -> professional)

Only the small LoRA adapter is trained; the 4-bit base stays frozen. That is what makes this
fit in ~6 GB of VRAM and produce a small adapter file instead of a whole new model.

    .\.venv\Scripts\python.exe train_qlora.py
"""

import json
import sys
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig
from transformers import AutoTokenizer, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer

HERE = Path(__file__).resolve().parent
# Reuse the EXACT same prompt we use at inference time (single source of truth in prompt.py),
# so what the model is trained on matches what it will later be asked.
sys.path.insert(0, str(HERE.parent / "scripts"))
from prompt import build_messages  # noqa: E402

BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
DATA_FILE = HERE / "data" / "train.jsonl"
OUTPUT_DIR = HERE / "output" / "qwen2.5-1.5b-redactame-lora"


def load_training_dataset() -> Dataset:
    """Each example is a chat: system + user (from prompt.py) + the gold assistant answer."""
    rows = [json.loads(line) for line in DATA_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    examples = [
        {"messages": build_messages(case) + [{"role": "assistant", "content": case["output"]}]}
        for case in rows
    ]
    return Dataset.from_list(examples)


def main() -> None:
    dataset = load_training_dataset()
    print(f"training examples: {len(dataset)}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 4-bit quantization of the base model (the "Q" in QLoRA). nf4 = a 4-bit format tuned for
    # neural-net weights; double-quant squeezes a bit more; compute in bf16 (Ampere supports it).
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
    )

    # The LoRA adapter: small low-rank matrices injected into the linear layers. r is the "rank"
    # (capacity); higher r = more capacity but bigger/slower. r=16 is a common starting point.
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )

    # Training settings. The dataset is tiny (a smoke test), so effective batch is small and we
    # run a few epochs just to watch the loss move and confirm the pipeline works end to end.
    sft_config = SFTConfig(
        output_dir=str(OUTPUT_DIR),
        num_train_epochs=5,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,     # effective batch = 1 * 4
        learning_rate=2e-4,
        lr_scheduler_type="cosine",
        max_length=768,
        packing=False,
        gradient_checkpointing=True,       # trade compute for less VRAM
        bf16=True,
        optim="paged_adamw_8bit",          # 8-bit optimizer (bitsandbytes) to save VRAM
        logging_steps=1,
        save_strategy="epoch",
        report_to="none",
        seed=42,
    )

    trainer = SFTTrainer(
        model=BASE_MODEL,
        args=sft_config,
        train_dataset=dataset,
        processing_class=tokenizer,
        quantization_config=bnb_config,    # trl loads the base in 4-bit for us
        peft_config=lora_config,           # ...and attaches the LoRA adapter
    )

    trainer.train()
    trainer.save_model(str(OUTPUT_DIR))
    print(f"LoRA adapter saved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
