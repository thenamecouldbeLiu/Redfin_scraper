import pandas as pd
import requests
import re
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
class RedfinScraper(object):

    def __init__(self, target_pages = ["https://www.redfin.com/CA/Canoga-Park/7615-Glade-Ave-91304/unit-103/home/8097168"]):
        self.target_pages = target_pages
        self.scraped_pages = []
        self.cur_index = 3 #目前爬取第幾項
        self.result ={}
        self.target_file = pd.read_excel("Crawling_Example.xlsx", index_col=0)
        self.final_DF = pd.DataFrame()

        options = webdriver.ChromeOptions()
        prefs = {
            "profile.default_content_setting_values":
                {
                    "notificaitons": 2
                }
        }
        options.add_experimental_option("prefs", prefs)
        options.add_argument("disable-infobars")
        options.add_argument("--mute-audio")
        #options.add_argument('--headless')  # 啟動無頭模式
        #options.add_argument('--disable-gpu')  # windowsd必須加入此行
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)

    def getSearchWord(self):
        #指定搜尋詞

        cur_target = self.target_file.iloc[self.cur_index,0:4]
        search_word = ""
        for i in cur_target:
            #print(i)

            if not pd.isna(i) and i != "#":
                i = str(i)
                search_word += i + " "

        return search_word + "redfin"

    def getGoogleSearch(self):
        search_word = self.getSearchWord()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"}
        google_request = requests.get('https://www.google.com/search?q={}'.format(search_word), headers = headers)
        #self.driver.get('https://www.google.com/search?q={}'.format(search_word))
        first_result_xpath = "//*[@id='rso']/div/div[1]/div/div[1]/a"

        #first_result_url = self.driver.find_element_by_xpath(first_result_xpath)
        #first_result_href = first_result_url.get_attribute('href')
        #self.driver.get(first_result_href)
        return self.driver.current_url

    def page_parser(self, url):

        redfin_request = requests.get(url)
        soup = BeautifulSoup(redfin_request.text, 'html.parser')

        atags = soup.find_all()

        for a in atags:
            print(a.get('href'))

if __name__ == "__main__":
    new_scraper = RedfinScraper()
    print(new_scraper.getSearchWord())
    print(new_scraper.getGoogleResults())