from types import SimpleNamespace

from creator_delivery import CreatorDelivery, DeliveryRequest


class FakeClient:
    def __init__(self, text: str = "update", fail: bool = False):
        self.fail = fail
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create_chat))
        self.embeddings = SimpleNamespace(create=self.create_embedding)
        self.text = text

    def create_chat(self, **_: object):
        if self.fail:
            raise RuntimeError("primary unavailable")
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.text))])

    def create_embedding(self, **_: object):
        return SimpleNamespace(data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])])


def test_delivery_uses_backup_when_primary_processing_fails():
    service = CreatorDelivery(FakeClient(fail=True), FakeClient(text="backup update"))
    result = service.deliver(DeliveryRequest("c1", "Pack", "Ready", "s@example.com"))
    assert result.processed_text == "backup update"
    assert result.embedding_dimensions == 3

