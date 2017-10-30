from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import datetime
import time
import re

now = datetime.datetime.now()
yesterday = (now + datetime.timedelta(days = -2)).strftime("%Y-%m-%d")

# 날짜 형식을 확인. 2000년 이후 2020년 이전 범위만.
def date_check(date):
    y, m, d = date.split("-")
    if not 2000 < int(y) < 2020:
        return False
    if not 1 <= int(m) <= 12:
        return False
    if not 1 <= int(d) <= 31:
        return False
    return True

# article에 있는 공백문자들 제거.
# replace_quotes = True 인 경우: 따옴표 단순화.
def arrange(article, **kwargs):
    article = article.strip()
    # article = re.sub(r"[\xa0\n\t ]+", " ", article)
    article = re.sub(r"\s+", " ", article)
    if ("replace_quotes" in kwargs) and (kwargs["replace_quotes"] == True):
        article = re.sub(r"[‘’]", "'", article)
        article = re.sub(r'[“”]', '"', article)
    return article

# url을 받아 해당하는 웹 페이지에 대한 BeautifulSoup 객체 반환
def get_soup(targetUrl):
    httpRequest = Request(targetUrl)
    httpResponse = urlopen(httpRequest)
    return BeautifulSoup(httpResponse.read(), "html.parser")

# 내부 링크의 경우. domain이 포함 되어 있는 경우, 상대 주소인 경우 둘 다 있음. 절대 주소를 반환.
def check_link(domain, link):
    if not link.startswith(domain):
        if domain.endswith("/") or link.startswith("/"):
            return domain + link
        else:
            return domain + "/" + link
    else:
        return link


def seoul_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    article = arrange(soup.find("div", {"class" : "v_article"}).get_text())
    return article

def seoul(date):
    if not date_check(date):
        print("Wrong input in [seoul(date)]")
        return None
    
    domain = "http://www.seoul.co.kr"
    editorialUrl = "/news/newsList.php?section=editorial"
    targetUrl = domain + editorialUrl + "&date=" + date
    
    soup = get_soup(targetUrl)
    
    links = soup.find("div", {"id" : "list_area"}).find_all("a", {"href" : True})
    
    articles = []
    for link in links:
        articles.append([link.get_text(), seoul_readArticle(domain, link.attrs["href"])])
    
    return articles

# 참조: https://stackoverflow.com/questions/4995116/only-extracting-text-from-this-element-not-its-children
# 17Oct30 17:13 현재 문제가 있는데 고치지 못함
def donga_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    print(targetUrl)
    
    tmp = soup.find("div", {"class" : "article_txt"}).contents
    article = "".join([i for i in tmp if isinstance(i, str)])
    print(article)
    article = arrange(article)
    return article

def donga(date):
    if not date_check(date):
        print("Wrong input in [donga(date)]")
        return None
    
    domain = "http://news.donga.com"
    editorialUrl = "/Series/70040100000001"
    targetUrl = domain + editorialUrl + "?ymd=" + date.replace("-", "")
    
    soup = get_soup(targetUrl)
    
    divs = soup.find_all("div", {"class":"rightList"})
    
    articles = []
    print(divs)
    print("+++++++++++++++++++++++++++++++")
    for div in divs:
        link = div.find("a")
        print(link)
        
        articles.append([link.find("span").get_text(), donga_readArticle(domain, link.attrs["href"])])
        print("___________________________________________")
    
    return articles

def joongang_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    article = soup.find("div", {"id":"article_body"}).get_text()
    article = arrange(article)
    return article

def joongang(date):
    if not date_check(date):
        print("Wrong input in [joongang(date)]")
        return None
    
    domain = "http://news.joins.com"
    editorialUrl = "/opinion/editorialcolumn/list/1"
    targetUrl = domain + editorialUrl + "?filter=OnlyJoongang&date=" + date
    
    soup = get_soup(targetUrl)
    
    lis = soup.find("ul", {"class" : "type_b"}).find_all("li")
    
    articles = []
    for li in lis:
        link = li.find("a", {"href" : True})
        title = link.get_text()
        if (not len(title) == 0 and title.startswith("[사설]")):
            articles.append([title, joongang_readArticle(domain, link.attrs["href"])])
    
    return articles

