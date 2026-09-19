import logging
from datetime import date
from openai import AsyncOpenAI, APIError
from pydantic import BaseModel, Field

class Transaction(BaseModel):
    category: str
    group: str
    subcategory: str
    amount: float
    description: str = ""
    transaction_date: date = Field(default_factory=date.today)

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key, timeout=20.0)

    async def parse_transaction(self, text: str, reference_text: str) -> Transaction | None:
        system_prompt = (
            "You are a financial assistant. Convert the user's text into a JSON object "
            "with fields: category, group, subcategory, amount, description. "
            "Use this reference guide:\n" + reference_text
        )
        try:
            resp = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            content = resp.choices[0].message.content
            return Transaction.model_validate_json(content) if content else None
        except APIError as e:
            logging.error(f"OpenAI API error during parsing: {e}")
            return None
        except Exception as e:
            logging.error(f"Failed to parse transaction content: {e}")
            return None

    async def get_financial_advice(self, text: str) -> str:
        system_prompt = "You are an experienced and friendly financial advisor. Provide clear, helpful advice."
        try:
            resp = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            return resp.choices[0].message.content or "I can't provide an answer right now."
        except APIError as e:
            logging.error(f"OpenAI API error during advice generation: {e}")
            return "Sorry, I'm having trouble connecting to my knowledge base."
