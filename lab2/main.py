import gensim
import numpy as np
from bs4 import BeautifulSoup
import os
from selenium import webdriver
import jieba
from time import time as t
from time import sleep
from selenium.webdriver.chrome.options import Options
import time
import json
import random
import requests
import re


def read(file_name):
    with open(file_name, encoding='utf8') as f:
        return [i.strip('\n\r\t ') for i in f]


def out(relation):
    with open(os.path.join(outputPath, outputName), mode='w', encoding='utf8') as f:
        f.write('Index,bilibili,weibo,zhihu,wx,douban,ximalaya\n')
        for i, each in enumerate(relation):
            try:
                f.write(
                    f'{i},{each.bili},{each.weibo},{each.zhihu},{each.wx[0] if isinstance(each.wx, list) else each.wx},{each.douban},{each.xima}\n')
            except:
                continue


def load_list(file_name):
    list_of_user = []
    try:
        with open(file_name, mode='r', encoding='utf8') as f:
            next(f)
            for line in f:
                list_of_url = line.strip('\n\r').split(',')[1:]
                newU = User()
                newU.bili = list_of_url[0]
                newU.has |= BILIBILI if newU.bili != newU.default else 0
                newU.weibo = list_of_url[1]
                newU.has |= WEIBO if newU.weibo != newU.default else 0
                newU.zhihu = list_of_url[2]
                newU.has |= ZHIHU if newU.zhihu != newU.default else 0
                newU.wx = list_of_url[3]
                newU.has |= WEIXIN if newU.wx != newU.default else 0
                newU.douban = list_of_url[4]
                newU.has |= DOUBAN if newU.douban != newU.default else 0
                newU.xima = list_of_url[5]
                newU.has |= XIMA if newU.xima != newU.default else 0
                list_of_user.append(newU)
        return list_of_user

    except:
        return list_of_user


# global vars && parameters here
BILIBILI = 1
WEIBO = 2
ZHIHU = 4
WEIXIN = 8
DOUBAN = 16
XIMA = 32

WAIT_TIME = 2
LONG_WAIT_TIME = 15
threshold = 0.85  # when similarity >= threshold, 2 urls are considered relative.
'''
modify all these absolute paths to the according paths on your machine.
'''
stopwds_path = r'C:\Users\Neo\PycharmProjects\SQA_lab2\static'
stopwds_name = r'stopwords.txt'
# stopwords list
wordvec_path = r'C:\Users\Neo\PycharmProjects\SQA_lab2\static'
wordvec_name = r'sgns.sogou.word'
# pretrained word vector
# dimension of word vector default to 300
search_path = r'C:\Users\Neo\PycharmProjects\SQA_lab2\static'
search_name = r'search_list.txt'
chrome_path = r'C:\Users\Neo\PycharmProjects\SQA_lab2\static'
chrome_name = r'chromedriver.exe'
outputPath = r'C:\Users\Neo\PycharmProjects\SQA_lab2\static'
outputName = r'output.csv'
wechat_account = "***"
wechat_password = "***"
# 一个能够登陆入微信公众号平台的账号的邮箱和密码。不要用微信小程序的号！
zhihu_account = "***"
zhihu_password = "***"
# 一个能够登陆入知乎的账号和密码。 不是手机验证的免密登录，而是账号和密码！
weixin_url = 'https://mp.weixin.qq.com/'
cookie_path = r'C:\Users\Neo\PycharmProjects\SQA_lab2\static'
cookie_name = r'cookie.txt'
# f'store cookie from {weixin_url}'
search_list = read(os.path.join(search_path, search_name))
start = 0
# crawling from the start-th name
limit = 30


# number of users crawled once