def hani_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    tmp = soup.find("div", {"class":"text"}).contents
    article = "".join([i for i in tmp if isinstance(i, str)])
    article = arrange(article)
    
    time.sleep(600) # robots.txt 에 있는 Crawl-delay: 600 에 의하여.
    return article

def hani(date):
    if not date_check(date):
        print("Wrong input in [hani(date)]")
        return None
    
    page_counter = 1
    stop_flag = False
    
    articles = []
    while (not stop_flag) and (page_counter < 100):
        domain = "http://www.hani.co.kr"
        editorialUrl = "/arti/opinion/editorial"
        targetUrl = domain + editorialUrl + "/list{}.html".format(page_counter)
        
        soup = get_soup(targetUrl)
        
        divs = soup.find("div", {"class":"section-list-area"}).find_all("div", {"article-area"})
        
        for div in divs:
            article_date = div.find("span", {"class" : "date"}).get_text().split()[0]
            links = div.find_all("a", {"href":True})
            for link in links:
                title = link.get_text()
                if ("사설]" in title) and (date == article_date):
                    articles.append([title, hani_readArticle(domain, link.attrs["href"])])
            
            # 찾고자 하는 날짜 까지 왔으니, 그만 돌아도 된다. 
            if date > article_date:
                stop_flag = True
        
        page_counter += 1
        time.sleep(600) # robots.txt 에 있는 Crawl-delay: 600 에 의하여.
    
    return articles

def kmib_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    article = soup.find("div", {"id" : "articleBody"}).get_text()
    article = arrange(article)
    return article

def kmib(date):
    if not date_check(date):
        print("Wrong input in [joongang(date)]")
        return None
    
    domain = "http://news.kmib.co.kr/article"
    editorialUrl = "/list.asp?sid1=opi"
    targetUrl = domain + editorialUrl + "&sid2=&sdate=" + date.replace("-", "")
    
    soup = get_soup(targetUrl)
    
    links = soup.find("div", {"class":"nws_list"}).find_all("a", {"href" : True})
    
    articles = []
    for link in links:
        title = link.get_text()
        if "사설]" in title:
            articles.append([title, kmib_readArticle(domain, link.attrs["href"])])
    
    return articles

# 미완
def segye_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    tmp = soup.find("div", {"class":"text"}).contents
    article = "".join([i for i in tmp if isinstance(i, str)])
    article = arrange(article)
    
    time.sleep(600) # robots.txt 에 있는 Crawl-delay: 600 에 의하여.
    return article
# 미완
def segye(date):
    if not date_check(date):
        print("Wrong input in [hani(date)]")
        return None
    
    page_counter = 1
    stop_flag = False
    
    articles = []
    while (not stop_flag) and (page_counter < 100):
        domain = "http://www.segye.com"
        editorialUrl = "/newsList/0101100300000"
        targetUrl = domain + editorialUrl + "?curPage={}".format(page_counter)
        
        soup = get_soup(targetUrl)
        
        divs = soup.find("div", {"class":"newslist_area"}).find_all("div", {"area_box"})
        
        for div in divs:
            article_date = div.find("span", {"class" : "date"}).get_text().split()[0]
            links = div.find_all("a", {"href":True})
            for link in links:
                title = link.get_text()
                if ("사설]" in title) and (date == article_date):
                    articles.append([title, hani_readArticle(domain, link.attrs["href"])])
            
            # 찾고자 하는 날짜 까지 왔으니, 그만 돌아도 된다. 
            if date > article_date:
                stop_flag = True
        
        page_counter += 1
        time.sleep(600) # robots.txt 에 있는 Crawl-delay: 600 에 의하여.
    
    return articles

lst = donga("2017-10-25")





















    