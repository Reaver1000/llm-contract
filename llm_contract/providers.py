"""Provider layer. One minimal interface in front of every LLM API."""
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0

    def add(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens


@dataclass
class Completion:
    text: str
    model: str
    usage: Usage


class Provider(ABC):
    """The two things every provider must do: complete(), report a model name."""

    model: str = ""

    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int = 2000) -> Completion: ...


class AnthropicProvider(Provider):
    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None):
        from anthropic import Anthropic

        self.client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> Completion:
        r = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
        return Completion(text=text, model=self.model,
                          usage=Usage(r.usage.input_tokens, r.usage.output_tokens))


class OpenAIProvider(Provider):
    def __init__(self, model: str = "gpt-5-mini", api_key: str | None = None):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])
        self.model = model

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> Completion:
        r = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return Completion(text=r.choices[0].message.content, model=self.model,
                          usage=Usage(r.usage.prompt_tokens, r.usage.completion_tokens))


class MockProvider(Provider):
    """Scripted responses returned in order. Powers tests and mock-mode eval cases."""

    def __init__(self, responses: list[str]):
        self.responses = list(responses)
        self.calls: list[dict] = []
        self.model = "mock"

    def complete(self, system: str, user: str, max_tokens: int = 2000) -> Completion:
        self.calls.append({"system": system, "user": user})
        if not self.responses:
            raise AssertionError("MockProvider ran out of scripted responses")
        return Completion(text=self.responses.pop(0), model="mock", usage=Usage(10, 20))


def load_provider(name: str, model: str | None = None) -> Provider:
    providers = {"anthropic": AnthropicProvider, "openai": OpenAIProvider}
    if name not in providers:
        raise ValueError(f"Unknown provider {name!r}. Available: {sorted(providers)}")
    return providers[name](model=model) if model else providers[name]()