# an entity in real world is represented by an object of user.
class User:
    def __init__(self):
        self.default = '\\'
        self.bili = self.default
        self.weibo = self.default
        self.zhihu = self.default
        self.wx = self.default
        self.douban = self.default
        self.xima = self.default
        self.has = 0

    def add(self, what):
        if what['ptype'] == BILIBILI:
            self.bili = what['url'] if not self.has & BILIBILI else self.bili
            self.has = self.has | BILIBILI if self.bili == what['url'] else self.has
            return self.bili == what['url']
        elif what['ptype'] == WEIBO:
            self.weibo = what['url'] if not self.has & WEIBO else self.weibo
            self.has = self.has | WEIBO if self.weibo == what['url'] else self.has
            return self.weibo == what['url']
        elif what['ptype'] == ZHIHU:
            self.zhihu = what['url'] if not self.has & ZHIHU else self.zhihu
            self.has = self.has | ZHIHU if self.zhihu == what['url'] else self.has
            return self.zhihu == what['url']
        elif what['ptype'] == WEIXIN:
            self.wx = what['url'] if not self.has & WEIXIN else self.wx
            self.has = self.has | WEIXIN if self.wx == what['url'] else self.has
            return self.wx == what['url']
        elif what['ptype'] == DOUBAN:
            self.douban = what['url'] if not self.has & DOUBAN else self.douban
            self.has = self.has | DOUBAN if self.douban == what['url'] else self.has
            return self.douban == what['url']
        elif what['ptype'] == XIMA:
            self.xima = what['url'] if not self.has & XIMA else self.xima
            self.has = self.has | XIMA if self.xima == what['url'] else self.has
            return self.xima == what['url']
        else:
            print('Wrong ptype of parameter in user.add')
            return False

    def __str__(self):
        return f'Bilibili: {self.bili} ' \
               f'\tWeibo: {self.weibo}' \
               f'\tZhihu: {self.zhihu}' \
               f'\tWeixin: {self.wx}' \
               f'\tDouban: {self.douban}' \
               f'\tXima: {self.xima}' \
               f'\n Found!'

    def isEmpty(self):
        return self.bili == self.default and self.weibo == self.default and self.wx == self.default and self.zhihu == self.default and self.douban == self.default and self.xima == self.default


relation_list = load_list(os.path.join(outputPath, outputName))  # list of instances of user


