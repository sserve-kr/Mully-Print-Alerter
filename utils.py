import requests
from bs4 import BeautifulSoup
import sqlite3
from settings import target_url
from settings import DB_HOST, DB_NAME, DB_USER, DB_PASS, DB_PORT
import psycopg2 as pg

async def factor_to_link(factors):
    factors = factors.split()
    return f"http://bupyeong.icehs.kr/boardCnts/updateCnt.do?boardID={factors[0]}&viewBoardID={factors[1]}&boardSeq={factors[2]}&lev={factors[3]}&action=view&searchType={factors[4]}&statusYN={factors[5]}&page={factors[6]}"

async def get_news():
    response = requests.get(target_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    subjects_objects = soup.find_all("td", attrs={"data-table": "subject"})
    return [(obj.text.replace("\n", ""), await onclick_to_factorstr(obj.find("a").get('onclick'))) for obj in subjects_objects if '물리' in obj.text]

async def get_files(factors):
    url = await factor_to_link(factors)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    file_list = soup.find("ul", attrs={"class": "list_file"})
    attaches = file_list.find_all("a")
    return [(attach.text, attach.get("href")) for attach in attaches]

async def onclick_to_factorstr(onclick_text):
    return onclick_text.replace('javascript:goView(', '').replace(')', '').replace('\n', '').replace("'", "").replace(', ', ' ').replace(',', ' ')

class DB:
    def __init__(self):
        self.db = pg.connect(
            database=DB_NAME,
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
    
    @staticmethod
    def sql_before(func):
        async def wrapper(self, sqls):
            sqls = [sql.replace('\n', '').lstrip(" ") for sql in sqls.split(';')]
            try:
                sqls.remove('')
            except ValueError:
                pass
            cursor = self.db.cursor()
            return await func(self, sqls, cursor)
        return wrapper

    @sql_before
    async def execute(self, sqls, cursor):
        for command in sqls:
            cursor.execute(command)
        self.db.commit()
        return None
    
    @sql_before
    async def execute_get(self, sqls, cursor):
        for command in sqls:
            cursor.execute(command)
        return cursor.fetchall()