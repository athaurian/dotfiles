"""Low-level Neovim RPC via --remote-expr."""

from __future__ import annotations

import json
import os
import subprocess


def vim_single_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def extract_json(text: str, marker: str) -> dict | None:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and marker in value:
            return value
    return None


from ..config import NVIM_RPC_TIMEOUT


def nvim_rpc(
    server_path: str, lua: str, marker: str, timeout: float = NVIM_RPC_TIMEOUT
) -> dict | None:
    expression = f"json_encode(luaeval({vim_single_quote(lua)}))"
    env = os.environ.copy()
    env.pop("NVIM", None)
    try:
        result = subprocess.run(
            [
                "nvim",
                "--headless",
                "--server",
                server_path,
                "--remote-expr",
                expression,
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return None
    return extract_json(result.stdout + "\n" + result.stderr, marker)
