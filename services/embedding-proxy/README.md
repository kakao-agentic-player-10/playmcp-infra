# Embedding Proxy

OpenAI API key를 PlayMCP in KC에 직접 넣을 수 없을 때 사용하는 임베딩 프록시입니다.

`welfare-agent`는 이 프록시에 텍스트를 보내 임베딩 벡터만 받고, OpenAI key는 이 서비스의 런타임 환경변수로만 보관합니다.

## API

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

## Environment

| Key | Required | Description |
|---|---:|---|
| `OPENAI_API_KEY` | yes | OpenAI API key. Never commit this value. |
| `OPENAI_EMBEDDING_MODEL` | no | Default `text-embedding-3-small`. |
| `OPENAI_EMBEDDING_DIMENSIONS` | no | Default `1536`. |
| `EMBEDDING_PROXY_TOKEN` | no | If set, require `Authorization: Bearer ...` or `X-Embedding-Proxy-Token`. |
| `EMBEDDING_PROXY_MAX_INPUTS` | no | Max batch size. Default `16`. |
| `EMBEDDING_PROXY_MAX_INPUT_CHARS` | no | Max chars per input. Default `6000`. |
| `PORT` | no | Default `8080`. |

## Local Run

```bash
cp .env.example .env
# fill OPENAI_API_KEY in .env
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

After deployment, set `welfare-agent` to use:

```text
OPENAI_EMBEDDING_PROXY_URL=https://<proxy-host>/v1/embeddings
```

If the deploy target cannot inject runtime env vars, put only this non-secret proxy URL into the `welfare-agent` image build/default config. Do not put `OPENAI_API_KEY` in `welfare-agent`.
