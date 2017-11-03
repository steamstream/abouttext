from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import datetime
import time
import re

newspaper = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] # 조선, 동아, 중앙, 한국, 경향, 서울, 한겨레, 국민, 세계, 문화

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

def logger(articles):
    with open("reader.log", "at", encoding = "utf-8") as fout:
        for article in articles:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            newspaper_id = article[0]
            article_date = article[1]
            article_title = article[2]
            fout.write("[{}], {}, {}, {}".format(now, newspaper_id, article_date, article_title))
            fout.write("\n" if (len(article[3]) > 500) else ", WARNING(TOO_SHORT)\n")

# 참조: https://stackoverflow.com/questions/4995116/only-extracting-text-from-this-element-not-its-children
# 17Oct30 17:13 현재 문제가 있는데 고치지 못함
def donga_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    tmp = soup.find("div", {"class" : "article_txt"}).contents
    article = "".join([i for i in tmp if isinstance(i, str)])
    article = arrange(article)
    return article

def donga(date_list):
    articles = []
    for date in date_list:
        if not date_check(date):
            print("Wrong input in [donga(date)]")
            return None
        
        domain = "http://news.donga.com"
        editorialUrl = "/Series/70040100000001"
        targetUrl = domain + editorialUrl + "?ymd=" + date.replace("-", "")
        
        soup = get_soup(targetUrl)
        
        divs = soup.find_all("div", {"class":"rightList"})
        
        for div in divs:
            link = div.find("a")
            articles.append([2, date, link.find("span").get_text(), donga_readArticle(domain, link.attrs["href"])])
    
    return articles

def joongang_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    article = soup.find("div", {"id":"article_body"}).get_text()
    article = arrange(article)
    return article

def joongang(date_list):
    articles = []
    for date in date_list:
        if not date_check(date):
            print("Wrong input in [joongang(date)]")
            return None
        
        domain = "http://news.joins.com"
        editorialUrl = "/opinion/editorialcolumn/list/1"
        targetUrl = domain + editorialUrl + "?filter=OnlyJoongang&date=" + date
        
        soup = get_soup(targetUrl)
        
        lis = soup.find("ul", {"class" : "type_b"}).find_all("li")
        
        for li in lis:
            link = li.find("a", {"href" : True})
            title = link.get_text()
            if (not len(title) == 0 and title.startswith("[사설]")):
                articles.append([3, date, title, joongang_readArticle(domain, link.attrs["href"])])
    
    return articles

# 한국일보는 다른 신문이랑 좀 다름. "[사설]" 로 검색한 결과에서 찾아나감.
def hankook_readArticle(link):
    targetUrl = link
    soup = get_soup(targetUrl)
    
    temp_article_date = soup.find("div", {"class":"author"}).find("div", {"class":"writeOption"}).get_text()
    article_date = re.findall(r"\d{4}.\d{2}.\d{2}", temp_article_date)[0].replace(".", "-")
    
    article = soup.find("article", {"class":"newsStoryTxt", "id":"article-body"}).get_text()
    article = arrange(article)
    
    return (article_date, article)

def hankook(date_list):
    articles = []
    
    for date in date_list:
        if not date_check(date):
            print("Wrong input in [munhwa(date)]")
            return None
    
    page_counter = 1
    stop_flag = False
    
    start_from = min(date_list)
    while (not stop_flag) and (page_counter < 100):
        targetUrl = "http://search.hankookilbo.com/?ssort=0&page={}&sword=[%EC%82%AC%EC%84%A4]".format(page_counter)
        
        soup = get_soup(targetUrl)
        
        links = soup.find("div",{"class":"dw_news"}).find_all("a", {"onclick":True})
        
        for link in links:
            title = link.get_text()
            addr = re.findall(r"baro_view_src\('(.*)'\); ", link.attrs["onclick"])[0]
            
            if ("사설" in title):
                (article_date, article) = hankook_readArticle(addr)
                if (article_date in date_list):
                    articles.append([4, article_date, title, article])
            else:
                continue
            
            # 찾고자 하는 날짜 까지 왔으니, 그만 돌아도 된다. 
            if start_from > article_date:
                stop_flag = True
        
        page_counter += 1
    
    return articles

def seoul_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    article = arrange(soup.find("div", {"class" : "v_article"}).get_text())
    return article

def seoul(date_list):
    articles = []
    for date in date_list:
        if not date_check(date):
            print("Wrong input in [seoul(date)]")
            return None
        
        domain = "http://www.seoul.co.kr"
        editorialUrl = "/news/newsList.php?section=editorial"
        targetUrl = domain + editorialUrl + "&date=" + date
        
        soup = get_soup(targetUrl)
        
        links = soup.find("div", {"id" : "list_area"}).find_all("a", {"href" : True})
        
        for link in links:
            articles.append([6, date, link.get_text(), seoul_readArticle(domain, link.attrs["href"])])
    
    return articles

