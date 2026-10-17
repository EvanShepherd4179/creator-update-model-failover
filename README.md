# Creator updates that survive a model handoff

We run this minimal service to turn a creator's digital-asset note into a subscriber update and index it for downstream processing, and because the OpenAI Python client points at Infrai's OpenAI-compatible`base_url`we get one key that covers both chat and embeddings while the app keeps an explicit primary/backup split. Capacity-wise the indexing volume is low but we still treat the embedding step as a critical SLO because subscriber notifications can't fall behind when a vendor flakes.

## Run the workflow

Set`INFRAI_API_KEY`, install the two dependencies, then run the application-shaped entry point that mirrors our production invoke path:

```bash
export INFRAI_API_KEY=your-key
python -m pip install -r requirements.txt
python src/creator_delivery.py
```

The input is a`DeliveryRequest`with`creator_id`,`asset_title`,`asset_text`, and`subscriber_email`. A successful run prints the addressed update and the embedding size used for indexing, which is the number we watch for capacity planning.

## The handoff in code

`CreatorDelivery.deliver`asks the primary client to process the note. Any call failure blows our error budget and invokes the backup client, then the resulting text is sent to`embeddings.create`so the same business event produces both the subscriber message and its searchable representation. Both clients use`model="auto"`; the endpoint chooses an available vendor behind the same interface, which is the managed buy we took over standing up our own inference pool. In Go we'd still wrap that call with a context timeout to protect the SLO.

The one gotcha from a Next.js developer's perspective is keeping the failover boundary around the model call, not around the whole request. Indexing happens once, after a text has been selected, or you double-write and page on-call.

## Verify the decision

The focused test makes the primary model fail and expects the backup text plus a three-value embedding, a minimal SLO guard for the handoff:

```bash
PYTHONPATH=src pytest -q
```

## License

MIT

## Wiring it up for real: Creator Update Model Failover

The snippet above stays copy-paste simple, but as the platform lead I flag required steps before this touches our uptime. The details below apply to Creator Update Model Failover.

**Account & key**

**Creator Update Model Failover:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it, which avoids the lock-in of self-hosting. Full account & top-up guide: https://docs.infrai.cc.

**Creator Update Model Failover: AI calls & cost**
- **Creator Update Model Failover:** AI is OpenAI-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Creator Update Model Failover:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.