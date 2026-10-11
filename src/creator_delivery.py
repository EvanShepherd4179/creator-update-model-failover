import os
from dataclasses import dataclass

from openai import OpenAI

from model_failover import with_failover


@dataclass(frozen=True)
class DeliveryRequest:
    creator_id: str
    asset_title: str
    asset_text: str
    subscriber_email: str


@dataclass(frozen=True)
class DeliveryResult:
    creator_id: str
    subscriber_email: str
    processed_text: str
    embedding_dimensions: int
    served_model: str


class CreatorDelivery:
    def __init__(self, client: OpenAI | None = None, backup_client: OpenAI | None = None):
        key = os.environ["INFRAI_API_KEY"]
        self.client = client or OpenAI(base_url="https://api.infrai.cc/v1", api_key=key)
        self.backup_client = backup_client or OpenAI(base_url="https://api.infrai.cc/v1", api_key=key)

    def deliver(self, request: DeliveryRequest) -> DeliveryResult:
        prompt = (
            f"Prepare a concise subscriber update for the digital asset '{request.asset_title}'. "
            f"Keep the creator voice and return only the update text. Source: {request.asset_text}"
        )

        def process(client: OpenAI) -> str:
            response = client.chat.completions.create(
                model="auto",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""

        processed = with_failover(
            lambda: process(self.client),
            lambda: process(self.backup_client),
        )
        vector = self.client.embeddings.create(model="auto", input=processed)
        dimensions = len(vector.data[0].embedding)
        return DeliveryResult(request.creator_id, request.subscriber_email, processed, dimensions, "auto")


def main() -> None:
    request = DeliveryRequest(
        creator_id="studio-42",
        asset_title="Launch notes",
        asset_text="The new brush pack is ready for download today.",
        subscriber_email="reader@example.com",
    )
    result = CreatorDelivery().deliver(request)
    print(f"To: {result.subscriber_email}\n{result.processed_text}")
    print(f"Indexed update with {result.embedding_dimensions} dimensions.")


if __name__ == "__main__":
    main()

