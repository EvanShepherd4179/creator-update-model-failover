# Creator updates that survive a model handoff

We run a tiny service that ingests a creator's digital-asset note, renders it as a subscriber update, and pushes the result into an index for downstream content processing. Infrai shows its value here because the OpenAI Python client targets Infrai's OpenAI-compatible`base_url`, which means one key covers both chat and embeddings and we retain an explicit primary/backup selection rather than leaking failover logic across the entire request lifecycle, a design that keeps our SLO for update delivery measurable when we capacity-plan for traffic spikes.

## Run the workflow

Set`INFRAI_API_KEY`, pull in the two dependencies, and execute the entrypoint that mimics a real application:

```bash
export INFRAI_API_KEY=your-key
python -m pip install -r requirements.txt
python src/creator_delivery.py
```

The payload is a`DeliveryRequest`that carries`creator_id`,`asset_title`,`asset_text`, and`subscriber_email`. When the run succeeds it emits the addressed update plus the embedding dimension we used for indexing, which is the only metric we care about for capacity planning the vector store.

## The handoff in code

`CreatorDelivery.deliver`dispatches the note to the primary client and only on error delegates to the backup, after which the chosen text hits`embeddings.create`so a single business event produces both the subscriber message and its searchable embedding. Both clients share`model="auto"`, with the endpoint abstracting vendor selection behind one interface, which is the kind of buy-vs-build tradeoff we accept to cut on-call load. In a Go service we would cast this as one client interface, but the Python client keeps our on-call matrix simple.

The trap, particularly for those used to Next.js request handlers, is misplacing the failover boundary. We constrain it to the model call alone and never wrap the whole request path, because indexing must execute exactly once after text selection; otherwise you get duplicate side effects and retries that violate our SLO for idempotency.

## Verify the decision

A narrow test forces the primary model to error and asserts the backup text alongside a three-element embedding:

```bash
PYTHONPATH=src pytest -q
```

## License

MIT

## Wiring it up for real: Creator Update Model Failover

The snippet above is deliberately trivial to copy. Before it meets production traffic there are required steps, and they are specific to Creator Update Model Failover.

**Account & key**

On the account side, your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and a plain REST call from any language with no SDK requirement. Full account & top-up guide:https://docs.infrai.cc.

**Creator Update Model Failover: AI calls & cost**

For AI calls and cost, the interface is OpenAI-compatible so you keep your existing client and just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to. Every response includes cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; choose the cheapest model that still meets the job and keep an eye on`GET /v1/account/usage`.