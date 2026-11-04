"""Gradio chat interface for a configurable Qwen-compatible model."""

import os
from pathlib import Path

import gradio as gr
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = os.getenv("MODEL_ID", "Qwen/Qwen3-4B")
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
LOAD_IN_4BIT = os.getenv("LOAD_IN_4BIT", "true").lower() in {"1", "true", "yes"}
SYSTEM_PROMPT = (ROOT / "config" / "system_prompt.txt").read_text(encoding="utf-8")

if not torch.cuda.is_available():
    raise RuntimeError(
        "No CUDA GPU was detected. This starter app is configured for GPU inference. "
        "Run it in a GPU-enabled environment or adapt the loading configuration for CPU use."
    )

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

model_kwargs = {
    "device_map": "auto",
    "torch_dtype": torch.float16,
}

if LOAD_IN_4BIT:
    try:
        from transformers import BitsAndBytesConfig
    except ImportError as exc:
        raise RuntimeError(
            "4-bit loading requires a compatible bitsandbytes installation."
        ) from exc

    model_kwargs["quantization_config"] = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **model_kwargs)
model.eval()


def respond(message, history):
    """Generate a response from the model using the configured safety prompt."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Gradio history is a list of message dictionaries in the current ChatInterface API.
    for item in history or []:
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"}:
            content = item.get("content")
            if isinstance(content, str):
                messages.append({"role": item["role"], "content": content})

    messages.append({"role": "user", "content": message})

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=0.7,
            top_p=0.8,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = output[0][inputs["input_ids"].shape[-1]:]
    answer = tokenizer.decode(generated, skip_special_tokens=True).strip()
    return answer or "The model did not return a text response."


demo = gr.ChatInterface(
    fn=respond,
    title="Qwen Cybersecurity Learning Assistant",
    description=(
        "An experimental assistant for ethical cybersecurity learning and defensive "
        "security education. Do not enter passwords, tokens, or private information."
    ),
    examples=[
        "Explain Linux file permissions with a safe example.",
        "What does a SOC analyst do when an alert is received?",
        "Explain the TCP three-way handshake.",
        "How can I investigate failed Windows logons defensively?",
    ],
)

if __name__ == "__main__":
    share = os.getenv("GRADIO_SHARE", "false").lower() in {"1", "true", "yes"}
    demo.launch(share=share)
