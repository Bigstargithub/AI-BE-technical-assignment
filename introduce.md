## 목표

> **_회사, 재직기간, 직무(타이틀) 만 존재하는 인재 데이터를 기반으로 LLM 을 활용하여 어떤 경험을 했는지, 어떤 역량을 가지고 있는지 추론하기_**

---

## 서버 구동 방법

0. poetry 설치

- pyenv install 3.13.0
- poetry env use python3.13

1. poetry install로 package 설치
2. poetry run uvicorn main:app --reload

---

## 로직

```mermaid
  A[인재 데이터 처리] --> B
  B[인재 데이터 기반 회사 정보 가져오기] --> C
  C[회사 정보 기반하여 재직기간 뉴스 Vector Search] --> D
  D[LLM 호출] --> E
  E[결과 반환]
```

---

## 모델

gpt-5-mini

---

## 파일 구조

- **main.py**: 메인 로직 파일 (API 및 전체 흐름)
- **llm.py**: LLM(OpenAI) 호출 관련 로직
- **utils.py**: 공통 유틸 함수 (날짜 변환, 파일 로드 등)
- **db.py**: DB 연결 및 쿼리 함수
- **constant.py**: 시스템 프롬프트 등 상수
- **test_main.py**: 전체 기능 및 유틸 함수 테스트 코드 (pytest 기반)

---

## API 구조

### POST /

- **body**

```json
{
  "file_path": "string"
}
```

- **response**
  - 성공: `{ "status": 200, "data": response }`
  - 파일 경로 누락: `{ "status": 400, "message": "파일 경로를 입력하시기 바랍니다." }`
  - 파일 없음: `{ "status": 500, "message": "파일이 없습니다." }`

---

## 테스트 코드 및 실행 방법

### 테스트 프레임워크

- **pytest** 사용
- 모든 주요 로직(main API, utils 함수 등)을 test_main.py에서 통합 관리

### 테스트 실행 방법

1. poetry 환경에서 아래 명령어 실행
   ```bash
   poetry run pytest
   ```
   또는 가상환경 진입 후
   ```bash
   pytest
   ```
2. 테스트 결과가 터미널에 출력됨 (성공/실패 여부 확인)

### 주요 테스트 케이스

- **API 정상 동작**: 올바른 파일 경로 입력 시 성공 응답
- **API 예외 처리**: 파일 경로 누락, 파일 없음 등 예외 상황 응답
- **utils 함수**: 날짜 변환, 파일 로드 정상/비정상 케이스

### 참고

- 테스트는 test_main.py 한 파일에서 모두 관리
- 외부 의존성(DB, LLM 등)은 mock 처리하여 테스트의 독립성 보장

---
