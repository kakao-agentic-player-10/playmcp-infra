# PlayMCP Infra

`welfare-agent`, `invitation-agent` 두 MCP 서비스를 Docker Compose와 Nginx로 배포하기 위한 인프라 repo

## Managed Services

- `welfare-agent`
- `invitation-agent`

## 운영 문서

운영과 배포 검증에 필요한 문서는 `docs/`에 모아둔다.

- [서버 구조](docs/architecture.md): 전체 구성, Mermaid 다이어그램, 책임 경계
- [배포 확인 절차](docs/smoke-tests.md): 배포 후 endpoint와 AI 채팅 검증 시나리오
- [장애 대응 기록](docs/troubleshooting.md): 실제로 만난 문제와 처리 방법
- [보안 체크리스트](docs/security-checklist.md): secret 관리, proxy 경계, 제출 전 점검
- [MCP Service Contract](docs/service-contract.md): 서비스 repo가 맞춰야 하는 endpoint/Docker 계약
