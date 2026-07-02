# 보안 체크리스트

API key와 사용자 토큰이 코드나 로그에 남지 않도록 하기 위한 기준이다.

## Secret 관리

- 실제 API key, access token, refresh token은 GitHub에 커밋하지 않는다.
- Dockerfile에 secret을 `ENV`로 넣지 않는다.
- README, Notion, 채팅 캡처에 실제 secret을 남기지 않는다.
- 한 번 노출된 key는 재발급하고 이전 key는 폐기한다.
- Render Environment에는 필요한 secret만 저장한다.

## Secret 위치

| Secret | 보관 위치 | 비고 |
|---|---|---|
| `OPENAI_API_KEY` | Render Environment | welfare-agent는 직접 알지 않는다 |
| `KAKAO_REST_API_KEY` | Render Environment, Kakao Developers | Local API proxy에서 사용 |
| Kakao Calendar access token | PlayMCP OAuth runtime, invitation-agent `/tmp` token store | 사용자 동의 후 캘린더 API 호출에만 사용 |

## Proxy 경계

Render API Proxy는 외부 API key를 숨기는 경계다.

허용하는 기능:

- OpenAI 임베딩 요청
- Kakao Local 키워드/주소/카테고리 검색

하지 않는 것:

- secret 반환
- access token 로그 출력
- 임의 URL fetch proxy 역할
- 필요 없는 OpenAI/Kakao endpoint 개방

## 로그 기준

- request body 전체를 운영 로그에 남기지 않는다.
- Authorization header, API key, access token, refresh token은 로그에 남기지 않는다.
- 외부 API 에러는 status code와 짧은 message만 남긴다.
- 초대장 본문, 복지 프로필처럼 개인정보가 섞일 수 있는 원문은 장기 저장하지 않는다.
- 캘링크 OAuth token store는 `/tmp` 기반 임시 저장소로 사용하고, token 값을 tool 응답에 반환하지 않는다.

## 커밋 전 확인

```bash
git diff --cached
```

확인할 것:

- `sk-`, `KakaoAK`, `Bearer`, `access_token`, `refresh_token` 같은 문자열이 실제 값과 함께 들어가지 않았는지 확인한다.
- `.env` 파일이 staged 상태가 아닌지 확인한다.
- 문서에는 placeholder만 넣는다.

권장 placeholder:

```text
OPENAI_API_KEY=<set in Render>
KAKAO_REST_API_KEY=<set in Render>
```

## OAuth 기준

- Kakao Calendar는 사용자별 권한이 필요하므로 고정 key/token 방식으로 운영하지 않는다.
- PlayMCP OAuth로 사용자 동의를 받고, Kakao Calendar API 호출에는 사용자 access token만 사용한다.
- PlayMCP가 tool 호출에 token을 전달하지 않는 경우 `invitation-agent`가 token 교환을 중계하고 `/tmp` token store에 임시 저장한다.
- access token을 DB, GitHub, Dockerfile, 로그에 저장하지 않는다.
- 재배포 후 token store가 비면 사용자가 다시 인증한다.

## 제출 전 점검

- [ ] public repo에 실제 secret이 없다.
- [ ] 노출된 secret은 재발급했다.
- [ ] Render Environment에 필요한 secret이 설정되어 있다.
- [ ] PlayMCP in KC 이미지에는 secret이 포함되어 있지 않다.
- [ ] Tool 응답에 raw external API payload가 과도하게 포함되지 않는다.
- [ ] OAuth token이 로그에 출력되지 않는다.
- [ ] `get_calendar_auth_status`가 token 원문 없이 인증 상태만 반환한다.
- [ ] 팀 문서나 채팅 캡처에도 실제 key가 남아 있지 않다.
