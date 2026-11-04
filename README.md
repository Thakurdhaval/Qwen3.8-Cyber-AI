# Qwen3.8-Cyber-AI

An open-source, Kaggle-friendly AI assistant project for ethical cybersecurity learning and defensive security education.

> **Important:** The repository name is a project name. The initial implementation uses a configurable Hugging Face model ID and does not claim to provide or reproduce a proprietary or 125B-parameter model. The default model is `Qwen/Qwen3-4B`, a practical starting point to test with a single Kaggle Tesla T4 GPU using 4-bit loading. Actual memory use and compatibility depend on the model revision, software versions, and available GPU memory.

## Goals

- Explain networking, Linux, Windows security, and SOC concepts.
- Support defensive security learning and authorized lab exercises.
- Provide a simple Gradio chat interface.
- Run experiments in a Kaggle notebook with a GPU runtime.
- Keep setup instructions reproducible and security-conscious.

## Project status

**Early development.** The repository currently contains the starter application and setup documentation. Kaggle execution and model compatibility must be tested in your own session before relying on them.

## Features

- Configurable Hugging Face causal language model.
- Optional 4-bit quantization through BitsAndBytes.
- Gradio browser interface.
- Defensive cybersecurity system instructions.
- Kaggle-oriented setup guide.

## Repository layout

```text
Qwen3.8-Cyber-AI/
├── app/
│   └── gradio_app.py
├── config/
│   └── system_prompt.txt
├── docs/
│   ├── kaggle_setup.md
│   └── security.md
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Quick start

### 1. Requirements

- Python 3.10 or newer.
- A compatible NVIDIA GPU is recommended for local inference.
- A Hugging Face account/token is only needed if the selected model requires gated access. Never commit tokens or credentials.

### 2. Install dependencies

Install a PyTorch build suitable for your platform first. For Kaggle, use the PyTorch installation already provided by the selected notebook image unless it is incompatible.

Then install:

```bash
pip install -r requirements.txt
```

### 3. Configure the model

Set the model ID with an environment variable:

```bash
export MODEL_ID=Qwen/Qwen3-4B
```

On Windows PowerShell:

```powershell
$env:MODEL_ID = "Qwen/Qwen3-4B"
```

### 4. Start the interface

```bash
python app/gradio_app.py
```

Open the local URL printed by Gradio. To create a temporary public share link, set `GRADIO_SHARE=true` before starting the app. Anyone with that link may be able to access the interface while the session is running; do not expose private data.

## Kaggle

See [docs/kaggle_setup.md](docs/kaggle_setup.md) for a GPU notebook workflow. A single Tesla T4 is not equivalent to a multi-GPU T4x2 setup. Large models may not fit, even with quantization or CPU offload. Start with the default 4B model and verify actual memory use.

## Safety

This project is intended for education, defensive security, and authorized labs. It must not be used to access systems without permission, steal credentials, deploy malware, or disrupt services. Read [docs/security.md](docs/security.md).

## Configuration

| Environment variable | Default | Purpose |
|---|---|---|
| `MODEL_ID` | `Qwen/Qwen3-4B` | Hugging Face model identifier |
| `LOAD_IN_4BIT` | `true` | Enable 4-bit loading when supported |
| `MAX_NEW_TOKENS` | `512` | Maximum generated tokens |
| `GRADIO_SHARE` | `false` | Enable a temporary Gradio share URL |

## Limitations

- Model responses can be incorrect, incomplete, or unsafe; verify important information.
- Quantization can affect output quality and does not guarantee a model will fit in memory.
- Kaggle sessions have time, resource, and internet-access limits.
- A Gradio share URL is not a production deployment or an authentication system.
- No model weights are included in this repository.

## Contributing

Issues and pull requests are welcome. Please do not submit secrets, personal data, malware, or instructions for unauthorized activity.

## License

This project is released under the MIT License. See [LICENSE](LICENSE).


## Kaggle

- For the experimental **Qwen3.8-Flash-Next 125B Gyro-S** path on a Kaggle **T4x2** session, see [the dedicated launcher notebook](notebooks/qwen38_flash_next_125b_gyro_s_t4x2.ipynb) and [setup guide](docs/kaggle_125b_gyro_s.md). This path uses the Strata engine and third-party Kaggle helper code; review the documented trust, hardware, and security warnings before running it.
- For the smaller Transformers-based starter path, see [docs/kaggle_setup.md](docs/kaggle_setup.md).

The 125B workflow is experimental and is not guaranteed to run in every Kaggle session. Verify that two T4 GPUs are actually visible and that the Strata launch plan succeeds before downloading or launching the model.
