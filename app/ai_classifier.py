import os
from typing import Literal

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field


PROMPT_VERSION = "v1"
DEFAULT_MODEL = "gpt-5-mini"

CATEGORY_VALUES = {"login", "billing", "technical_issue", "how_to_use", "other"}
URGENCY_VALUES = {"low", "medium", "high"}


class ClassificationResult(BaseModel):
    category: Literal["login", "billing", "technical_issue", "how_to_use", "other"]
    urgency: Literal["low", "medium", "high"]
    reason: str = Field(..., min_length=1)


def classify_inquiry_text(body: str) -> dict[str, str]:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    model_name = os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    client = OpenAI(api_key=api_key)

    response = client.responses.parse(
        model=model_name,
        input=[
            {
                "role": "system",
                "content": (
                    "You classify customer inquiries. "
                    "Choose exactly one category and one urgency. "
                    "Keep the reason concise."
                ),
            },
            {
                "role": "user",
                "content": f"Inquiry body:\n{body}",
            },
        ],
        text_format=ClassificationResult,
    )

    result = response.output_parsed
    if result is None:
        raise ValueError("AI classification response could not be parsed.")

    if result.category not in CATEGORY_VALUES:
        raise ValueError(f"Invalid category: {result.category}")
    if result.urgency not in URGENCY_VALUES:
        raise ValueError(f"Invalid urgency: {result.urgency}")

    return {
        "category": result.category,
        "urgency": result.urgency,
        "reason": result.reason,
        "model_name": model_name,
        "prompt_version": PROMPT_VERSION,
    }
