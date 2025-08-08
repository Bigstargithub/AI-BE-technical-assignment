import logging
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from constant import DB_CONFIG
from sentence_transformers import SentenceTransformer
from utils import convert_start_to_end_date

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

def check_and_add_column(conn):
    cursor = conn.cursor()

    query = """
        SELECT EXISTS(
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'company_news' and column_name = 'embedding_column'
        )
    """

    cursor.execute(query)
    column_exists = cursor.fetchone()[0]

    if not column_exists:
        create_extension_query = """
            CREATE EXTENSION IF NOT EXISTS vector;
        """
        cursor.execute(create_extension_query)

        alter_query = """
            ALTER TABLE
            company_news
            ADD COLUMN embedding_column VECTOR(768)
        """
        cursor.execute(alter_query)
        conn.commit()

        select_query = """
            SELECT id, title FROM company_news WHERE embedding_column IS NULL
        """

        cursor.execute(select_query)
        rows = cursor.fetchall()

        model = SentenceTransformer('jhgan/ko-sbert-nli')
        for row in rows:
            id, title = row
            
            embedding = model.encode(title)
            embedding_list = embedding.tolist()
            update_query = "UPDATE company_news SET embedding_column = %s WHERE id = %s;"
            cursor.execute(update_query, (embedding_list, id))
        
        conn.commit()

    else:
        cursor.close()

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



def find_company_news_by_company(conn, companyId, startEndDate, companyDesc):
    startDate, endDate = convert_start_to_end_date(startEndDate)

    model = SentenceTransformer('jhgan/ko-sbert-nli')
    companyDescVector = model.encode(companyDesc)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                    SELECT title, original_link FROM company_news where company_id = {companyId} and news_date >= '{startDate}' and news_date <= '{endDate}' order by embedding_column <=> '{companyDescVector.tolist()}' LIMIT 10
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