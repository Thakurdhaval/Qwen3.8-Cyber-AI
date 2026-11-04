"""Project-owned Kaggle runtime helpers for Qwen3.8-Cyber-AI.

This module orchestrates the Strata CLI; it does not implement the Strata inference
engine or redistribute model weights.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

STRATA_PORT = 8080
STRATA_ROOT = Path("/root/.local/share/strata")
BIN_DIR = Path("/root/.local/bin")


def log(message: str) -> None:
    print("[Qwen3.8-Cyber-AI] " + message, flush=True)


def redact(value: str) -> str:
    value = re.sub(r"sk-strata-[A-Za-z0-9._~-]+", "sk-strata-<redacted>", value)
    value = re.sub(r"(?i)(authorization\s*:\s*bearer\s+)\S+", r"\1<redacted>", value)
    return value


def run_command(command: list[str], *, timeout: int = 900,
                env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=timeout, env=env, check=False,
    )
    output = redact(result.stdout or "")
    if output:
        print(output, end="" if output.endswith("\n") else "\n", flush=True)
    if result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{output[-4000:]}"
        )
    return output


def load_kaggle_credentials(username: str, secret_name: str = "KAGGLE_API_TOKEN") -> dict[str, str]:
    if not username or username.lower().startswith("your-"):
        raise ValueError("Set KAGGLE_USERNAME in the notebook configuration cell.")
    try:
        from kaggle_secrets import UserSecretsClient
        token = UserSecretsClient().get_secret(secret_name).strip()
    except Exception as exc:
        raise RuntimeError(
            f"Kaggle Secret '{secret_name}' is unavailable. Add it in Add-ons > Secrets, "
            "enable notebook access, and rerun. Never paste the token into notebook code."
        ) from exc
    if not token:
        raise RuntimeError(f"Kaggle Secret '{secret_name}' is empty.")

    home = Path("/tmp/qwen38-cyber-ai-home")
    config = home / ".kaggle"
    config.mkdir(parents=True, exist_ok=True)
    token_file = config / "access_token"
    token_file.write_text(token + "\n", encoding="utf-8")
    token_file.chmod(0o600)

    env = os.environ.copy()
    env.update({
        "HOME": str(home),
        "KAGGLE_CONFIG_DIR": str(config),
        "KAGGLE_USERNAME": username,
        "TMPDIR": "/kaggle/working/tmp",
        "XDG_CACHE_HOME": str(home / ".cache"),
    })
    Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
    Path(env["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
    os.environ.update({
        "KAGGLE_CONFIG_DIR": str(config),
        "KAGGLE_USERNAME": username,
        "TMPDIR": env["TMPDIR"],
        "XDG_CACHE_HOME": env["XDG_CACHE_HOME"],
    })
    log("Kaggle Secret loaded into a temporary credential directory (value hidden).")
    return env


def install_kaggle_cli(env: dict[str, str]) -> None:
    run_command([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", "kaggle"],
                timeout=900, env=env)
    run_command(["kaggle", "--version"], timeout=60, env=env)


def gpu_names() -> list[str]:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=20, check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def hardware_summary() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "gpu_names": gpu_names(),
    }


def default_gpu_list() -> str:
    names = gpu_names()
    return ",".join(str(index) for index in range(len(names))) if names else "0"


def install_strata_if_missing() -> None:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ.get("PATH", "")
    if shutil.which("strata"):
        run_command(["strata", "--version"], timeout=60)
        return
    installer = Path("/tmp/qwen38-strata-install.sh")
    run_command([
        "curl", "-fsSL",
        "https://github.com/Niko1221/Strata/releases/latest/download/install.sh",
        "-o", str(installer),
    ], timeout=180)
    run_command(["sh", str(installer)], timeout=900)
    os.environ["PATH"] = str(BIN_DIR) + os.pathsep + os.environ.get("PATH", "")
    if not shutil.which("strata"):
        raise RuntimeError("Strata installer finished, but 'strata' is not available on PATH.")
    run_command(["strata", "--version"], timeout=60)


def _model_source_args(data_dir: Path) -> list[str]:
    return ["--data-dir", str(data_dir)]


def _launch_args(family: str, variant: str, context: str, vision: str,
                 gpu_list: str, data_dir: Path, plan: bool) -> list[str]:
    args = [
        "strata", "launch",
    ]
    if plan:
        args.append("--plan")
    args += [
        "--family", family, "--model", variant,
        *_model_source_args(data_dir),
        "--context", context, "--vision", vision,
        "--mtp", "off", "--tune", "skip", "--access", "cloudflare",
        "--port", str(STRATA_PORT), "--gpu", gpu_list,
    ]
    if not plan:
        args += ["--yes", "--no-tui"]
    return args


def _stream_command(command: list[str], timeout: int, label: str) -> str:
    log(label)
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, env=os.environ.copy(),
    )
    lines: list[str] = []
    started = time.monotonic()
    try:
        assert process.stdout is not None
        for line in process.stdout:
            safe_line = redact(line)
            print(safe_line, end="", flush=True)
            lines.append(line)
            if time.monotonic() - started > timeout:
                process.terminate()
                raise TimeoutError(f"{label} timed out after {timeout} seconds.")
        code = process.wait(timeout=max(1, timeout - int(time.monotonic() - started)))
    except Exception:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        raise
    output = redact("".join(lines))
    if code:
        raise RuntimeError(f"{label} failed (exit {code}). Recent output:\n{output[-4000:]}")
    return output


def run_plan(family: str, variant: str, context: str, vision: str,
             gpu_list: str, data_dir: Path) -> str:
    return _stream_command(
        _launch_args(family, variant, context, vision, gpu_list, data_dir, True),
        timeout=300, label="Reviewing Strata launch plan…",
    )


def launch_strata(family: str, variant: str, context: str, vision: str,
                  gpu_list: str, data_dir: Path) -> str:
    return _stream_command(
        _launch_args(family, variant, context, vision, gpu_list, data_dir, False),
        timeout=3600, label="Launching Strata model server…",
    )


def _extract_tunnel_url(output: str) -> str | None:
    match = re.search(r"https://[A-Za-z0-9-]+\.trycloudflare\.com", output)
    return match.group(0) if match else None


def _install_cloudflared() -> Path:
    existing = shutil.which("cloudflared")
    if existing:
        return Path(existing)
    machine = platform.machine().lower()
    asset = {
        "x86_64": "cloudflared-linux-amd64",
        "amd64": "cloudflared-linux-amd64",
        "aarch64": "cloudflared-linux-arm64",
        "arm64": "cloudflared-linux-arm64",
    }.get(machine)
    if not asset:
        raise RuntimeError(f"Unsupported CPU architecture for cloudflared: {machine}")
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    target = BIN_DIR / "cloudflared"
    run_command([
        "curl", "-fL", "--retry", "3",
        "https://github.com/cloudflare/cloudflared/releases/latest/download/" + asset,
        "-o", str(target),
    ], timeout=600)
    target.chmod(0o755)
    run_command([str(target), "--version"], timeout=60)
    return target


def start_quick_tunnel(existing_url: str | None = None) -> str:
    if existing_url:
        log("Using HTTPS URL reported by Strata.")
        return existing_url
    binary = _install_cloudflared()
    log_file = Path("/kaggle/working/cloudflared.log")
    with log_file.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(
            [str(binary), "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{STRATA_PORT}"],
            stdout=output, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            start_new_session=True, text=True,
        )
    for _ in range(60):
        time.sleep(2)
        if process.poll() is not None:
            raise RuntimeError("Cloudflare tunnel process exited. Inspect /kaggle/working/cloudflared.log.")
        if log_file.exists():
            url = _extract_tunnel_url(log_file.read_text(encoding="utf-8", errors="replace"))
            if url:
                log("Temporary Cloudflare Quick Tunnel started.")
                return url
    raise TimeoutError("No temporary Cloudflare URL appeared. Inspect cloudflared.log.")


def wait_health(timeout_seconds: int = 900) -> dict[str, Any]:
    import requests
    deadline = time.monotonic() + timeout_seconds
    last = "no response"
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"http://127.0.0.1:{STRATA_PORT}/health", timeout=5)
            if response.ok:
                body = response.json()
                if body.get("loaded") is True:
                    if not body.get("api_key"):
                        raise RuntimeError("Strata has no API-key protection. Do not expose a public tunnel.")
                    log("Strata health check passed; model is loaded and API-key protection is enabled.")
                    return body
                last = "model is not loaded yet"
            else:
                last = f"HTTP {response.status_code}"
        except RuntimeError:
            raise
        except Exception as exc:
            last = str(exc)
        time.sleep(5)
    raise TimeoutError("Strata did not become healthy: " + last)


def read_api_key() -> str:
    result = subprocess.run(
        ["strata", "launch", "--show-key"], text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60, check=True,
    )
    match = re.search(r"sk-strata-[A-Za-z0-9._~-]+", result.stdout or "")
    if not match:
        raise RuntimeError("Could not identify the Strata API key. Do not print command output.")
    return match.group(0)


def verify_public_endpoint(public_url: str, expected_model: str | None = None) -> dict[str, Any]:
    import requests
    base = public_url.rstrip("/")
    key = read_api_key()
    unauth = requests.get(base + "/v1/models", timeout=20)
    if unauth.status_code not in (401, 403):
        raise RuntimeError(
            f"Unauthenticated API request returned HTTP {unauth.status_code}; expected 401/403. "
            "Stop the tunnel and secure the endpoint."
        )
    headers = {"Authorization": "Bearer " + key}
    response = requests.get(base + "/v1/models", headers=headers, timeout=30)
    if not response.ok:
        raise RuntimeError(f"Authenticated model-list request failed: HTTP {response.status_code}.")
    models = response.json().get("data", [])
    available = [item.get("id") for item in models if isinstance(item, dict) and item.get("id")]
    model_id = expected_model if expected_model in available else (available[0] if available else expected_model)
    if not model_id:
        raise RuntimeError("Strata did not return a model ID.")
    chat = requests.post(
        base + "/v1/chat/completions",
        headers={**headers, "Content-Type": "application/json"},
        json={
            "model": model_id,
            "messages": [{"role": "user", "content": "Reply with exactly: connection working."}],
            "max_tokens": 32,
            "reasoning_effort": "none",
            "stream": False,
        },
        timeout=240,
    )
    if not chat.ok:
        raise RuntimeError(f"Authenticated generation test failed: HTTP {chat.status_code}.")
    body = chat.json()
    choices = body.get("choices", [])
    answer = choices[0].get("message", {}).get("content", "") if choices else ""
    if isinstance(answer, list):
        answer = "".join(part.get("text", "") for part in answer if isinstance(part, dict))
    print("Authenticated generation test: " + str(answer))
    log("Unauthenticated requests were rejected; authenticated generation succeeded.")
    return {"model_id": model_id, "url": base, "unauthenticated_status": unauth.status_code}


def opencode_config_snippet(public_url: str, model_id: str) -> str:
    provider = {
        "name": "Qwen3.8-Cyber-AI Kaggle",
        "package": "@opencode/ai/providers/openai-compatible",
        "settings": {
            "baseURL": public_url.rstrip("/") + "/v1",
            "apiKey": "{file:~/.config/opencode/qwen38-strata-key.txt}",
            "encoding": "none",
            "timeout": 600000,
            "headerTimeout": 120000,
            "chunkTimeout": 300000,
        },
        "models": {
            model_id: {
                "name": model_id,
                "modelID": model_id,
                "reasoningEffort": "none",
                "capabilities": {"tools": True, "input": ["text"], "output": ["text"]},
                "limit": {"context": 32768, "output": 8192},
            }
        },
    }
    return json.dumps({"qwen38": provider}, indent=2)
