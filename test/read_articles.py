from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import datetime
import re

now = datetime.datetime.now()
yesterday = (now + datetime.timedelta(days = -1)).strftime("%Y-%m-%d")

articles = {}

def date_check(date):
    y, m, d = date.split("-")
    if not 2000 < int(y) < 2020:
        return False
    if not 1 <= int(m) <= 12:
        return False
    if not 1 <= int(d) <= 31:
        return False
    return True

def arrange(article):
    article = article.strip()
    article = re.sub(r"[\n\t ]+", " ", article)
    # article = re.sub(r"[‘’]", "'", article)
    # article = re.sub(r'[“”]', '"', article)
    return article
    
def seoul_readArticle(url):
    baseUrl = "http://www.seoul.co.kr"
    
    if not url.startswith(baseUrl):
        targetUrl =  baseUrl + url
    else:
        targetUrl = url
    
    httpRequest = Request(targetUrl)
    httpResponse = urlopen(httpRequest)
    soup = BeautifulSoup(httpResponse.read(), "html.parser")
    
    article = arrange(soup.find("div", {"class" : "v_article"}).get_text())
    return article
    
def seoul(date):
    if not date_check(date):
        print("Wrong input in [seoul(date)]")
        return None
    
    baseUrl = "http://www.seoul.co.kr"
    editorialUrl = "/news/newsList.php?section=editorial"
    targetUrl = baseUrl + editorialUrl + "&date=" + date
    
    httpRequest = Request(targetUrl)
    httpResponse = urlopen(httpRequest)
    soup = BeautifulSoup(httpResponse.read(), "html.parser")
    
    links = soup.find("div", {"id" : "list_area"}).find_all("a", {"href" : True})
    
    articles = []
    for link in links:
        articles.append([link.get_text(), seoul_readArticle(link.attrs["href"])])
    
    return articles

def donga_readArticle(url):
    baseUrl = "http://news.donga.com"
    
    if not url.startswith(baseUrl):
        targetUrl =  baseUrl + url
    else:
        targetUrl = url
    
    httpRequest = Request(targetUrl)
    httpResponse = urlopen(httpRequest)
    soup = BeautifulSoup(httpResponse.read(), "html.parser")
    
    tmp = soup.find("div", {"class" : "article_txt"}).contents
    article = "".join([i for i in tmp if isinstance(i, str)])
    article = arrange(article)
    return article

def donga(date):
    if not date_check(date):
        print("Wrong input in [seoul(date)]")
        return None
    
    baseUrl = "http://news.donga.com"
    editorialUrl = "/Series/70040100000001"
    targetUrl = baseUrl + editorialUrl + "?ymd=" + date.replace("-", "")
    
    httpRequest = Request(targetUrl)
    httpResponse = urlopen(httpRequest)
    soup = BeautifulSoup(httpResponse.read(), "html.parser")
    
    divs = soup.find_all("div", {"class":"rightList"})
    
    articles = []
    for div in divs:
        link = div.find("a")
        articles.append([link.find("span").get_text(), donga_readArticle(link.attrs["href"])])
    
    return articles




lst = donga(yesterday)





















    