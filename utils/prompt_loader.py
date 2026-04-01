from pathlib import Path

import config


def load_prompt(sheet_number: int, prompts_dir: Path = config.PROMPTS_DIR) -> str:
    """
    Load a sheet prompt .md file by sheet number.
    Raises FileNotFoundError with a clear message if the file is missing.
    Never hardcodes prompt content — always reads from disk.
    """
    filename = config.PROMPT_FILES.get(sheet_number)
    if filename is None:
        raise ValueError(f"No prompt registered for sheet number {sheet_number}")

    path = prompts_dir / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {path}\n"
            f"Expected: prompts/{filename}"
        )

    return path.read_text(encoding="utf-8")


def load_prompt_by_name(filename: str, prompts_dir: Path = config.PROMPTS_DIR) -> str:
    """Load a prompt file by explicit filename (for briefing / content agents)."""
    path = prompts_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")
