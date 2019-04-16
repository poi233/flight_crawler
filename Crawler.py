# coding=UTF-8
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup
import time
import MySQLdb
import const
import re


class Crawler:
    def __init__(self):
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('headless')
        self.airline_dict = dict()
        self.db_path = 'rm-0xi03qr9vkuhu27bnyo.mysql.rds.aliyuncs.com'
        self.db_username = 'root'
        self.db_password = '************'
        self.db_name = 'flight'
         # self.chrome_options.add_argument('--disable-gpu')
        # self.chrome_options.add_argument("--no-sandbox")

    def get_source(self, url):
        driver = webdriver.Chrome(chrome_options=self.chrome_options)
        driver.get(url)
        # driver.implicitly_wait(2)
        try:
            WebDriverWait(driver, 20, 0.5).until_not(
                EC.visibility_of_element_located((By.CLASS_NAME, "step-loading")))
            WebDriverWait(driver, 20, 0.5).until_not(
                EC.presence_of_element_located((By.CLASS_NAME, "loading-block1")))
        finally:
            response = driver.page_source
            soup = BeautifulSoup(response, "html.parser")
            driver.quit()
            return soup

    def get_flight_count(self, soup):
        one_way = 0
        not_one_way = 0
        lis = soup.select('.list-card > li')
        for li in lis:
            if "flight-info" not in str(li):
                continue
            if "<span class=\"state\">转</span>" in str(li):
                not_one_way += 1
            else:
                one_way += 1
        return one_way, not_one_way

    def get_airline_count(self, soup):
        airlines = soup.find_all("div", class_='flight-plane')
        for i in range(len(airlines)):
            span = airlines[i].find("span")
            airline = str(span.text)[0:re.search('\d', str(span.text)).start()].strip()
            if airline not in self.airline_dict.keys():
                self.airline_dict[airline] = 1
            else:
                self.airline_dict[airline] += 1

    def save_flight_by_file(self, from_city, to_city, one_way, not_one_way, total):
        with open("flight_count", 'a') as f:
            f.write('{},{},{},{},{}\n'.format(from_city, to_city, one_way, not_one_way, total))

    def save_airline_by_file(self, airline_dict):
        pass

    def save_flight_by_db(self, from_city, to_city, one_way, not_one_way, total):
        db = MySQLdb.connect(self.db_path, self.db_username, self.db_password, self.db_name, charset='utf8')
        cursor = db.cursor()
        sql = """INSERT INTO flight_count(from_city,
                 to_city, one_way, not_one_way, total)
                 VALUES ('{}', '{}', {}, '{}', {})""".format(from_city, to_city, one_way, not_one_way, total)
        try:
            cursor.execute(sql)
            db.commit()
        except:
            db.rollback()
        db.close()

    def save_airline_by_db(self):
        db = MySQLdb.connect(self.db_path, self.db_username, self.db_password, self.db_name, charset='utf8')
        cursor = db.cursor()
        for key, value in self.airline_dict.items():
            search_sql = """SELECT * FROM airline_count 
                            WHERE airline_name = \"{}\"""".format(key)
            cursor.execute(search_sql)
            res = cursor.fetchall()
            if len(res) == 0:
                insert_sql = """INSERT INTO airline_count(airline_name,airline_count) 
                                VALUES ('{}', '{}')""".format(key, value)
                try:
                    cursor.execute(insert_sql)
                    db.commit()
                except:
                    db.rollback()
            else:
                count = int(res[0][2]) + value
                update_sql = """UPDATE airline_count SET airline_count = {} WHERE airline_name = \"{}\"""".format(count, key)
                try:
                    cursor.execute(update_sql)
                    db.commit()
                except:
                    db.rollback()
        db.close()

    def check_compete(self, city1, city2=None):
        db = MySQLdb.connect(self.db_path, self.db_username, self.db_password, self.db_name, charset='utf8')
        cursor = db.cursor()
        if city2 is None:
            search_sql = """SELECT * FROM flight_count 
                            WHERE from_city = \"{}\"""".format(city1)
        else:
            search_sql = """SELECT * FROM flight_count 
                            WHERE from_city = \"{}\" AND to_city = \"{}\"""".format(city1, city2)
        cursor.execute(search_sql)
        res = cursor.fetchall()
        if len(res) == 0:
            return False
        elif city2 is None and len(res) != len(const.city_code) - 1:
            return False
        else:
            return True

    def get_all_info(self, from_city, to_city):
        # check if exist
        if self.check_compete(from_city, to_city):
            return
        # abstract data
        one_way = 0
        not_one_way = 0
        count = 0
        for date in const.date:
            url = 'https://m.ctrip.com/html5/flight/swift/international/{}/{}/{}'.format(from_city, to_city, date)
            soup = self.get_source(url)
            _one_way, _not_one_way = self.get_flight_count(soup)
            # print(soup.prettify())
            self.get_airline_count(soup)
            one_way += _one_way
            not_one_way += _not_one_way
            # 均为0认为两城市间无关联
            if count > 1 and one_way == 0 and not_one_way == 0:
                break
            count += 1
            # print('{}, {}, {}, one_way={}, not_one_way={}'.format(from_city, to_city, date, _one_way, _not_one_way))
        # save
        self.save_flight_by_db(from_city, to_city, one_way, not_one_way, one_way + not_one_way)
        self.save_airline_by_db()
        print(from_city, to_city, one_way, not_one_way)
