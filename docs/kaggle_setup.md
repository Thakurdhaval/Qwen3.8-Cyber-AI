# Kaggle GPU Setup

This guide describes a starter workflow for running the project in a Kaggle notebook.

## 1. Create a notebook

1. Open Kaggle and create a new notebook.
2. In notebook settings, select a GPU accelerator if one is available to your account.
3. Confirm the selected accelerator in the notebook output. Do not assume that a T4x2 runtime is available.

## 2. Check the runtime

Run:

```python
import torch

print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("GPU count:", torch.cuda.device_count())
```

If CUDA is unavailable, check the notebook accelerator settings before installing or changing PyTorch.

## 3. Install project dependencies

In a notebook cell:

```python
%pip install -q "transformers>=4.51.0" "accelerate>=1.6.0" "bitsandbytes>=0.45.0" "gradio>=5.0.0"
```

If package installation changes core libraries, restart the notebook session and repeat the GPU check.

## 4. Download the project

Clone the public repository:

```bash
!git clone https://github.com/Thakurdhaval/Qwen3.8-Cyber-AI.git
%cd Qwen3.8-Cyber-AI
```

## 5. Start with a modest model

The starter app defaults to `Qwen/Qwen3-4B`. You can set another compatible Hugging Face model ID:

```python
import os
os.environ["MODEL_ID"] = "Qwen/Qwen3-4B"
os.environ["LOAD_IN_4BIT"] = "true"
os.environ["GRADIO_SHARE"] = "true"
```

Then launch:

```bash
!python app/gradio_app.py
```

Gradio may print a temporary public URL. Treat it as a shareable link: anyone who obtains it may be able to access the running app. Do not submit secrets or personal data. Stop the notebook session when finished.

## 6. Resource notes

- A Tesla T4 commonly has 16 GB of GPU memory, but the usable amount varies.
- A single T4 is not the same as two T4 GPUs.
- 4-bit quantization reduces weight memory but does not eliminate memory needed for activations, context, or runtime overhead.
- Model loading can fail due to incompatible package versions, unsupported quantization kernels, insufficient memory, or gated model access.
- Start with a smaller model and short prompts. Monitor GPU memory before attempting larger models.

## Troubleshooting

- **CUDA unavailable:** confirm the GPU accelerator is enabled and restart the session.
- **Out of memory:** reduce the model size, context length, or generation length. Restart the runtime to clear allocated memory.
- **bitsandbytes error:** check its compatibility with the Kaggle CUDA/PyTorch environment.
- **Chat template error:** the selected model may not support the same chat-template arguments. Consult that model's documentation and adjust the application.
- **Model access denied:** check the model's license and access requirements. Never place a Hugging Face token directly in notebook source code or commit it to Git.

This is a starter guide, not a guarantee that every model will run on every Kaggle accelerator.
