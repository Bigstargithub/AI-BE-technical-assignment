import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

# 정상 케이스: 파일 경로가 주어지고 모든 의존성 함수가 정상 동작할 때
@patch('main.load_talent_data')
@patch('main.connect_to_db')
@patch('main.check_and_add_column')
@patch('main.find_company_data_by_name')
@patch('main.find_company_news_by_company')
@patch('main.call_openai')
def test_post_talent_success(mock_call_openai, mock_find_company_news_by_company, mock_find_company_data_by_name, mock_check_and_add_column, mock_connect_to_db, mock_load_talent_data):
    # Mock 데이터 준비
    mock_load_talent_data.return_value = {
        'positions': [
            {
                'companyName': '토스',
                'startEndDate': '2020-01 ~ 2021-01',
                'description': '테스트 설명'
            }
        ]
    }
    mock_connect_to_db.return_value = MagicMock()
    mock_check_and_add_column.return_value = None
    mock_find_company_data_by_name.return_value = [1, '비바리퍼블리카', '기타정보']
    mock_find_company_news_by_company.return_value = {'news': '뉴스내용'}
    mock_call_openai.return_value = {'result': 'ok'}

    response = client.post('/', json={'file_path': 'dummy.json'})
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 200
    assert data['message'] == 'success'
    assert 'data' in data

# 비정상 케이스: file_path가 None일 때
def test_post_talent_no_file_path():
    response = client.post('/', json={'file_path': None})
    assert response.status_code == 422

# 비정상 케이스: load_talent_data가 None을 반환할 때
@patch('main.load_talent_data')
def test_post_talent_file_not_found(mock_load_talent_data):
    mock_load_talent_data.return_value = None
    response = client.post('/', json={'file_path': 'not_exist.json'})
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 500
    assert data['message'] == '파일이 없습니다.'

# ---------------------- utils.py 테스트 ----------------------
import os
import json
from datetime import date
from utils import convert_start_to_end_date, load_talent_data

def test_convert_start_to_end_date_full():
    startEndDate = {
        'start': {'year': 2020, 'month': 1},
        'end': {'year': 2021, 'month': 2}
    }
    start, end = convert_start_to_end_date(startEndDate)
    assert start == '2020-1-01'
    assert end == '2021-2-01'

def test_convert_start_to_end_date_no_end():
    today = date.today().strftime('%Y-%m-%d')
    startEndDate = {
        'start': {'year': 2020, 'month': 1},
        'end': None
    }
    start, end = convert_start_to_end_date(startEndDate)
    assert start == '2020-1-01'
    assert end == today

def test_convert_start_to_end_date_no_start():
    startEndDate = {
        'start': None,
        'end': {'year': 2021, 'month': 2}
    }
    start, end = convert_start_to_end_date(startEndDate)
    assert start == ''
    assert end == '2021-2-01'

def test_load_talent_data_success(tmp_path):
    file_content = {"positions": [{"companyName": "테스트"}]}
    file_name = 'test_talent.json'
    file_path = tmp_path / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(file_content, f, ensure_ascii=False)
    os.makedirs('example_datas', exist_ok=True)
    os.rename(file_path, f'example_datas/{file_name}')
    data = load_talent_data(file_name)
    assert data == file_content
    os.remove(f'example_datas/{file_name}')

def test_load_talent_data_file_not_found():
    data = load_talent_data('not_exist.json')
    assert data is None

def test_load_talent_data_invalid_json(tmp_path):
    file_name = 'invalid.json'
    file_path = tmp_path / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('{invalid json}')
    os.makedirs('example_datas', exist_ok=True)
    os.rename(file_path, f'example_datas/{file_name}')
    data = load_talent_data(file_name)
    assert data is None
    os.remove(f'example_datas/{file_name}')
