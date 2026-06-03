import os

from dotenv import load_dotenv
from openai import OpenAI


PROMPT_VERSION = "v1"
DEFAULT_MODEL = "gpt-5-mini"


def generate_reply_draft(
    body: str,
    category: str | None = None,
    urgency: str | None = None,
) -> dict[str, str]:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    model_name = os.getenv("OPENAI_MODEL") or DEFAULT_MODEL
    client = OpenAI(api_key=api_key)

    # 分類結果があれば文脈として渡す（無ければ本文だけで生成する）。
    context_lines = [f"問い合わせ本文:\n{body}"]
    if category:
        context_lines.append(f"カテゴリ: {category}")
    if urgency:
        context_lines.append(f"緊急度: {urgency}")
    user_content = "\n\n".join(context_lines)

    response = client.responses.create(
        model=model_name,
        input=[
            {
                "role": "system",
                "content": (
                    "あなたはカスタマーサポート担当者です。"
                    "問い合わせ内容に対する、丁寧で簡潔な日本語の一次返信案を作成してください。"
                    "これは自動送信されるものではなく、担当者が確認・編集して使う下書きです。"
                    "事実を断定しすぎず、状況の確認が必要な場合は丁寧に質問を含めてください。"
                    "返信本文のみを出力し、前置きや補足説明は付けないでください。"
                ),
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
    )

    reply_text = response.output_text
    if not reply_text:
        raise ValueError("AI reply draft response was empty.")

    return {
        "reply_text": reply_text.strip(),
        "model_name": model_name,
        "prompt_version": PROMPT_VERSION,
    }
