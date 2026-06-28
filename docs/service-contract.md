# MCP Service Contract

각 서비스 repo는 아래 규칙을 맞춰야 한다.

## 공통 규칙

- Dockerfile은 각 서비스 repo 루트에 둔다.
- 컨테이너 내부 포트는 반드시 `8000`을 사용한다.
- MCP Endpoint는 `/mcp`로 제공한다.
- Health Check Endpoint는 `/health`로 제공한다.
- 서버는 `0.0.0.0`으로 바인딩한다.
- STDIO 방식이 아니라 Streamable HTTP 방식으로 실행한다.
- 프로세스는 `PORT=8000` 환경변수를 읽을 수 있어야 한다.
- 로그는 stdout/stderr로 출력한다.
- API key, 토큰, 주민번호, 전화번호 등 민감정보를 로그에 남기지 않는다.

## 필수 파일

각 서비스 repo 루트에는 최소한 아래 파일이 있어야 한다.

```text
welfare-agent/
├─ Dockerfile
├─ pyproject.toml
└─ app/
```

```text
invitation-agent/
├─ Dockerfile
├─ pyproject.toml
└─ app/
```

`uv.lock`이나 `requirements.txt`는 서비스별 패키지 관리 방식에 맞춰 추가한다.

## 서비스별 Endpoint

### welfare-agent

Local:
- http://localhost:8001/mcp
- http://localhost:8001/health

Production:
- https://welfare.example.com/mcp
- https://welfare.example.com/health

### invitation-agent

Local:
- http://localhost:8002/mcp
- http://localhost:8002/health

Production:
- https://invitation.example.com/mcp
- https://invitation.example.com/health

## Tool 규칙

- Tool name에 `kakao` 문자열 금지
- Tool name은 영어, 숫자, `_`, `-`만 사용
- Tool description은 영어 중심으로 작성
- annotations 필드 포함
  - title
  - readOnlyHint
  - destructiveHint
  - openWorldHint
  - idempotentHint
- API 원문 그대로 반환 금지
- 응답은 짧고 정제된 text/json으로 반환

## Health Check 규칙

`GET /health`는 외부 API 호출 없이 빠르게 응답해야 한다.

권장 응답:

```json
{
  "status": "ok",
  "service": "welfare-agent"
}
```

서비스 장애 시에는 5xx로 응답한다.

## Infra Repo와의 약속

`playmcp-infra/docker-compose.yml`은 기본적으로 아래 sibling 경로를 build context로 사용한다.

```text
~/study/
├─ welfare-agent/
├─ invitation-agent/
└─ playmcp-infra/
```

경로를 바꿔야 하면 `.env`에 아래 값을 넣는다.

```env
WELFARE_AGENT_CONTEXT=../welfare-agent
INVITATION_AGENT_CONTEXT=../invitation-agent
```

## 로컬 검증 체크리스트

서비스 담당자는 PR/공유 전에 아래를 확인한다.

```bash
docker build -t welfare-agent-test .
docker run --rm -p 8000:8000 welfare-agent-test
curl http://localhost:8000/health
```

인프라 담당자는 두 repo가 준비된 뒤 아래를 실행한다.

```bash
cd ~/study/playmcp-infra
./scripts/check.sh
./scripts/compose.sh up -d --build
curl http://localhost:8001/health
curl http://localhost:8002/health
```
