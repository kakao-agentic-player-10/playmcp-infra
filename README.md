# PlayMCP Infra

`welfare-agent`, `invitation-agent` 두 MCP 서비스를 Docker Compose와 Nginx로 배포하기 위한 인프라 repo.

## Managed Services

- `welfare-agent`
- `invitation-agent`

## Directory Layout

세 repo는 같은 상위 폴더에 둔다.

```text
~/study/
├─ welfare-agent/
├─ invitation-agent/
└─ playmcp-infra/
```

서비스 repo는 앱 코드와 Dockerfile만 책임지고, 이 repo는 포트, 배포, 로그, Nginx reverse proxy를 책임진다.

Compose는 각 서비스 repo의 Dockerfile을 build해서 아래 이미지 이름으로 태깅한다.

- `playmcp-welfare-agent:local`
- `playmcp-invitation-agent:local`

## Ownership

서비스 담당자가 책임지는 것:

- 서비스 앱 코드
- 서비스별 `Dockerfile`
- 서비스별 라이브러리/패키지 관리
- 서비스별 환경변수 목록과 `.env.example`
- `/health`, `/mcp` endpoint 구현

인프라 담당자가 책임지는 것:

- 두 서비스 repo를 같은 상위 폴더에 두는 배포 구조
- Docker Compose 실행과 컨테이너 재시작/로그 확인
- 로컬 포트 매핑
- Nginx reverse proxy 라우팅
- VM 배포 시 도메인/HTTPS 연결

실제 API key, 토큰 같은 비밀값은 Dockerfile에 넣지 않고 런타임 환경변수로 주입한다.

## Service Contract

각 서비스 repo는 아래 조건을 맞춰야 한다.

- repo root에 `Dockerfile`을 둔다.
- 컨테이너 내부 포트는 `8000`을 사용한다.
- MCP endpoint는 `/mcp`로 제공한다.
- Health check endpoint는 `/health`로 제공한다.
- MCP transport는 Streamable HTTP 방식을 사용한다.

자세한 규칙은 [docs/service-contract.md](docs/service-contract.md)를 본다.

## Local Setup

```bash
cp env/.env.example .env
./scripts/check.sh
```

`docker compose` 플러그인이 깨진 환경에서도 `docker-compose` standalone 바이너리가 있으면 스크립트가 자동으로 fallback한다.

## Run

```bash
./scripts/compose.sh up -d --build
```

이 명령은 `../welfare-agent/Dockerfile`, `../invitation-agent/Dockerfile`을 각각 build한 뒤 컨테이너를 띄운다.

이미지만 먼저 만들어보고 싶으면:

```bash
./scripts/compose.sh build
docker images | grep playmcp
```

서비스 repo 경로나 이미지 이름을 바꾸고 싶으면 `.env`에서 조정한다.

```env
WELFARE_AGENT_IMAGE=playmcp-welfare-agent:local
INVITATION_AGENT_IMAGE=playmcp-invitation-agent:local
WELFARE_AGENT_CONTEXT=../welfare-agent
INVITATION_AGENT_CONTEXT=../invitation-agent
```

## Health Check

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## MCP Endpoints

Local:

- `http://localhost:8001/mcp`
- `http://localhost:8002/mcp`

Production placeholder:

- `https://welfare.example.com/mcp`
- `https://invitation.example.com/mcp`

## Logs

```bash
./scripts/logs.sh welfare-agent
./scripts/logs.sh invitation-agent
```

최근 로그 라인 수를 바꾸고 싶으면:

```bash
TAIL_LINES=500 ./scripts/logs.sh welfare-agent
```

## Restart

전체 재시작:

```bash
./scripts/restart.sh
```

서비스 하나만 재시작:

```bash
./scripts/restart.sh welfare-agent
./scripts/restart.sh invitation-agent
```

## Deploy

서비스 repo 두 개가 같은 상위 폴더에 준비된 뒤 실행한다.

```bash
./scripts/deploy.sh
```

`deploy.sh`는 각 서비스 repo를 현재 branch 기준으로 `git pull --ff-only` 한 뒤 compose build/up을 실행한다.

## Nginx

실제 VM에서는 도메인을 정한 뒤 아래 파일의 `server_name`을 변경한다.

- `nginx/welfare-agent.conf`
- `nginx/invitation-agent.conf`

적용 예시:

```bash
sudo cp nginx/welfare-agent.conf /etc/nginx/sites-available/welfare-agent
sudo cp nginx/invitation-agent.conf /etc/nginx/sites-available/invitation-agent

sudo ln -s /etc/nginx/sites-available/welfare-agent /etc/nginx/sites-enabled/
sudo ln -s /etc/nginx/sites-available/invitation-agent /etc/nginx/sites-enabled/

sudo nginx -t
sudo systemctl reload nginx
```

HTTPS:

```bash
sudo certbot --nginx \
  -d welfare.example.com \
  -d invitation.example.com
```

## Docker Compose Troubleshooting

현재 Mac에서 `docker compose`가 안 되고 `docker-compose`는 되는 경우:

```bash
docker-compose version
./scripts/compose.sh version
```

Docker daemon 확인:

```bash
docker info
```

`Cannot connect to the Docker daemon`이 나오면 Docker Desktop을 먼저 켠다.
