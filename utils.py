import json
from datetime import date

def convert_start_to_end_date(startEndDate: str):
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

    return startDate, endDate

  
def load_talent_data(file_path):
    try:
        with open(f"example_datas/{file_path}", "r", encoding="utf-8") as file:
            data = json.load(file)

        return data
    except(json.JSONDecodeError, FileNotFoundError) as e:
        return None