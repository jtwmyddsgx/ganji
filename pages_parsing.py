#coding:utf-8

import requests
import re
import time
import pymongo
from bs4 import BeautifulSoup

client = pymongo.MongoClient("localhost",27017)
ganji = client["ganji"]
kinds_links = ganji["kinds_links"]
goods_links = ganji["goods_links"]
goods_info = ganji["goods_info"]

class pages:
    headers = {
        "User-Agent":"Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
    }
    host_url = "http://3g.ganji.com/"
    session = requests.session()

    #(url) return soup
    @classmethod
    def get_soup(cls,url,headers=None):
        if headers is None:
            headers = cls.headers.copy()
        resp = None
        try:
            resp = cls.session.get(url=url,headers=headers)
        except Exception as ex:
            print(ex)
            print("error:"+url)
            time.sleep(10)
        if resp:
            if resp.status_code == 200:
                charset_re = re.search(r"charset=([0-9a-zA-Z-]{3,8})",resp.text)
                if charset_re: #set encoding of resp
                    charset = charset_re.group()
                    resp.encoding=charset
                soup = BeautifulSoup(resp.text,"lxml")
                return soup
            else:
                print(resp.status_code)
                return None

    @classmethod
    def insert_one(cls,collection,data):
        try:
            collection.insert_one(data)
        except Exception as ex:
            print(ex)

    #(url)  return kind_links
    @classmethod
    def get_kinds_links(cls,url,headers=None):
        if headers is None:
            headers = cls.headers.copy()
        soup = cls.get_soup(url=url,headers=headers)
        kind1 = soup.find_all("a","kind")
        kind2 = soup.select("div.other > ul > li > a")
        kind_links = {}
        for i in kind1:
            kind_span = i.find_all("span")
            if kind_span:
                kind = kind_span[0].get_text()
            else:
                kind = None
            kind_url = cls.host_url + i.get("href")
            kind_links.update({kind_url:kind}) #key:url  value:kind
        for i in kind2:
            kind = i.get_text()
            kind_url = cls.host_url + i.get("href")
            #kind_links.update({kind_url:kind}) #key:url  value:kind
            kinds_links.insert_one({"url":kind_url,"kind":kind}) #database:kinds_links

    @classmethod
    def get_goods_links(cls,url,headers=None):
        if headers is None:
            headers = cls.headers.copy()

        soup = cls.get_soup(url=url,headers=headers)
        if soup:
            page_num_tag = soup.find_all("span","page-num")
            if page_num_tag:
                page_num = int(page_num_tag[0].get_text().split("/")[1])
            else:
                page_num = 1
            url = url.split("?")[0]
            urls = [url+"?page={}".format(i) for i in range(1,page_num+1)]
            for url in urls:
                headers.update({
                    "Referer": url
                })
                soup = cls.get_soup(url=url,headers=headers)
                if soup:
                    good_url_tag = soup.find_all("a", "infor")
                    if good_url_tag:
                        for i in good_url_tag:
                            good_url = cls.host_url + i.get("href").split("?")[0]
                            if "zhuanzhuan" in good_url:
                                continue
                            title_tag = i.find_all("div","iName")
                            if title_tag:
                                title = title_tag[0].get_text().strip()
                            else:
                                title = None
                            print(good_url)
                            #goods_links.insert_one({"url":good_url,"title":title})
                time.sleep(1)

    @classmethod
    def get_good_info(cls,url,headers=None):
        if headers is None:
            headers = cls.headers.copy()
        soup = cls.get_soup(url=url,headers=headers)
        if soup:
            phone_tag = soup.find_all("span","f15 fc-red")
            phone = phone_tag[0].get_text() if phone_tag else None
            title_tag = soup.find_all("h1", "title")
            title = title_tag[0].get_text() if title_tag else None
            table = soup.select("div.comm-area > table")
            types = {"价格":"price","联系人":"username","品牌":"brand","区域":"location","来源":"source","容量/版本":"version","新旧程度":"recency","发票/配件":"invoice"}
            tr = []
            brand = None
            location = None
            username = None
            price = None
            source = None
            version = None
            recency = None
            invoice = None
            for t in table:
                tr += t.find_all("tr")
            for t in tr:
                th = t.find_all("th")
                td = t.find_all("td")
                for h,d in zip(th,td):
                    type = h.get_text()
                    type_in = types.get(type)
                    if type_in == "brand":
                        brand = [i for i in d.stripped_strings]
                    elif type_in == "location":
                        location = [i for i in d.stripped_strings]
                    elif type_in == "source":
                        source = d.get_text()
                    elif type_in == "version":
                        version = d.get_text()
                    elif type_in == "recency":
                        recency = d.get_text()
                    elif type_in == "invoice":
                        invoice = d.get_text()
                    elif type_in == "username":
                        username = d.get_text()
                    elif type_in == "price":
                        price = [i for i in d.stripped_strings]
            data = {"url":url,"username":username,"phone":phone,"brand":brand,"title":title,
                    "price":price,"location":location,"source":source,"recency":recency,
                    "invoice":invoice,"vesion":version,
                    }
            cls.insert_one(goods_info,data)
            time.sleep(2)






if __name__ == "__main__":
    #pages.get_kinds_links("http://3g.ganji.com/fz_secondmarket/")
    #url = kinds_links.find()
    #urls = []
    #for i in url:
        # if i["url"] in urls:
        #     print(i["url"])
        # else:
        #     urls.append(i["url"])
        #pages.get_goods_links(url=i["url"])
    #print(goods_links.count())
    #pages.get_good_info("http://3g.ganji.com/fz_shoujihao/1921389379x")

    y = []
    x = []
    for i in goods_links.find():
        y.append(i["url"])
    for i in goods_info.find():
        x.append(i["url"])
    y = set(y)
    x = set(x)
    result = list(y-x)

    for i in result:
        pages.get_good_info(i)

