import re
import json
import logging
import os
import psycopg2
from openai import OpenAI
from fastapi import FastAPI
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "user": os.getenv("POSTGRES_USER", "searchright"),
    "password": os.getenv("POSTGRES_PASSWORD", "searchright"),
    "database": os.getenv("POSTGRES_DB", "searchright")
}

system_prompt = f"""
    [instruction]
    당신은 채용 전문가로 사람들의 회사, 재직기간, 직무, 기술 스택의 정보를 기반으로 어떤 경험을 하였고, 어떤 역량을 가졌는지 판단하는 역할이 있습니다.
    당신에게 주어지는 data는 3가지 입니다.
    [user_data]는 한 사람의 데이터로서 재직회사, 재직기간, 직무, 기술스택 등이 있습니다.
    [company_data]는 재직회사의 재무정보와 mau, 회사연혁, 매출 등 전반적인 회사정보가 있습니다.
    [company_news_data]는 사람의 회사와 재직기간동안 있었던 뉴스 제목과 링크가 제공될 예정입니다.

    해당 내용을 보고 당신이 [output_format]으로 출력해주시기 바랍니다.
    [output_format]
    해당 키워드는 총 7개로 '상위권대학교', '대규모 회사 경험', '성장기스타트업 경험', '리더쉽', '대용량데이터처리경험', 'M&A 경험', '신규 투자 유치 경험'입니다.
    '상위권 대학교'는 서울에 있는 대학교로서 상위 10%의 대학교를 의미합니다.
    '대규모 회사 경험'은 회사 매출이 1000억 이상인 회사를 의미합니다.
    '성장기스타트업 경험'은 회사의 성장이 어떠한 영역이든지 3배 이상 성장한 경험을 의미합니다.
    '리더쉽'은 책임을 지는 자리에 있는 경험을 의미합니다.
    '대용량데이터처리경험'은 대용량의 데이터를 처리한 경험을 의미합니다.
    'M&A 경험'은 회사가 다른 곳으로 매각한 경험을 의미합니다.
    '신규 투자 유치 경험'은 회사 재직 시절 시리즈 투자를 의미합니다.

    해당 키워드에 해당하지 않는다면 출력을 하지 않아도 됩니다.
    해당 키워드에 해당한다면 [**키워드** : 내용]의 포맷을 유지하되, 내용은 10단어 이하의 한 문장으로 표현해주시기 바랍니다.
"""

@app.get('/')
def read_root(file_path: str = ""):
    if file_path is None:
        return "파일 경로를 입력하시기 바랍니다."
    file_data = load_talent_data(file_path)
    
    if file_data is None:
        return "파일이 없습니다."
    
    connection = connect_to_db()
    companyList = []
    selectedList = []
    companyNewList = []
    
    for position in file_data.get('positions'):
        # (주) 글자 삭제
        companyName = position.get('companyName')
        pattern = r"\((주)\)"
        companyName = re.sub(pattern, "", companyName)

        if companyName == '토스':
            companyName = '비바리퍼블리카'

        if companyName not in selectedList:
            companyData = find_company_data_by_name(connection, companyName)
            companyList.append({
                'name': position.get('companyName'),
                'data': companyData if companyData else '',
                'startEndDate': position.get('startEndDate')
            })

            selectedList.append(position.get('companyName'))

    for companyData in companyList:
        companyId = companyData.get('data')[0]
        startEndDate = companyData.get('startEndDate')

        if companyId and startEndDate:        
            companyNewList.append(
                find_company_news_by_company(connection, companyId, startEndDate)
            )

    
    userData = json.dumps(file_data)
    companyData = json.dumps(companyList)
    companyNewsData = json.dumps(companyNewList, cls=CustomJSONEncoder)

    user_prompt = f"""
        user_data = {userData}
        company_data = {companyData}
        company_news_data = {companyNewsData}
    """

    response = call_openai(system_prompt, user_prompt)
    return response

def connect_to_db():
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn

    except psycopg2.Error as e:
        logging.debug(f"데이터베이스 연결 오류: {e}")
        raise

def find_company_data_by_name(conn, companyName):
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT * FROM company where name = '{companyName}'
                """
            )
            companyData = cursor.fetchone()

            return companyData
    except psycopg2.Error as e:
        logging.debug(f"조회 실패: {e}")
        raise

def find_company_news_by_company(conn, companyId, startEndDate):
    startDate = ''
    endDate = ''
    
    if startEndDate.get('start'):
        startDate = f"{startEndDate.get('start').get('year')}-{startEndDate.get('start').get('month')}-01"
    
    if startEndDate.get('end'):
        endDate = f"{startEndDate.get('end').get('year')}-{startEndDate.get('end').get('month')}-01"
    else:
        # 오늘 날짜를 가져옵니다.
        today = date.today()

        # 원하는 형식으로 포맷팅합니다.
        endDate = today.strftime("%Y-%m-%d")
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT * FROM company_news where company_id = {companyId} and news_date >= '{startDate}' and news_date <= '{endDate}'
                """
            )

            companyNewsData = cursor.fetchall()

            columns = [col.name for col in cursor.description]
            companyNewsData_dict_list = [
                dict(zip(columns, row)) for row in companyNewsData
            ]

            return companyNewsData_dict_list
    except psycopg2.Error as e:
        logging.debug(f"조회 실패: {e}")
        raise

def load_talent_data(file_path):
    try:
        with open(f"example_datas/{file_path}", "r", encoding="utf-8") as file:
            data = json.load(file)

        return data
    except(json.JSONDecodeError, FileNotFoundError) as e:
        return None
    
def call_openai(system_prompt: str, user_data: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

    completion = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_data}
        ]
    )
    return completion.choices[0].message.content

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