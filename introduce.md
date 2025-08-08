## 목표

> **_회사, 재직기간, 직무(타이틀) 만 존재하는 인재 데이터를 기반으로 LLM 을 활용하여 어떤 경험을 했는지, 어떤 역량을 가지고 있는지 추론하기_**

## 서버 구동 방법

0. poetry 설치

- pyenv install 3.13.0
- poetry env use python3.13

1. poetry install로 package 설치
2. poetry run uvicorn main:app --reload

## 로직

```mermaid
  A[인재 데이터 처리] --> B
  B[인재 데이터 기반 회사 정보 가져오기] --> C
  C[회사 정보 기반하여 재직기간 뉴스 Vector Search] --> D
  D[LLM 호출] --> E
  E[결과 반환]
```

## 모델

gpt-5-mini

## 파일 구조

- **main.py**: 메인 로직 파일
- **llm.py**: llm 관련 로직 파일
- **utils.py**: 기타 공통 함수 파일
- **db.py**: db 연결 및 factory 작업 파일
- **constant.py**: Constant 모여있는 파일

## API 구조

POST /
body
{
file_path: str
}
response

- 성공시: { status: 200, data: response}
- 파일 경로가 누락이 되었을 때 { status: 400, message: "파일 경로를 입력하시기 바랍니다."}
- 파일이 없을 때 { status: 400, "message": "파일이 없습니다."}
