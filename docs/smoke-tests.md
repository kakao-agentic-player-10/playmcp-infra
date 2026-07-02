# 배포 확인 절차

배포 후에는 아래 순서로 최소 기능을 확인한다.
목표는 전체 기능을 깊게 검증하는 것이 아니라, 데모 직전에 "지금 살아 있는지"를 빠르게 판단하는 것이다.

## 1. Endpoint 확인

### Render API Proxy

```bash
curl -s https://playmcp-embedding-proxy.onrender.com/health
```

정상 응답:

```json
{"ok": true}
```

### PlayMCP in KC

PlayMCP in KC 상세 화면에서 각 endpoint 상태를 확인한다.

| 서비스 | 확인할 내용 |
|---|---|
| welfare-agent | `Active`, tool 목록 표시 |
| invitation-agent | `Active`, tool 목록 표시 |

## 2. Tool 목록 확인

PlayMCP 개발자 콘솔이나 MCP 카드에서 tool 목록을 확인한다.

### welfare-agent

- `save_profile`
- `search_benefits`
- `match_benefits`
- `find_visit_offices`

### invitation-agent

- `fetch_invitation`
- `geocode_address`
- `get_calendar_auth_status`
- `check_calendar_conflict`
- `create_calendar_event`
- `guide_route`

서비스 구현이 바뀌면 tool 이름은 달라질 수 있다. 다만 아래 시나리오를 수행할 수 있어야 한다.

## 3. AI 채팅 테스트

### 복지알리미

#### 청년 지원 정책 추천

입력:

```text
28살 서울 거주 취업준비생인데 받을 수 있는 청년 지원 정책 알려줘
```

기대하는 tool 흐름:

```text
save_profile
search_benefits
match_benefits
```

확인할 내용:

- 나이, 지역, 취업 상태가 프로필에 반영된다.
- 청년/취업 관련 복지 후보가 나온다.
- 최종 답변에 정책명, 요약, 대상, 링크가 포함된다.
- 최종 자격은 기관 기준으로 확인해야 한다는 안내가 포함된다.

#### 방문기관 안내

입력:

```text
주민센터 방문 신청이 필요한 복지 혜택이면 어디로 가야 하는지도 알려줘
```

기대하는 tool 흐름:

```text
find_visit_offices
```

확인할 내용:

- 주민센터 또는 행정복지센터 결과가 나온다.
- 지역별 후보를 너무 많이 나열하지 않는다.
- 방문 전 기관에 확인하라는 안내가 포함된다.

### 캘링크

#### 초대장 정보 추출

입력:

```text
https://small-square.com/sample/02/index.html?v=2 이 청첩장 분석해서 일정 정보를 정리해줘
```

기대하는 tool 흐름:

```text
fetch_invitation
geocode_address
```

확인할 내용:

- 신랑/신부 이름을 추출한다.
- 날짜 `2026-06-24`, 시간 `15:00`을 추출한다.
- 장소와 주소를 추출한다.
- 주소를 좌표로 변환한다.
- `geocode_address`가 일시적으로 실패해도 장소명/주소는 추출되어야 한다.

#### 가까운 역 안내

입력:

```text
https://small-square.com/sample/02/index.html?v=2 결혼식장 주소를 확인하고 가장 가까운 역도 알려줘
```

기대하는 tool 흐름:

```text
fetch_invitation
geocode_address
guide_route
```

확인할 내용:

- Kakao Local 주소 검색으로 좌표를 얻는다.
- `SW8` 카테고리 검색으로 가까운 지하철역을 찾는다.
- 역명, 도보 예상 시간, 카카오맵 링크를 짧게 안내한다.

#### 캘린더 인증 상태

입력:

```text
캘링크 캘린더 인증 상태 확인해줘
```

기대하는 tool 흐름:

```text
get_calendar_auth_status
```

확인할 내용:

- `authenticated: true`가 나온다.
- `token_source`가 `server_store` 또는 요청 헤더 기반 값으로 표시된다.
- 토큰 원문은 응답에 노출되지 않는다.

#### 캘린더 등록

입력:

```text
https://small-square.com/sample/02/index.html?v=2 이 청첩장 분석해서 캘린더에 등록해줘
```

기대하는 tool 흐름:

```text
fetch_invitation
geocode_address
check_calendar_conflict
create_calendar_event
```

확인할 내용:

- PlayMCP OAuth 인증 후 `invitation-agent`의 임시 토큰 저장소로 캘린더 access token을 사용할 수 있다.
- 같은 날짜 일정이 있으면 중복 가능성을 안내한다.
- Kakao Calendar 일정 생성 결과가 나온다.
- `geocode_address`가 일시적으로 실패해도 장소명/주소만으로 등록을 계속할 수 있다.

운영 메모:

- PlayMCP in KC 재배포 후 `/tmp` token store가 비면 캘링크 MCP의 `인증하기`를 다시 진행한다.
- `fetch_invitation`, Kakao Local 검색은 메모리 캐시를 사용하므로 첫 호출보다 반복 호출이 빠를 수 있다.

## 장애 1차 확인

| 증상 | 먼저 볼 곳 |
|---|---|
| `Tool call returned too large content part` | Tool 응답 크기, raw payload 포함 여부 |
| `OPENAI_API_KEY` 누락 | Render env, `OPENAI_EMBEDDING_PROXY_URL` |
| `KAKAO_REST_API_KEY` 누락 | Render env, `KAKAO_LOCAL_PROXY_URL` |
| 캘린더 access token 누락 | PlayMCP OAuth 설정, `get_calendar_auth_status`, 재배포 후 재인증 여부 |
| `geocode_address` timeout | Render proxy 상태, Kakao Local retry/cache, 장소명/주소만으로 등록 지속 여부 |
| Kakao KOE205 | Kakao Developers 동의항목, PlayMCP Client ID |
