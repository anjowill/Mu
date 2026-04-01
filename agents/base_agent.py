"""
BaseAgent — shared foundation for every agent in the pipeline.

Responsibilities:
- Load system prompt from disk (never hardcoded)
- Wrap client.messages.create() with retry logic
- Log token usage via Rich console
- Preserve raw LLM response text for audit
"""

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

import anthropic

import config
from utils.console import get_console, print_agent_complete, print_warning

_console = get_console()


class BaseAgent(ABC):
    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str = config.DEFAULT_MODEL,
        prompt_path: Optional[Path] = None,
        temperature: float = config.SHEET_AGENT_TEMPERATURE,
        max_tokens: int = config.MAX_TOKENS_SHEET,
    ):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt: str = self._load_prompt(prompt_path)

    @property
    @abstractmethod
    def agent_name(self) -> str:
        """Human-readable name shown in terminal output."""

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Each agent implements its own run() signature and return type."""

    # ── Claude API call ────────────────────────────────────────────────────────

    def _call_claude(self, user_message: str) -> tuple[str, dict]:
        """
        Call the Claude API with exponential-backoff retry.

        Returns:
            (response_text, usage_dict)
        """
        last_error: Optional[Exception] = None
        delay = config.RETRY_BASE_DELAY_SECONDS

        for attempt in range(1, config.MAX_RETRIES + 1):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    system=self.system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )
                text = response.content[0].text
                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                }
                print_agent_complete(self.agent_name, usage)
                return text, usage

            except anthropic.RateLimitError as e:
                last_error = e
                print_warning(f"{self.agent_name} — rate limit hit (attempt {attempt}/{config.MAX_RETRIES}). Retrying in {delay}s…")
                time.sleep(delay)
                delay *= 2

            except anthropic.APIStatusError as e:
                if e.status_code >= 500:
                    last_error = e
                    print_warning(f"{self.agent_name} — server error {e.status_code} (attempt {attempt}/{config.MAX_RETRIES}). Retrying in {delay}s…")
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise  # 4xx errors are not retried

        raise RuntimeError(
            f"{self.agent_name} failed after {config.MAX_RETRIES} retries: {last_error}"
        )

    # ── Prompt loading ────────────────────────────────────────────────────────

    @staticmethod
    def _load_prompt(path: Optional[Path]) -> str:
        if path is None:
            return ""
        if not path.exists():
            raise FileNotFoundError(
                f"System prompt not found: {path}\n"
                "Ensure the prompts/ directory contains the required .md file."
            )
        return path.read_text(encoding="utf-8")

    # ── Normalized batch → markdown table helper ───────────────────────────────

    @staticmethod
    def batch_to_markdown_table(batch: Any) -> str:
        """
        Convert a NormalizedBatch to the standard markdown table format
        expected by the sheet prompt instructions.
        """
        lines = [
            "| Company Name | Deal Size ($ Mn) | Stage | Industry | Business Model | Investors |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for deal in batch.deals:
            size = f"{deal.deal_size_mn:.1f}" if deal.deal_size_mn is not None else "–"
            investors = ", ".join(deal.investors_list) if deal.investors_list else "–"
            lines.append(
                f"| {deal.company_name} | {size} | {deal.stage_normalized} "
                f"| {deal.sector_normalized} | {deal.business_model} | {investors} |"
            )
        return "\n".join(lines)
