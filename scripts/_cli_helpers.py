"""Small interactive CLI helpers for the numbered pipeline scripts."""

from __future__ import annotations

from pathlib import Path


def prompt_text(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"{prompt}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        print("A value is required.")


def prompt_path(
    prompt: str,
    value: Path | None = None,
    *,
    must_exist: bool = True,
    expect_dir: bool | None = None,
    default: str | None = None,
) -> Path:
    candidate = value
    while candidate is None:
        raw = prompt_text(prompt, default=default)
        candidate = Path(raw).expanduser()

    candidate = candidate.expanduser()
    if not must_exist:
        return candidate

    while True:
        if candidate.exists():
            if expect_dir is True and not candidate.is_dir():
                print(f"{candidate} exists but is not a directory.")
            elif expect_dir is False and not candidate.is_file():
                print(f"{candidate} exists but is not a file.")
            else:
                return candidate
        else:
            print(f"{candidate} does not exist.")

        raw = prompt_text(prompt, default=default)
        candidate = Path(raw).expanduser()
