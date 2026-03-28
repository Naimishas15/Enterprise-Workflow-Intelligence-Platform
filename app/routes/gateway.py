import time
import asyncio
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from app.models.gateway import ChatRequest
from app.services.llm import stream_completion
from app.services.reconciliation import reconcile
import json

router = APIRouter()

@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    if getattr(request.state, "cache_hit", False):
        return JSONResponse(content={
            "id": "cache-hit",
            "object": "chat.completion",
            "cached": True,
            "choices": []
        })

    body_bytes = getattr(request.state, "body_bytes", None)
    if body_bytes:
        body = json.loads(body_bytes)
    else:
        body = await request.json()

    chat_req = ChatRequest(**body)

    tenant_id = request.state.tenant_id
    start_time = time.time()

    async def generate():
        full_response = ""
        input_tokens = 0
        output_tokens = 0

        try:
            response = await stream_completion(
                model=chat_req.model,
                messages=[m.dict() for m in chat_req.messages],
                temperature=chat_req.temperature
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_response += token
                    yield f"data: {json.dumps({'choices': [{'delta': {'content': token}}]})}\n\n"

                if hasattr(chunk, 'usage') and chunk.usage:
                    input_tokens = chunk.usage.prompt_tokens
                    output_tokens = chunk.usage.completion_tokens

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return

        latency_ms = int((time.time() - start_time) * 1000)

        asyncio.create_task(reconcile(
            tenant_id=tenant_id,
            model=chat_req.model,
            input_tokens=input_tokens or 100,
            output_tokens=output_tokens or len(full_response.split()),
            latency_ms=latency_ms,
            query_text=getattr(request.state, "query_text", ""),
            response_text=full_response,
            query_embedding=getattr(request.state, "query_embedding", None),
            cached=False
        ))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"X-Tenant-ID": tenant_id}
    )