# Qwen3.8-Flash-Next 125B Gyro-S on Kaggle T4x2

This experimental workflow uses the Strata inference engine and the Gyro-S quantization for Qwen3.8-Flash-Next. It is not a conventional Hugging Face Transformers load.

## Hardware and storage

The upstream Strata-on-Kaggle project reports a reference session with 2 NVIDIA Tesla T4 GPUs (about 15 GB VRAM each) and roughly 31 GB system RAM. It reports approximately 27.6 GB combined RAM + VRAM model memory for Gyro-S, a 58.5 GB main model file, and a larger cache of about 80 GiB including support files.

These are upstream estimates and observed configuration notes, not a guarantee. Kaggle GPU availability, RAM, disk, quota, model compatibility, and session limits can change. The notebook checks for two visible GPUs and stops if fewer than two are detected. A successful download is not proof that the model loaded or generated output.

## Before running

1. Open the [Kaggle launcher notebook](../notebooks/qwen38_flash_next_125b_gyro_s_t4x2.ipynb) in Kaggle.
2. Confirm the notebook runtime actually shows **2 × Tesla T4**. Do not rely only on saved notebook metadata.
3. Enable Internet.
4. Add a Kaggle API token as a Kaggle Secret named `KAGGLE_API_TOKEN`, then grant this notebook access. Never paste the token into a code cell or commit it.
5. Edit `KAGGLE_USERNAME` in the configuration cell to your Kaggle username. This is not necessarily your GitHub username.
6. Keep `I_CONFIRM_MODEL_LICENSE_AND_PRIVATE_STORAGE = False` until you have read the model license and confirmed private dataset caching is permitted.

## Run sequence

Run notebook cells from top to bottom:

1. Load helper code and credentials.
2. Detect GPU hardware and restore any personal private caches.
3. Install Strata if it is not already present.
4. Review the Strata launch plan. Stop if it reports an unsupported backend, model, GPU selection, or missing dependency.
5. Launch the model with API-key protection.
6. Verify that unauthenticated API requests are rejected and an authenticated generation request succeeds.
7. Optionally save personal model/runtime caches to private Kaggle datasets, only after checking the model license.
8. Optionally connect OpenCode Desktop while the Kaggle session and temporary tunnel remain active.

## Third-party components and trust

The notebook uses helper code from [DevZoneX Strata on Kaggle](https://github.com/iAmAjayTeli/devzonex-strata-kaggle), pinned to commit [`ca775962d90a7bc2a4b2db6eecb052e0e399c94c`](https://github.com/iAmAjayTeli/devzonex-strata-kaggle/commit/ca775962d90a7bc2a4b2db6eecb052e0e399c94c), and installs Strata from [Niko1221/Strata](https://github.com/Niko1221/Strata). The helper performs package installation, downloads model/runtime components, may upload caches to datasets in your Kaggle account, and can expose a temporary Cloudflare Quick Tunnel. Review upstream code and the commands it runs before executing it. This repository does not maintain or audit those third-party components.

## Security warnings

- The tunnel URL is publicly reachable while active. The notebook verifies API-key enforcement, but never share the URL or API key publicly.
- Do not send passwords, access tokens, private keys, personal data, or confidential work data to the model.
- Do not commit Kaggle API tokens, Strata API keys, model weights, or cache archives to GitHub.
- Private Kaggle datasets remain subject to Kaggle's storage, quota, terms, and processing rules.
- Stop the server and tunnel and end the Kaggle session when finished.

## Troubleshooting

- **Only one GPU detected:** stop; change Kaggle accelerator to T4x2 if available. Do not proceed with this 125B profile on one T4.
- **Insufficient disk/RAM/VRAM:** do not repeatedly retry. Review the Strata plan, free storage, and reduce context only if the model's documented support allows it.
- **Model or engine unavailable:** stop and consult the official [Strata model guide](https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md).
- **No API-key enforcement:** stop the tunnel immediately and do not expose the endpoint.
- **Kaggle session ends:** temporary URLs and in-memory server state are lost. Restore caches in a new session if they were successfully saved.

## References

- [Strata model compatibility and memory guide](https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md)
- [Strata Gyro documentation](https://github.com/Niko1221/Strata/blob/main/docs/GYRO.md)
- [DevZoneX Kaggle launcher source](https://github.com/iAmAjayTeli/devzonex-strata-kaggle)