# handling similar but subtly differentiated operations between platforms
# tool class, singleton.
class PlatformHandler:
    url = None
    ptype = None
    name = None
    timeout = 30
    where_is_chrome = None
    zhihu_chrome = None
    other_chrome = None
    wechat_chrome = None
    wechat_cookie = None

    def __init__(self):
        PlatformHandler.where_is_chrome = os.path.join(chrome_path, chrome_name)
        PlatformHandler.other_chrome = webdriver.Chrome(executable_path=PlatformHandler.where_is_chrome)
        PlatformHandler.wechat_chrome = webdriver.Chrome(executable_path=PlatformHandler.where_is_chrome)
        driver_options = Options()
        driver_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        PlatformHandler.zhihu_chrome = webdriver.Chrome(executable_path=PlatformHandler.where_is_chrome,
                                                        options=driver_options)
        PlatformHandler.wechat_cookie = os.path.join(cookie_path, cookie_name)
        self.wechat_login()
        self.wechat_cookies()

    def reset(self, u, t=None, n=None):
        PlatformHandler.url = u
        PlatformHandler.ptype = t
        PlatformHandler.name = n
        return self

    def wechat_login(self):
        driver = PlatformHandler.wechat_chrome
        driver.get(weixin_url)
        driver.maximize_window()
        time.sleep(WAIT_TIME)

        # if the website uses QR code login modes
        img_xpath = "//*[@id='header']/div[2]/div/div/div[2]/img"
        if driver.find_element_by_xpath(img_xpath):
            switch_mode_xpath = "//*[@id='header']/div[2]/div/div/div[2]/a"
            driver.find_element_by_xpath(switch_mode_xpath).click()

        # input account number and password
        print("Inputing information...")
        # XPath from html
        user_account_xpath = "//*[@id='header']/div[2]/div/div/div[1]/form/div[1]/div[1]/div/span/input"
        user_password_xpath = "//*[@id='header']/div[2]/div/div/div[1]/form/div[1]/div[2]/div/span/input"
        # set account and password
        driver.find_element_by_xpath(user_account_xpath).clear()
        driver.find_element_by_xpath(user_account_xpath).send_keys(wechat_account)
        driver.find_element_by_xpath(user_password_xpath).clear()
        driver.find_element_by_xpath(user_password_xpath).send_keys(wechat_password)

        # remember me
        # XPath from html
        remember_me_xpath = "//*[@id='header']/div[2]/div/div/div[1]/form/div[3]/label"
        driver.find_element_by_xpath(remember_me_xpath).click()

        # login
        login_xpath = "//*[@id='header']/div[2]/div/div/div[1]/form/div[4]/a"
        driver.find_element_by_xpath(login_xpath).click()
        time.sleep(WAIT_TIME)

        print("Please scan the QR code using your phone in 15 seconds.")
        time.sleep(LONG_WAIT_TIME)

        try:
            first_page_xpath = "//*[@id='menuBar']/li[1]/a/span/span"
            driver.find_element_by_xpath(first_page_xpath).click()
            time.sleep(WAIT_TIME)
        except:
            print("Exception: login failure!")
            self.wechat_login()

    def wechat_cookies(self):
        driver = PlatformHandler.wechat_chrome
        post = {}
        # relogin this website
        driver.get('https://mp.weixin.qq.com/')
        # get cookies
        cookie_items = driver.get_cookies()
        # the cookies is a list
        # we change it into json and save it
        for cookie_item in cookie_items:
            post[cookie_item['name']] = cookie_item['value']
        cookie_str = json.dumps(post)
        with open(PlatformHandler.wechat_cookie, 'w+', encoding='utf-8') as f:
            f.write(cookie_str)

    def url2string_bilibili(self):
        string_list = []
        content_list = []
        for each in PlatformHandler.url:
            chrome = PlatformHandler.other_chrome
            chrome.implicitly_wait(15)
            chrome.get(each)
            sleep(3)
            chrome.refresh()
            start = t()
            while not len(content_list):
                try:
                    content_list = [i.text for i in chrome.find_elements_by_class_name('content-full')]
                    if not len(content_list):
                        content_list = [i.text for i in chrome.find_elements_by_class_name('video-wrap')]
                        # some users only post videos without adding any description
                    if t() - start > PlatformHandler.timeout:
                        break
                except:
                    break
            if len(content_list):
                content_list = content_list[:10] if len(content_list) > 10 else content_list
                string_list.append("".join(content_list))
            content_list.clear()
        return string_list

    def url2string_weibo(self):
        string_list = []
        content_list = []
        start = t()
        for each in PlatformHandler.url:
            chrome = PlatformHandler.other_chrome
            chrome.implicitly_wait(15)
            chrome.get(each)
            sleep(3)
            chrome.refresh()
            while not len(content_list):
                try:
                    content_list = [i.text for i in chrome.find_elements_by_class_name('WB_detail')]
                    sleep(1)
                    if t() - start > PlatformHandler.timeout:
                        break
                except:
                    break
            if len(content_list):
                content_list = content_list[:10] if len(content_list) > 10 else content_list
                string_list.append("".join(content_list))
            content_list.clear()

        return string_list

    def url2string_weixin(self):
        string_list = []
        driver = PlatformHandler.wechat_chrome
        for each_user in PlatformHandler.url:
            temp_str = []
            for url in each_user:
                driver.get(url)
                sleep(1)
                temp_str.append(driver.find_element_by_id('js_content').text)
            if len(temp_str):
                string_list.append(temp_str)
        return string_list

    def url2string_douban(self):
        string_list = []
        url_list = PlatformHandler.url
        chrome = PlatformHandler.other_chrome
        for each in url_list:
            chrome.get(each)

            try:
                diary = chrome.find_element_by_xpath('//*[@id="note"]/h2/span/a')
                chrome.get(diary.get_attribute('href'))
                diary_list = chrome.find_elements_by_class_name('note-container')[:10]
                string_list.append([i.text for i in diary_list])
            except:
                continue

        return string_list

    def url2string_xima(self):
        string_list = []
        content_list = []
        for each in PlatformHandler.url:
            chrome = PlatformHandler.other_chrome
            chrome.implicitly_wait(15)
            chrome.get(each)
            sleep(3)
            chrome.refresh()
            start = t()
            while not len(content_list):
                for i in range(1, 11):
                    try:
                        content_list.append(chrome.find_element_by_xpath(
                            f'//*[@id="award"]/main/div[1]/div[2]/div/div[1]/div[2]/div[2]/div/div[{i}]').text)
                    except:
                        break
                if t() - start > PlatformHandler.timeout:
                    break
            if len(content_list):
                string_list.append("".join(content_list))
            content_list.clear()

        return string_list

    def url2string(self, url_list, ptype):
        PlatformHandler.url = url_list
        PlatformHandler.ptype = ptype
        if self.ptype == BILIBILI:
            PlatformHandler.other_chrome.refresh()
            return self.url2string_bilibili();
        elif self.ptype == WEIBO:
            PlatformHandler.other_chrome.refresh()
            return self.url2string_weibo()
        elif self.ptype == ZHIHU:
            PlatformHandler.zhihu_chrome.refresh()
            return self.url2string_zhihu()
        elif self.ptype == WEIXIN:
            PlatformHandler.wechat_chrome.refresh()
            return self.url2string_weixin()
        elif self.ptype == DOUBAN:
            PlatformHandler.other_chrome.refresh()
            return self.url2string_douban()
        elif self.ptype == XIMA:
            PlatformHandler.other_chrome.refresh()
            return self.url2string_xima()
        else:
            return "Wrong parameter inside class user"

    def name2url_bilibili(self):
        html = requests.get("https://search.bilibili.com/upuser?keyword=" + PlatformHandler.name).text
        soup = BeautifulSoup(html, 'lxml')
        user_list = soup.find_all('div', class_='up-face')[:3]
        user_list = [str(i.find_all('a')) for i in user_list]
        url_header = 'https:'
        url_tailer = '/dynamic'
        return [(url_header + i[i.find('href="') + len('href="'):i.find("?from")] + url_tailer) for i in
                user_list]

    def name2url_weibo(self):
        html = requests.get("https://s.weibo.com/user?q=" + PlatformHandler.name + "&Refer=weibo_user").text
        soup = BeautifulSoup(html, 'lxml')
        user_list = soup.find_all('div', class_='avator')[:3]
        user_list = [str(i.find_all('a')) for i in user_list]
        url_header = 'https:'
        url_tailer = ''
        return [
            (url_header + i[i.find('href="') + len('href="'):i[i.find('href="') + len('href="'):].find('"') + i.find(
                'href="') + len('href="')] + url_tailer) for i in
            user_list]

    def name2url_weixin(self):
        top_articles_url = []
        try:
            query = PlatformHandler.name
            header = {
                "HOST": "mp.weixin.qq.com",
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0"
            }

            # read cookies
            with open('cookie.txt', 'r', encoding='utf-8') as f:
                cookie = f.read()
            cookies = json.loads(cookie)

            # after login, the url change to:
            # https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=1596832206

            response = requests.get(url=weixin_url, cookies=cookies)
            token = re.findall(r'token=(\d+)', str(response.url))[0]

            # search the interface of target
            search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
            # pass three parameters: token, random, target_name
            query_id = {
                'action': 'search_biz',
                'token': token,
                'lang': 'zh_CN',
                'f': 'json',
                'ajax': '1',
                'random': random.random(),
                'query': query,
                'begin': '0',
                'count': '5'
            }

            search_response = requests.get(search_url, cookies=cookies, headers=header, params=query_id)
            # the first 3 in result
            fakeid_list = [i.get('fakeid') for i in search_response.json().get('list')[:3]]
            # obtain the fakeid

            # for each fakeid, obtain 10 passages.
            # article interface
            appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
            # pass three tokes: token, fakeid, random
            for fakeid in fakeid_list:
                query_id_data = {
                    'token': token,
                    'lang': 'zh_CN',
                    'f': 'json',
                    'ajax': '1',
                    'random': random.random(),
                    'action': 'list_ex',
                    'begin': '0',  # different pages, add 5 each time
                    'count': '5',
                    'query': '',
                    'fakeid': fakeid,
                    'type': '9'
                }
                # article response
                appmsg_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=query_id_data)

                # total article number of this account
                query_id_data = {
                    'token': token,
                    'lang': 'zh_CN',
                    'f': 'json',
                    'ajax': '1',
                    'random': random.random(),
                    'action': 'list_ex',
                    'begin': '0',
                    'count': '5',
                    'query': '',
                    'fakeid': fakeid,
                    'type': '9'
                }
                query_response = requests.get(appmsg_url, cookies=cookies, headers=header, params=query_id_data)
                top_articles_url.append([i.get('link') for i in query_response.json().get('app_msg_list')][:10])
            return top_articles_url
        except:
            return top_articles_url
        # no such user found

    def name2url_douban(self):
        chrome = PlatformHandler.other_chrome
        chrome.get('https://www.douban.com/search?cat=1005&q=' + PlatformHandler.name)
        url_list = []
        for i in range(1, 4):
            try:
                url_list.append(chrome.find_element_by_xpath(
                    f'//*[@id="content"]/div/div[1]/div[3]/div[2]/div[{i}]/div[2]/div/h3/a').get_attribute('href'))
            except:
                break

        return url_list

    def name2url_xima(self):
        chrome = PlatformHandler.other_chrome
        chrome.get("https://www.ximalaya.com/search/zhubo/" + PlatformHandler.name)
        url_list = []
        for i in range(1, 4):
            try:
                url_list.append(chrome.find_element_by_xpath(
                    f'//*[@id="searchPage"]/div[2]/div/div[1]/div/div[1]/div[2]/div/div/div[2]/div/div[2]/div/ul/div[{i}]/div/div/a').get_attribute(
                    'href'))
            except:
                break

        return url_list

    def url2string_zhihu(self):
        string_list = []
        content_list = []
        start = t()
        for each in PlatformHandler.url:
            PlatformHandler.zhihu_chrome.get(each)
            sleep(3)
            PlatformHandler.zhihu_chrome.refresh()
            while not len(content_list):
                try:
                    content_list = [i.text for i in
                                    PlatformHandler.zhihu_chrome.find_elements_by_class_name('List-item')]
                    sleep(1)
                    if t() - start > PlatformHandler.timeout:
                        break
                except:
                    break
            if len(content_list):
                content_list = content_list[:10] if len(content_list) > 10 else content_list
                string_list.append("".join(content_list))
            content_list.clear()
        return string_list

    def name2url_zhihu(self):
        chrome = PlatformHandler.zhihu_chrome
        chrome.get('https://www.zhihu.com/signin')
        if chrome.find_elements_by_link_text('开通机构号'):
            chrome.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div/div[1]/div/form/div[1]/div[2]').click()
            chrome.find_element_by_name('username').clear()
            chrome.find_element_by_name('username').send_keys(zhihu_account)
            chrome.find_element_by_name('password').clear()
            chrome.find_element_by_name('password').send_keys(zhihu_password)
            chrome.find_element_by_xpath('//*[@id="root"]/div/main/div/div/div/div[1]/div/form/button').click()
        PlatformHandler.zhihu_chrome = chrome
        chrome.get('https://www.zhihu.com/search?type=people&q=' + PlatformHandler.name)
        try:
            ret = [i.find_element_by_class_name('UserLink-link').get_attribute('href') for i in
                   chrome.find_elements_by_class_name('List-item')[:3]]
        except:
            ret = []
        return ret

    # this function takes in a name and ptype(bili/weibo...
    # search the web and returns 3 urls of top ranking results.
    # like ['https://space.bilibili.com/66391032/dynamic","...","..."]
    def name2url(self, name, ptype):
        PlatformHandler.name = name
        PlatformHandler.ptype = ptype
        if ptype == BILIBILI:
            PlatformHandler.other_chrome.refresh()
            return self.name2url_bilibili()
        elif ptype == WEIBO:
            PlatformHandler.other_chrome.refresh()
            return self.name2url_weibo()
        elif ptype == ZHIHU:
            PlatformHandler.zhihu_chrome.refresh()
            return self.name2url_zhihu()
        elif ptype == WEIXIN:
            PlatformHandler.wechat_chrome.refresh()
            return self.name2url_weixin()
        elif ptype == DOUBAN:
            PlatformHandler.other_chrome.refresh()
            return self.name2url_douban()
        elif ptype == XIMA:
            PlatformHandler.other_chrome.refresh()
            return self.name2url_xima()
        else:
            return "Wrong parameter inside class user, calling name2url"


