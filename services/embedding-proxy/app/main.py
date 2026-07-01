from __future__ import annotations

import os
from typing import Annotated, Any

from fastapi import FastAPI, Header, HTTPException
import httpx
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


class KakaoLocalSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=80)
    x: str = ""
    y: str = ""
    radius: int = Field(default=20000, ge=1, le=20000)
    size: int = Field(default=5, ge=1, le=5)


class KakaoAddressSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=120)
    size: int = Field(default=1, ge=1, le=5)


class KakaoCategorySearchRequest(BaseModel):
    category_group_code: str = Field(min_length=1, max_length=10)
    x: float
    y: float
    radius: int = Field(default=2000, ge=1, le=20000)
    sort: str = Field(default="distance", pattern="^(accuracy|distance)$")
    size: int = Field(default=1, ge=1, le=5)


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


@app.post("/v1/kakao/local/search")
async def search_kakao_local(
    payload: KakaoLocalSearchRequest,
    authorization: Annotated[str | None, Header()] = None,
    x_kakao_proxy_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    require_kakao_proxy_auth(authorization, x_kakao_proxy_token)

    api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="KAKAO_REST_API_KEY is not configured")

    params: dict[str, Any] = {"query": " ".join(payload.query.split()), "size": payload.size}
    if payload.x and payload.y:
        params.update({"x": payload.x, "y": payload.y, "radius": payload.radius})

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                "https://dapi.kakao.com/v2/local/search/keyword.json",
                params=params,
                headers={"Authorization": f"KakaoAK {api_key}"},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Kakao Local API returned {exc.response.status_code}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Kakao Local API request failed: {exc}") from exc

    kakao_payload = response.json()
    places = [
        {
            "name": item.get("place_name", ""),
            "category": item.get("category_name", ""),
            "address": item.get("road_address_name") or item.get("address_name", ""),
            "phone": item.get("phone", ""),
            "url": item.get("place_url", ""),
            "x": item.get("x", ""),
            "y": item.get("y", ""),
        }
        for item in kakao_payload.get("documents", [])
    ]
    return {
        "ok": True,
        "places": places,
        "documents": kakao_payload.get("documents", []),
        "meta": kakao_payload.get("meta", {}),
    }


@app.post("/v1/kakao/local/keyword")
async def search_kakao_keyword(
    payload: KakaoLocalSearchRequest,
    authorization: Annotated[str | None, Header()] = None,
    x_kakao_proxy_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    return await search_kakao_local(payload, authorization, x_kakao_proxy_token)


@app.post("/v1/kakao/local/address")
async def search_kakao_address(
    payload: KakaoAddressSearchRequest,
    authorization: Annotated[str | None, Header()] = None,
    x_kakao_proxy_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    require_kakao_proxy_auth(authorization, x_kakao_proxy_token)
    kakao_payload = await kakao_get(
        "/v2/local/search/address.json",
        {"query": " ".join(payload.query.split()), "size": payload.size},
    )
    return {
        "ok": True,
        "documents": kakao_payload.get("documents", []),
        "meta": kakao_payload.get("meta", {}),
    }


@app.post("/v1/kakao/local/category")
async def search_kakao_category(
    payload: KakaoCategorySearchRequest,
    authorization: Annotated[str | None, Header()] = None,
    x_kakao_proxy_token: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    require_kakao_proxy_auth(authorization, x_kakao_proxy_token)
    kakao_payload = await kakao_get(
        "/v2/local/search/category.json",
        {
            "category_group_code": payload.category_group_code,
            "x": payload.x,
            "y": payload.y,
            "radius": payload.radius,
            "sort": payload.sort,
            "size": payload.size,
        },
    )
    return {
        "ok": True,
        "documents": kakao_payload.get("documents", []),
        "meta": kakao_payload.get("meta", {}),
    }


async def kakao_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="KAKAO_REST_API_KEY is not configured")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"https://dapi.kakao.com{path}",
                params=params,
                headers={"Authorization": f"KakaoAK {api_key}"},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Kakao Local API returned {exc.response.status_code}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Kakao Local API request failed: {exc}") from exc
    return response.json()


def require_proxy_auth(authorization: str | None, header_token: str | None) -> None:
    expected = os.getenv("EMBEDDING_PROXY_TOKEN", "").strip()
    if not expected:
        return

    bearer = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()

    if expected not in {bearer, (header_token or "").strip()}:
        raise HTTPException(status_code=401, detail="Invalid embedding proxy token")


def require_kakao_proxy_auth(authorization: str | None, header_token: str | None) -> None:
    expected = os.getenv("KAKAO_PROXY_TOKEN", "").strip()
    if not expected:
        return

    bearer = ""
    if authorization and authorization.lower().startswith("bearer "):
        bearer = authorization[7:].strip()

    if expected not in {bearer, (header_token or "").strip()}:
        raise HTTPException(status_code=401, detail="Invalid Kakao proxy token")


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
