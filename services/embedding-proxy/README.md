# PlayMCP API Proxy

OpenAI/Kakao API key를 PlayMCP in KC에 직접 넣을 수 없을 때 사용하는 API 프록시입니다.

`welfare-agent`는 이 프록시에 텍스트를 보내 임베딩 벡터만 받고, OpenAI key는 이 서비스의 런타임 환경변수로만 보관합니다.
방문기관 검색도 이 프록시를 통해 Kakao Local API를 호출합니다.

## API

### Embeddings

```http
POST /v1/embeddings
POST /embeddings
```

Request:

```json
{
  "model": "text-embedding-3-small",
  "input": ["청년 월세 지원"],
  "dimensions": 1536
}
```

Response:

```json
{
  "object": "list",
  "model": "text-embedding-3-small",
  "data": [
    {"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}
  ],
  "embeddings": [[0.1, 0.2]]
}
```

### Kakao Local Search

```http
POST /v1/kakao/local/search
POST /v1/kakao/local/keyword
POST /v1/kakao/local/address
POST /v1/kakao/local/category
```

Keyword request:

```json
{
  "query": "마포구 주민센터",
  "size": 5
}
```

Address request:

```json
{
  "query": "서울시 영등포구 은행로 30",
  "size": 1
}
```

Category request, e.g. nearest subway:

```json
{
  "category_group_code": "SW8",
  "x": 126.924,
  "y": 37.521,
  "radius": 2000,
  "sort": "distance",
  "size": 1
}
```

Keyword response includes `places` for welfare-agent and raw Kakao `documents` for invitation-agent:

```json
{
  "ok": true,
  "places": [
    {
      "name": "마포구청",
      "category": "공공,사회기관 > 구청",
      "address": "서울 마포구 월드컵로 212",
      "phone": "02-3153-8114",
      "url": "https://place.map.kakao.com/...",
      "x": "126.9013",
      "y": "37.5663"
    }
  ],
  "documents": [],
  "meta": {}
}
```

## Environment

| Key | Required | Description |
|---|---:|---|
| `OPENAI_API_KEY` | yes | OpenAI API key. Never commit this value. |
| `KAKAO_REST_API_KEY` | yes for Kakao search | Kakao REST API key. Never commit this value. |
| `OPENAI_EMBEDDING_MODEL` | no | Default `text-embedding-3-small`. |
| `OPENAI_EMBEDDING_DIMENSIONS` | no | Default `1536`. |
| `EMBEDDING_PROXY_TOKEN` | no | If set, require `Authorization: Bearer ...` or `X-Embedding-Proxy-Token`. |
| `KAKAO_PROXY_TOKEN` | no | If set, require `Authorization: Bearer ...` or `X-Kakao-Proxy-Token`. |
| `EMBEDDING_PROXY_MAX_INPUTS` | no | Max batch size. Default `16`. |
| `EMBEDDING_PROXY_MAX_INPUT_CHARS` | no | Max chars per input. Default `6000`. |
| `PORT` | no | Default `8080`. |

## Local Run

```bash
cp .env.example .env
# fill OPENAI_API_KEY and KAKAO_REST_API_KEY in .env
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

```bash
curl -s http://127.0.0.1:8080/health
```

## Docker

```bash
docker build -t embedding-proxy .
docker run --rm -p 8080:8080 --env-file .env embedding-proxy
```

## Render

Repo root의 `render.yaml`로 Docker Web Service를 생성할 수 있습니다.

Render Dashboard에서 Blueprint 또는 Web Service 생성 시 `playmcp-infra` repo를 연결하고,
`OPENAI_API_KEY`, `KAKAO_REST_API_KEY` 값만 Render 환경변수 화면에 직접 입력합니다. 이 값은 GitHub에 커밋하지 않습니다.

권장 설정:

- Name: `playmcp-embedding-proxy`
- Runtime: Docker
- Root Directory: `services/embedding-proxy`
- Health Check Path: `/health`
- Required secrets: `OPENAI_API_KEY`, `KAKAO_REST_API_KEY`

배포 후 Render가 발급한 HTTPS URL 뒤에 `/v1/embeddings`를 붙여 `welfare-agent`의 proxy URL로 사용합니다.

After deployment, set `welfare-agent` to use:

```text
OPENAI_EMBEDDING_PROXY_URL=https://<proxy-host>/v1/embeddings
KAKAO_LOCAL_PROXY_URL=https://<proxy-host>/v1/kakao/local/search
```

Set `invitation-agent` to use the Kakao Local base path:

```text
KAKAO_LOCAL_PROXY_BASE_URL=https://<proxy-host>/v1/kakao/local
```

If the deploy target cannot inject runtime env vars, put only these non-secret proxy URLs into the `welfare-agent` image build/default config. Do not put `OPENAI_API_KEY` or `KAKAO_REST_API_KEY` in `welfare-agent`.
