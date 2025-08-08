import re
import json
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date, datetime
from db import connect_to_db, check_and_add_column, find_company_data_by_name, find_company_news_by_company
from constant import system_prompt
from utils import convert_start_to_end_date, load_talent_data
from llm import call_openai

app = FastAPI()

class TalentPayload(BaseModel):
    file_path: str

@app.post('/')
def post_talent(payload: TalentPayload):
    # 파일 경로 변수 체크
    if payload.file_path is None:
        return "파일 경로를 입력하시기 바랍니다."

    # 인재 데이터 가져오기
    file_data = load_talent_data(payload.file_path)
    if file_data is None:
        return "파일이 없습니다."
    
    # 데이터베이스 연결
    connection = connect_to_db()
    companyList = []
    selectedList = []
    companyNewList = []

    # vector embedding 추가
    check_and_add_column(connection)
    
    # 회사 데이터 가져오기
    for position in file_data.get('positions'):
        # (주) 글자 삭제
        companyName = position.get('companyName')
        pattern = r"\((주)\)"
        companyName = re.sub(pattern, "", companyName)

        # 토스 회사명 변경
        if companyName == '토스':
            companyName = '비바리퍼블리카'

        # 중복 회사 체크
        if companyName not in selectedList:
            companyData = find_company_data_by_name(connection, companyName)
            
            companyList.append({
                'name': position.get('companyName'),
                'data': companyData if companyData else '',
                'startEndDate': position.get('startEndDate'),
                'companyDesc': position.get('description')
            })

            selectedList.append(position.get('companyName'))

    # 회사 뉴스 가져오기 (vector search)
    for companyData in companyList:
        if companyData.get('data') is None or companyData.get('data') == '':
            continue
        
        companyId = companyData.get('data')[0]
        startEndDate = companyData.get('startEndDate')
        companyDesc = companyData.get('companyDesc')

        if companyId and startEndDate:        
            companyNewList.append(
                find_company_news_by_company(connection, companyId, startEndDate, companyDesc)
            )

    userData = json.dumps(file_data)
    companyData = json.dumps(companyList)
    companyNewsData = json.dumps(companyNewList, cls=CustomJSONEncoder)

    # 프롬프트 생성
    user_prompt = f"""
        user_data = {userData}
        company_data = {companyData}
        company_news_data = {companyNewsData}
    """

    # 뉴스 데이터 추출 후 응답 반환
    response = call_openai(system_prompt, user_prompt)
    return response

class CustomJSONEncoder(json.JSONEncoder):
    """
    datetime 객체를 JSON 문자열로 변환하기 위한 커스텀 인코더.
    """
    def default(self, obj):
        # 객체가 datetime.date 또는 datetime.datetime 타입인지 확인
        if isinstance(obj, (date, datetime)):
            # ISO 8601 형식 문자열로 변환
            return obj.isoformat()
        # 다른 타입은 기본 인코더에 맡깁니다.
        return super().default(obj)
    
