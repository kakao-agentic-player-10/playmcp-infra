# 장애 대응 기록

예선 준비 중 실제로 만난 문제와 처리 방법을 남긴다.
같은 문제가 다시 나왔을 때 원인을 빠르게 좁히는 것이 목적이다.

## 응답 크기 초과

증상:

```text
Tool call returned too large content part.
```

원인:

- MCP tool 응답이 PlayMCP가 처리할 수 있는 크기를 넘었다.
- 외부 페이지 본문, HTML, API 원문을 그대로 반환할 때 자주 발생한다.

처리:

- 외부 API 원문 전체를 반환하지 않는다.
- 다음 tool 호출에 필요한 필드만 남긴다.
- 복지 검색/매칭 결과는 후보 수와 필드 수를 제한한다.
- 초대장 fetch 결과는 일정 추출에 필요한 본문 중심으로 줄인다.

다시 확인할 것:

- raw HTML, raw API payload, 긴 스크립트 텍스트가 응답에 섞이지 않았는지 본다.
- 실제 PlayMCP AI 채팅에서 smoke test를 돌린다.

## OpenAI key 누락

증상:

```json
{"ok":false,"message":"OPENAI_API_KEY가 필요합니다."}
```

원인:

- welfare-agent는 벡터 검색을 위해 사용자 입력을 임베딩해야 한다.
- PlayMCP in KC 배포 화면에서는 런타임 환경변수 주입이 제한적이라 서비스가 OpenAI key를 직접 읽기 어렵다.

처리:

- Render API Proxy를 두고 OpenAI key는 Render Environment에만 저장한다.
- welfare-agent는 `OPENAI_EMBEDDING_PROXY_URL`로 임베딩 요청을 보낸다.

주의:

- Dockerfile, GitHub, README, Notion에 실제 key를 넣지 않는다.
- 이미 노출된 key는 재발급한다.

## Kakao Local key 누락

증상:

```text
KAKAO_REST_API_KEY가 필요합니다.
```

원인:

- 복지알리미의 방문기관 검색과 캘링크의 주소/장소/지하철 검색은 Kakao Local API를 사용한다.
- PlayMCP in KC 환경에서는 Kakao key를 서비스에 직접 넣지 않는다.

처리:

- Render API Proxy에 Kakao Local endpoint를 추가한다.
- `KAKAO_REST_API_KEY`는 Render Environment에만 저장한다.
- 서비스에는 non-secret proxy URL만 넣는다.

주의:

- Kakao REST API key를 서비스 이미지나 문서에 넣지 않는다.
- 프록시는 필요한 Local API endpoint만 열어둔다.

## 캘린더 access token 누락

증상:

```text
캘린더 access token 이 없습니다. PlayMCP가 전달한 토큰(Authorization 헤더)이 필요합니다.
```

원인:

- Kakao Calendar는 사용자별 OAuth access token이 필요하다.
- Kakao REST API key만으로는 특정 사용자의 캘린더를 조회하거나 생성할 수 없다.
- PlayMCP 인증이 꺼져 있거나, OAuth가 끝나지 않았거나, 토큰이 invitation-agent로 전달되지 않은 경우 발생한다.

처리:

- PlayMCP MCP 등록에서 인증 방식을 `OAuth 인증`으로 둔다.
- Kakao Developers에 PlayMCP가 발급한 Redirect URI를 등록한다.
- Kakao Developers 동의항목에서 `talk_calendar`를 켠다.
- PlayMCP에서 `인증하기`를 완료한 뒤 calendar tool을 다시 테스트한다.

우회안:

- PlayMCP와 Kakao OAuth token 교환 방식이 맞지 않으면 `invitation-agent`에 OAuth adapter를 둔다.
- 고정 access token을 Key/Token 인증으로 넣는 방식은 사용자별 캘린더 구조와 맞지 않으므로 운영 방식으로 쓰지 않는다.

## Kakao KOE205

증상:

```text
잘못된 요청 (KOE205)
설정하지 않은 동의 항목: talk_calendar
```

원인:

- PlayMCP OAuth scope에 `talk_calendar`를 넣었지만 Kakao Developers 앱에서 해당 동의항목을 켜지 않았다.
- 또는 PlayMCP에 넣은 Client ID가 동의항목을 설정한 앱의 REST API key와 다르다.

처리:

- Kakao Developers `카카오 로그인 > 동의항목`에서 `talk_calendar`를 선택 동의 또는 필수 동의로 설정한다.
- PlayMCP OAuth `Client ID`가 같은 앱의 REST API key인지 확인한다.

## Kakao 동의 후 PlayMCP 인증 실패

증상:

```text
사용자 인증
인증 과정에서 문제가 발생하여 완료하지 못했습니다.
처음부터 다시 시작해 주세요.
```

원인 추정:

- 카카오 동의 화면까지 갔다면 authorization 요청은 대체로 통과한 상태다.
- 실패 위치는 PlayMCP가 authorization code를 Kakao token endpoint로 교환하는 단계일 가능성이 높다.
- Client Secret 사용 여부, token 요청 방식, redirect_uri 일치 여부를 확인해야 한다.

시도한 것:

- Scope를 `talk_calendar` 하나로 줄여 테스트했다.
- Kakao Developers `카카오 로그인 > 보안`에서 Client Secret 사용/미사용을 각각 테스트했다.
- Client ID/Secret 변경 후 새로 발급된 Redirect URI를 Kakao Developers에 추가했다.

다음 선택지:

- 공식 Discord에 PlayMCP OAuth token exchange 호환성을 문의한다.
- 답이 없거나 일정상 급하면 `invitation-agent` 내부에 OAuth adapter를 추가한다.

## 공통 확인 순서

장애가 나면 아래 순서로 범위를 좁힌다.

1. PlayMCP UI 문제인지, MCP endpoint 문제인지, 외부 API 문제인지 나눈다.
2. PlayMCP in KC 상세 화면에서 endpoint 상태와 tool 목록을 확인한다.
3. Render 로그에서 proxy 요청 성공/실패를 확인한다.
4. Tool 응답이 너무 크거나 민감정보를 과하게 노출하지 않는지 본다.
5. secret 누락이면 repo가 아니라 Render Environment 또는 Kakao OAuth 설정을 확인한다.
