import pandas as pd
from bs4 import BeautifulSoup
from collections import deque
import re
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
#from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException
import time

class IndividualScraperResult(object):
    def __init__(self, **kwargs):
        self.individual_result ={}

        for k,v in kwargs.items():
            self.individual_result[k] = v


    def getResult(self):
        return self.individual_result


class RedfinScraper(object):

    def __init__(self, target_pages = ["https://www.redfin.com/CA/Canoga-Park/7615-Glade-Ave-91304/unit-103/home/8097168"]):
        self.target_pages = target_pages
        self.scraped_pages = []
        self.cur_index = 1 #目前爬取第幾項
        self.result ={}
        self.target_file = pd.read_excel("Crawling_Example.xlsx", index_col=0)
        self.main_DF = pd.DataFrame()
        self.price_history = []

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
        options.add_argument('--headless')  # 啟動無頭模式
        options.add_argument('--disable-gpu')  # windowsd必須加入此行
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        #self.driver.set_page_load_timeout(15)
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

        # 注释这两行会导致最后输出结果的延迟，即等待页面加载完成再输出
        desired_capabilities = DesiredCapabilities.CHROME  # 修改页面加载策略页面加载策略
        desired_capabilities[
            "pageLoadStrategy"] = "none"  # none表示将browser操作方法改为非阻塞模式，在页面加载过程中也可以给browser发送指令，如获取url，pagesource等资源，get新的url等。

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

    """    考慮測試用BS4爬 但有點麻煩
    def getGoogleSearchBS4(self):
        search_word = self.getSearchWord()
        soup = BeautifulSoup('https://www.google.com/search?q={}'.format(search_word), 'html.parser')
        result_link = soup.find_all("herf")
        
    """


    def getGoogleSearch(self):
        search_word = self.getSearchWord()
        self.driver.get('https://www.google.com/search?q={}'.format(search_word))
        first_result_xpath = "//*[@id='rso']/div/div[1]/div/div[1]/a"
        first_result_url = self.driver.find_element_by_xpath(first_result_xpath)
        first_result_href = first_result_url.get_attribute('href')
        self.driver.get(first_result_href)

    def clean_number(self, value):
        #清除多餘符號
        cleaned_val = ""
        for t in value:
            # 取到括號前
            if t == "(":
                break
            else:
                if t.isnumeric():
                    cleaned_val += t
                else:
                    continue
        if cleaned_val.isnumeric():
            return int(cleaned_val)
        else:
            return "-"


    def getMainElements(self):

        #time.sleep(3)

        elements_results = {}
        #URL
        elements_results["redfin_url"] = self.driver.current_url
        print("current scraping "+self.driver.current_url)

        """Basic"""
        #print("into basic")
        basic_fact_val = self.driver.find_elements_by_css_selector(".statsValue")
        basic_fact_label = self.driver.find_elements_by_css_selector(".statsLabel.font-size-small")
        for i in range(len(basic_fact_label)):
            print(basic_fact_label[i].text, basic_fact_val[i].text)
            elements_results[basic_fact_label[i].text] = basic_fact_val[i].text


        #Sold_price
        #按按鈕
        try:
            history_expand = self.driver.find_element_by_xpath("//*[@id='propertyHistory-expandable-segment']/div[2]/div/span")
            history_expand.click()
        except NoSuchElementException:
            pass

        last_sold_price_origin = self.driver.find_elements_by_css_selector(".row.PropertyHistoryEventRow")
        last_price_flag = False
        for origin in last_sold_price_origin:
            last_sold_price_origin_date = origin.find_element_by_css_selector(
                ".col-4>p").text
            last_sold_price_origin_description = origin.find_element_by_css_selector(".description-col.col-4").text
            last_sold_price_origin_price = origin.find_element_by_css_selector(".price-col.number").text
            sold_price_data = (self.driver.current_url, last_sold_price_origin_date, last_sold_price_origin_description, last_sold_price_origin_price)
            self.price_history.append(sold_price_data)
            if type(last_sold_price_origin_price) == int and not last_price_flag:
                #紀錄最後一筆價格
                elements_results["Last_sold_price"] = last_sold_price_origin_price
                last_price_flag = True


        #rental
        rental = self.driver.find_element_by_css_selector(".value-block.font-size-medium > span")
        rental_text = rental.text.split(" - ")
        upper_rental = rental_text[1]
        lower_rental = rental_text[0]

        elements_results["Rental_Rental_Lower_Bound"] = lower_rental
        elements_results["Rental_Rental_Upper_Bound"] = upper_rental

        #about this home
        try:
            about_this_home = self.driver.find_element_by_css_selector(".remarks#marketing-remarks-scroll")

            final_text = about_this_home.find_element_by_css_selector(".text-base").text
        except NoSuchElementException:
            about_this_home = self.driver.find_element_by_css_selector(".clear-fix.descriptive-paragraph")
            about_this_home_text = about_this_home.find_elements_by_css_selector("span")
            final_text = ""
            for t in about_this_home_text:
                final_text += t.text

        elements_results["About_this_home"] = final_text

        #Brokerage_Compensation
        try:
            Brokerage_Compensation = self.driver.find_element_by_xpath("// *[ @ id = 'house-info'] / div / "
                                                                       "div / div[4] / div[3] / span[2]").text
            elements_results["Brokerage_Compensation"] = Brokerage_Compensation
        except NoSuchElementException as e:
            pass


        #home_facts
        try:
            home_facts_list = self.driver.find_element_by_xpath("//*[@id='house-info']/div/div/div[6]")
            home_fact_label = home_facts_list.find_elements_by_css_selector(
                ".keyDetailsList .header.font-color-gray-light.inline-block")
            home_fact_val = home_facts_list.find_elements_by_css_selector(
                ".keyDetailsList .content.text-right")
            for i in range(1, len(home_fact_label)):
                elements_results[home_fact_label[i].text] = home_fact_val[i].text


        except NoSuchElementException:
            pass

        #public facts
        try:
            public_facts_list = self.driver.find_element_by_xpath("//*[@id='basicInfo']/div[2]/div[1]")
            public_fact_label = public_facts_list.find_elements_by_css_selector(
                ".table-label")
            public_fact_val = public_facts_list.find_elements_by_css_selector(
                ".table-value")
            for i in range(len(public_fact_label)):
                if elements_results.get('Lot Size') and public_fact_label[i].text =="Lot Size":

                    elements_results['Lot Size 2'] = public_fact_val[i].text
                else:

                    elements_results[public_fact_label[i].text] = public_fact_val[i].text

        except NoSuchElementException:
            pass

        #activitys
        try:
            activity_table = self.driver.find_element_by_css_selector(".activityStatsTable")
            activity_upper = activity_table.find_elements_by_css_selector(".upperLabel")
            activity_button = activity_table.find_elements_by_css_selector(".bottomLabel")


            for uc in range(len(activity_upper)):
                activity_upper_count = activity_upper[uc].find_element_by_css_selector(".count").text
                activity_upper_label = activity_upper[uc].find_element_by_css_selector(
                    ".DefinitionFlyoutLink.inline-block.underline.clickable").text
                elements_results[activity_upper_label] = activity_upper_count

            lower_prefix = ["Favorites", "X-Outs", "Redfin Tours"]
            prefix_counter = 0
            for bc in range(len(activity_button)):
                activity_button_count = activity_button[bc].find_element_by_css_selector(".count").text
                activity_button_label = activity_button[bc].find_element_by_css_selector(
                    ".DefinitionFlyoutLink.inline-block.underline.clickable").text
                if activity_button_label == "all-time":
                    #print("cur_lower label", activity_button_label)
                    cur_prefix = lower_prefix[prefix_counter]
                    elements_results[cur_prefix + "_" + activity_button_label] = activity_button_count
                    prefix_counter += 1
                else:
                    elements_results[activity_button_label] = activity_button_count
        except:
            pass

        #flood risk
        try:
            flood_preview = self.driver.find_element_by_class_name("floodPreview")
            flood_factor = flood_preview.find_element_by_class_name("padding-bottom-smaller").text
            for f in range(len(flood_factor)):
                if flood_factor[f] =="(":
                    elements_results["Flood_Factor"] = flood_factor[f+1]
                    break
        except NoSuchElementException:
            elements_results["Flood_Factor"] = None

        #transportation scores
        try:
            first_score = self.driver.find_element_by_xpath("//*[@id='neighborhoodInfo-collapsible']/div[2]/div/div/div[3]/div[1]/div/div[1]/div[1]/div/span[1]").text
            first_label = self.driver.find_element_by_xpath("//*[@id='neighborhoodInfo-collapsible']/div[2]/div/div/div[3]/div[1]/div/div[1]/div[2]/div[2]").text[:-1]
            elements_results[first_label] = first_score

        except NoSuchElementException:
            pass

        try:
            second_score =self.driver.find_element_by_xpath("//*[@id='neighborhoodInfo-collapsible']/div[2]/div/div/div[3]/div[1]/div/div[2]/div[1]/div/span[1]").text
            second_label = self.driver.find_element_by_xpath("//*[@id='neighborhoodInfo-collapsible']/div[2]/div/div/div[3]/div[1]/div/div[2]/div[2]/div[2]").text[:-1]
            elements_results[second_label] = second_score

        except NoSuchElementException:
            pass

        try:
            third_score = self.driver.find_element_by_xpath("//*[@id='neighborhoodInfo-collapsible']/div[2]/div/div/div[3]/div[1]/div/div[3]/div[1]/div/span[1]").text
            third_label = self.driver.find_element_by_xpath("//*[@id='neighborhoodInfo-collapsible']/div[2]/div/div/div[3]/div[1]/div/div[3]/div[2]/div[2]").text[:-1]
            elements_results[third_label] = third_score

        except NoSuchElementException:
            pass




        return elements_results

    def scrapedUrlReader(self, file="scraped.txt"):
        try:
            with open(file, "r") as pages:
                self.scraped_pages = pages.readlines()
                for i in range(len(self.scraped_pages)):
                    self.scraped_pages[i] = self.scraped_pages[i].strip("\n")

        except:
            new_scraped_file = open(file, "w")
            new_scraped_file.close()

    def run(self):

        file_len = self.target_file.shape[0]
        for item in range(1,file_len):
            self.cur_index = item
            self.getGoogleSearch()
            print(new_scraper.getMainElements().items())

        #print(self.price_history)

if __name__ == "__main__":

    new_scraper = RedfinScraper()
    #print(new_scraper.target_file.shape)
    #print(new_scraper.getSearchWord())
    #new_scraper.getGoogleSearch()
    #time.sleep(2)
    try:
        start = time.perf_counter()

        new_scraper.run()
        new_scraper.driver.quit()

        end = time.perf_counter()
        print(start-end)
    except Exception as e:
        import sys
        import traceback
        import test
        #    print(e)
        error_class = e.__class__.__name__  # 取得錯誤類型
        detail = e.args[0]  # 取得詳細內容
        cl, exc, tb = sys.exc_info()  # 取得Call Stack
        lastCallStack = traceback.extract_tb(tb)[-1]  # 取得Call Stack的最後一筆資料
        fileName = lastCallStack[0]  # 取得發生的檔案名稱
        lineNum = lastCallStack[1]  # 取得發生的行號
        funcName = lastCallStack[2]  # 取得發生的函數名稱
        errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
        print(errMsg)

        new_scraper.driver.quit()