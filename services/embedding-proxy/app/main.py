from __future__ import annotations

import os
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException
from openai import AsyncOpenAI, OpenAIError
from pydantic import BaseModel, Field


DEFAULT_MODEL = "text-embedding-3-small"
DEFAULT_DIMENSIONS = 1536
DEFAULT_MAX_INPUTS = 16
DEFAULT_MAX_INPUT_CHARS = 6000

app = FastAPI(title="Embedding Proxy", version="0.1.0")


class EmbeddingRequest(BaseModel):
    input: str | list[str]
    model: str | None = None
    dimensions: int | None = Field(default=None, ge=1)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/embeddings")
@app.post("/v1/embeddings")
async def create_embeddings(
    payload: EmbeddingRequest,
    authorization: Annotated[str | None, Header()] = None,
    x_embedding_proxy_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    require_proxy_auth(authorization, x_embedding_proxy_token)

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    inputs = normalize_inputs(payload.input)
    model = payload.model or os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_MODEL).strip()
    dimensions = payload.dimensions or env_int(
        "OPENAI_EMBEDDING_DIMENSIONS",
        DEFAULT_DIMENSIONS,
    )

    request: dict[str, Any] = {"model": model, "input": inputs}
    if dimensions and model.startswith("text-embedding-3"):
        request["dimensions"] = dimensions

    try:
        response = await AsyncOpenAI(api_key=api_key).embeddings.create(**request)
    except OpenAIError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI embeddings request failed: {exc}") from exc

    embeddings = [item.embedding for item in response.data]
    return {
        "object": "list",
        "model": model,
        "data": [
            {"object": "embedding", "index": index, "embedding": embedding}
            for index, embedding in enumerate(embeddings)
        ],
        "embeddings": embeddings,
    }


def require_proxy_auth(authorization: str | None, header_token: str | None) -> None:
    expected = os.getenv("EMBEDDING_PROXY_TOKEN", "").strip()
    if not expected:
        return

    bearer = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()

    if expected not in {bearer, (header_token or "").strip()}:
        raise HTTPException(status_code=401, detail="Invalid embedding proxy token")


def normalize_inputs(value: str | list[str]) -> list[str]:
    inputs = [value] if isinstance(value, str) else value
    max_inputs = env_int("EMBEDDING_PROXY_MAX_INPUTS", DEFAULT_MAX_INPUTS)
    max_chars = env_int("EMBEDDING_PROXY_MAX_INPUT_CHARS", DEFAULT_MAX_INPUT_CHARS)

    if not inputs:
        raise HTTPException(status_code=400, detail="input must not be empty")
    if len(inputs) > max_inputs:
        raise HTTPException(status_code=400, detail=f"input supports at most {max_inputs} items")

    normalized = []
    for text in inputs:
        if not isinstance(text, str):
            raise HTTPException(status_code=400, detail="input items must be strings")
        normalized.append(" ".join(text.split()).strip()[:max_chars] or "empty")
    return normalized


def env_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default