# handling numpy vectors and relevant operations.
# single ton
class Vec:
    vocab_list = None
    wordVector = None
    stopwds = None
    dimension = 300

    def __init__(self):
        self.load()
        Vec.dimension = self.wordVector.vector_size

    # return the similarity between self.vec and vec2
    def similarity(self, vec1, vec2):
        # pass in 2 vector
        epsilon = 1e-8
        return (np.dot(vec1, np.transpose(vec2))) / (
                np.linalg.norm(vec1, ord=2) * np.linalg.norm(vec2, ord=2) + epsilon)

    def reset(self, vec2):
        self.vec = vec2

    def string2vec(self, string_list):
        try:
            if len(string_list):
                wd_list = [self.filter(i) for i in string_list]
                encoded_sentence = np.zeros([Vec.dimension, len(string_list)], dtype=np.float32)
                for i, sentence in enumerate(wd_list):
                    count = 0
                    for word in sentence:
                        try:
                            if word in Vec.vocab_list:
                                encoded_sentence[:, i] += Vec.wordVector.get_vector(word)
                                count += 1
                        except:
                            print("exception!")
                    encoded_sentence[:, i] /= count
                return encoded_sentence
            else:
                return []
        except:
            print('Exception in Word2Vec')
            return []

    def load(self):
        # first load stopwords
        with open(os.path.join(stopwds_path, stopwds_name), encoding='utf8') as f:
            Vec.stopwds = f.read().split('\n')

        # then load the whole dictionary.
        Vec.wordVector = gensim.models.KeyedVectors.load_word2vec_format(os.path.join(wordvec_path, wordvec_name),
                                                                         binary=False)
        Vec.vocab_list = [word for word, Vocab in Vec.wordVector.vocab.items()]

    def filter(self, string):
        res = ''
        for char in string:
            if u'\u4e00' <= char <= u'\u9fbf' or 'a' <= char <= 'z' or 'A' <= char <= 'Z':
                res += char
        word_list = [i for i in jieba.cut(res)]
        for i, data in enumerate(word_list):
            if data in Vec.stopwds:
                word_list.pop(i)
        return word_list
    # load word vector to main memory.


