import article_reader as ar
import pymysql
import datetime
import sys

# 신문사 번호: 1.조선, 2.동아, 3.중앙, 4.한국, 5.경향, 6.서울, 7.한겨레, 8.국민, 9.세계, 10.문화
newspapers = [None, None, "donga", "joongang", "hankook", None, "seoul", "hani", "kmib", "segye", "munhwa"]

conn = pymysql.connect(host = "localhost", user = "article_scrapper", password = "article", charset = "utf8")
cur = conn.cursor()
cur.execute("USE articles")

# scrap_and_save.py (신문사 번호) (시작 날짜) (끝 날짜)
# Example1: scrap_and_save.py ==> 모든 신문사, 오늘 사설
# Example2: scrap_and_save.py 2 ==> 동아일보, 오늘 사설
# Example3: scrap_and_save.py 2 2017-10-25 ==> 동아일보, 2017년 10월 25일 사설
# Example4: scrap_and_save.py 2 2017-10-25 2017-10-31 ==> 동아일보, 2017년 10월 25일 부터 2017년 10월 31일 까지 사설
def main(argv):
    (co_id, start_date, end_date) = assignment(argv)
    
    date_list = []
    # 시작 날짜 부터 끝 날짜 까지 %Y-%m-%d 형식으로 date_list에 추가
    for i in range((end_date - start_date + datetime.timedelta(days = 1)).days):
        date_list.append((start_date + datetime.timedelta(days = i)).strftime("%Y-%m-%d"))
    
    articles = None
    try:
        if (co_id == 0):
            for i in range(len(newspapers)):
                if (newspapers[i] != None):
                    articles = eval("ar.{}(date_list)".format(newspapers[i]))
                    insert_articles(articles)
                else:
                    print("scrapping denied. co_id: " + i)
        else:
            if (newspapers[co_id] != None):
                articles = eval("ar.{}(date_list)".format(newspapers[co_id]))
                insert_articles(articles)
            else:
                print("scrapping denied. co_id:", co_id)
        
    finally:
        cur.close()
        conn.close()

def already_have(co_id, date, title):
    cur.execute("SELECT * FROM articles WHERE co_id=%s AND DATE(issued)=%s AND title=%s", (co_id, date, title))
    return False if cur.rowcount == 0 else True

def insert_articles(articles):
    for article in articles:
        co_id = int(article[0])
        date = article[1]
        title = article[2]
        contents = article[3]
        if not already_have(co_id, date, title):
            cur.execute("INSERT INTO articles (co_id, issued, title, contents) VALUES (%s, %s, %s, %s)", (co_id, date, title, contents))
            conn.commit()
            ar.logger([article])

# 신문사 번호, 날짜 초기화
def assignment(argv):
    co_id = 0
    start_date = datetime.datetime.now()
    end_date = datetime.datetime.now()
    
    idx = 1
    if (idx < len(argv)):
        co_id = int(argv[1])
    idx += 1
    if (idx < len(argv)):
        start_date = datetime.datetime.strptime(argv[2], "%Y-%m-%d")
    idx += 1
    if (idx < len(argv)):
        end_date = datetime.datetime.strptime(argv[3], "%Y-%m-%d")
    
    return (co_id, start_date, end_date)

if __name__ == "__main__":
    main(sys.argv)