def hani_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    tmp = soup.find("div", {"class":"text"}).contents
    article = "".join([i for i in tmp if isinstance(i, str)])
    article = arrange(article)
    
    time.sleep(600) # robots.txt 에 있는 Crawl-delay: 600 에 의하여.
    return article

def hani(date_list):
    articles = []
    
    for date in date_list:
        if not date_check(date):
            print("Wrong input in [hani(date)]")
            return None
    
    page_counter = 1
    stop_flag = False
    
    start_from = min(date_list)
    while (not stop_flag) and (page_counter < 100):
        domain = "http://www.hani.co.kr"
        editorialUrl = "/arti/opinion/editorial"
        targetUrl = domain + editorialUrl + "/list{}.html".format(page_counter)
        
        soup = get_soup(targetUrl)
        
        divs = soup.find("div", {"class" : "section-list-area"}).find_all("div", {"article-area"})
        
        for div in divs:
            article_date = div.find("span", {"class" : "date"}).get_text().split()[0]
            links = div.find_all("a", {"href":True})
            for link in links:
                title = link.get_text()
                if ("사설]" in title) and (article_date in date_list):
                    articles.append([7, article_date, title, hani_readArticle(domain, link.attrs["href"])])
            
            # 찾고자 하는 날짜 까지 왔으니, 그만 돌아도 된다. 
            if start_from > article_date:
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

def kmib(date_list):
    articles = []
    for date in date_list:
        if not date_check(date):
            print("Wrong input in [joongang(date)]")
            return None
        
        domain = "http://news.kmib.co.kr/article"
        editorialUrl = "/list.asp?sid1=opi"
        targetUrl = domain + editorialUrl + "&sid2=&sdate=" + date.replace("-", "")
        
        soup = get_soup(targetUrl)
        
        links = soup.find("div", {"class":"nws_list"}).find_all("a", {"href" : True})
        
        for link in links:
            title = link.get_text()
            if "사설]" in title:
                articles.append([8, date, title, kmib_readArticle(domain, link.attrs["href"])])
    
    return articles

def segye_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    article = soup.find("div", {"class" : "news_text"}).get_text()
    article = arrange(article)
    
    return article

def segye(date_list):
    articles = []
    
    for date in date_list:
        if not date_check(date):
            print("Wrong input in [segye(date)]")
            return None
    
    page_counter = 1
    stop_flag = False
    
    start_from = min(date_list)
    while (not stop_flag) and (page_counter < 100):
        domain = "http://www.segye.com"
        editorialUrl = "/newsList/0101100300000"
        targetUrl = domain + editorialUrl + "?curPage={}".format(page_counter)
        
        soup = get_soup(targetUrl)
        
        divs = soup.find("div", {"class":"newslist_area"}).find_all("div", {"area_box"})
        
        for div in divs:
            article_date = div.find("span", {"class" : "date"}).get_text().replace(".", "-")
            link = div.find("a", {"href":True})
            title = link.get_text()
            if ("사설]" in title) and (article_date in date_list):
                articles.append([9, article_date, title, segye_readArticle(domain, link.attrs["href"])])
            # 찾고자 하는 날짜 까지 왔으니, 그만 돌아도 된다. 
            if start_from > article_date:
                stop_flag = True
        
        page_counter += 1
    
    return articles

def munhwa_readArticle(domain, link):
    targetUrl = check_link(domain, link)
    soup = get_soup(targetUrl)
    
    article = soup.find("div", {"id" : "NewsAdContent"}).get_text()
    article = arrange(article)
    
    return article

def munhwa(date_list):
    articles = []
    
    for date in date_list:
        if not date_check(date):
            print("Wrong input in [munhwa(date)]")
            return None
    
    page_counter = 1
    stop_flag = False
    
    start_from = min(date_list)
    while (not stop_flag) and (page_counter < 100):
        domain = "http://www.munhwa.com"
        editorialUrl = "/news/section_list.html?sec=opinion&class=1"
        targetUrl = domain + editorialUrl + "&page={}".format(page_counter)
        
        soup = get_soup(targetUrl)
        
        links = soup.find_all("a", {"class" : "d14b_333"})
        
        for link in links:
            article_date_block = link.parent.find("font").get_text()
            article_date = re.sub(r"[\[\]]", "", article_date_block).replace(".", "-")
            title = link.get_text()
            if ("사설" in title) and (article_date in date_list):
                articles.append([10, article_date, title, munhwa_readArticle(domain, link.attrs["href"])])
            # 찾고자 하는 날짜 까지 왔으니, 그만 돌아도 된다. 
            if start_from > article_date:
                stop_flag = True
        
        page_counter += 1
    
    return articles