# writes relation_list to a csv.

# read to search_list


def main():
    ptHandler = PlatformHandler()
    vecHandler = Vec()

    # read a search list to search_list
    read(os.path.join(search_path, search_name))
    # construct the whole word dictionary
    # iterate over the search list

    for index, eachName in enumerate(search_list):
        if index < start:
            continue
        if index > limit + start:
            break
        try:
            thisUser = User()

            url_bili = ptHandler.name2url(eachName, BILIBILI)

            url_weibo = ptHandler.name2url(eachName, WEIBO)

            url_zhihu = ptHandler.name2url(eachName, ZHIHU)

            url_wx = ptHandler.name2url(eachName, WEIXIN)

            url_douban = ptHandler.name2url(eachName, DOUBAN)

            url_xima = ptHandler.name2url(eachName, XIMA)

            string_of_user_bili = ptHandler.reset(url_bili).url2string(url_bili, BILIBILI)

            string_of_user_weibo = ptHandler.reset(url_weibo).url2string(url_weibo, WEIBO)

            string_of_user_zhihu = ptHandler.reset(url_zhihu).url2string(url_zhihu, ZHIHU)

            string_of_user_wx = ptHandler.reset(url_wx).url2string(url_wx, WEIXIN)

            string_of_user_douban = ptHandler.reset(url_douban).url2string(url_douban, DOUBAN)

            string_of_user_xima = ptHandler.reset(url_xima).url2string(url_xima, XIMA)

            vec_of_user_bili = vecHandler.string2vec(string_of_user_bili)

            vec_of_user_weibo = vecHandler.string2vec(string_of_user_weibo)

            vec_of_user_zhihu = vecHandler.string2vec(string_of_user_zhihu)

            vec_of_user_wx = vecHandler.string2vec(string_of_user_wx)

            vec_of_user_douban = vecHandler.string2vec(string_of_user_douban)

            vec_of_user_xima = vecHandler.string2vec(string_of_user_xima)

            column = len(string_of_user_bili) + len(string_of_user_weibo) + len(string_of_user_zhihu) + len(
                string_of_user_wx) + len(string_of_user_douban) + len(string_of_user_xima)

            all_vec_list = list()

            all_vec_list.extend([{'ptype': BILIBILI, 'vec': vec_of_user_bili[:, i], 'url': url_bili[i]} for i in
                                 range(len(string_of_user_bili))]) if string_of_user_bili is not None and len(
                string_of_user_bili) > 0 else all_vec_list

            all_vec_list.extend([{'ptype': WEIBO, 'vec': vec_of_user_weibo[:, i], 'url': url_weibo[i]} for i in
                                 range(len(string_of_user_weibo))]) if string_of_user_weibo is not None and len(
                string_of_user_weibo) > 0 else all_vec_list

            all_vec_list.extend([{'ptype': ZHIHU, 'vec': vec_of_user_zhihu[:, i], 'url': url_zhihu[i]} for i in
                                 range(len(string_of_user_zhihu))]) if string_of_user_zhihu is not None and len(
                string_of_user_zhihu) > 0 else all_vec_list

            all_vec_list.extend([{'ptype': WEIXIN, 'vec': vec_of_user_wx[:, i], 'url': url_wx[i]} for i in
                                 range(len(string_of_user_wx))]) if string_of_user_wx is not None and len(
                string_of_user_wx) > 0 else all_vec_list

            all_vec_list.extend([{'ptype': DOUBAN, 'vec': vec_of_user_douban[:, i], 'url': url_douban[i]} for i in
                                 range(len(string_of_user_douban))]) if string_of_user_douban is not None and len(
                string_of_user_douban) > 0 else all_vec_list

            all_vec_list.extend([{'ptype': XIMA, 'vec': vec_of_user_xima[:, i], 'url': url_xima[i]} for i in
                                 range(len(string_of_user_xima))]) if string_of_user_xima is not None and len(
                string_of_user_xima) > 0 else all_vec_list

            for i in range(0, column - 1):
                for j in range(i + 1, column):
                    same = True if all_vec_list[i]['ptype'] != all_vec_list[j]['ptype'] and vecHandler.similarity(
                        all_vec_list[i]['vec'], all_vec_list[j]['vec']) > threshold else False
                    if same:
                        res = thisUser.add(all_vec_list[i])
                        res = res and thisUser.add(all_vec_list[j])
                        if res:
                            print(
                                f"Find match, with matchRatio {vecHandler.similarity(all_vec_list[i]['vec'], all_vec_list[j]['vec'])} :\n{all_vec_list[i]['url']}\n{all_vec_list[j]['url']}\n")

            if not thisUser.isEmpty():
                relation_list.append(thisUser)
                print(thisUser)
            if not index % 10 and index:
                print(f'Result before {index}th entry recorded!')
                out(relation_list)
        except Exception as e:
            PlatformHandler.zhihu_chrome.refresh()
            print('Exception!')
    out(relation_list)
    print("Done. ")


if __name__ == '__main__':
    '''
    make sure you execute 
    ' chrome.exe --remote-debugging-port=9222 --user-data-dir=./selenium_data '
    in cmd before running this script.
    '''
    main()
