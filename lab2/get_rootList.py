import os
from selenium import webdriver
import random
from time import sleep

search_path = r'C:\Users\Neo\PycharmProjects\SQA_lab2\resource'
search_name = r'search_list.txt'
chrome_path = r'C:\Users\Neo\PycharmProjects\SQA_lab2\resource'
chrome_name = r'chromedriver.exe'
chrome = webdriver.Chrome(executable_path=os.path.join(chrome_path, chrome_name))
chrome.get('https://www.kanbilibili.com/rank/ups/fans')
chrome.implicitly_wait(15)
name_list = []
for i in range(2, 16):
    sleep(1)
    chrome.find_element_by_xpath(f'//*[@id="app"]/div/div[3]/div[1]/div[1]/a[{i}]').click()
    sleep(1)
    chrome.refresh()
    sleep(1)
    ele = []
    for j in range(1, 101):
        try:
            ele.append(chrome.find_element_by_xpath(f'//*[@id="app"]/div/div[3]/div[2]/a[{j}]/div/div[1]/span[1]'))
        except:
            break
    random.shuffle(ele)
    ele = ele[:10]
    name_list.extend([i.text.strip('\n\t\r ') for i in ele])
with open(file=os.path.join(search_path, search_name), mode='w', encoding='utf8') as f:
    for i, data in enumerate(name_list):
        if data not in name_list[i+1:]:
            # avoid duplication
            f.write(f'{data}\n')
