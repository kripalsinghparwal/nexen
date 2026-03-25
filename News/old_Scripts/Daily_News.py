import time
import schedule
import requests
import xmltodict
import json
import datetime
from bs4 import BeautifulSoup as bs

news_payload = {
    "companyName": None,
    "cin": None,
    "heading": None,
    "newsBody": None,
    "newsDate": None,
    "link": None
}


# https://www.livemint.com/rss/markets
# https://www.livemint.com/rss/industry

def write_to_txt(news_payload):
    today = datetime.date.today()
    with open(r"I:\NewsData\NewsPayload\PendingNews_{0}.txt".format(today), "a+") as f:
        f.write(json.dumps(news_payload))
        f.write(",")
        f.write("\n")
        f.close()


################################################# Money Control ##############################################
def insolvencynews():
    url = "https://insolvencytracker.in/"
    header = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"}
    resp = requests.get(url=url, headers=header)
    soup = bs(resp.content, "html.parser")
    tables = soup.find(id="aft-inner-row")
    classess = tables.find_all(class_='align-items-center')
    for classes in classess:
        links = classes.find_all(class_='article-title article-title-1')
        for link in links:
            url = link.find('a').get('href')
            news_payload['link'] = url
            date = "-".join(url.split('in/')[1].split('/')[0:3])
            news_payload['newsDate'] = date
            heading = link.find('a').getText()
            news_payload['heading'] = heading.strip()
            # print(heading.strip())
        bodys = classes.find_all(class_='full-item-discription')
        for body in bodys:
            Body = body.find('p').getText()
            news_payload['newsBody'] = Body.strip()

        # print(json.dumps(news_payload))
        write_to_txt(news_payload)


def moneycontrolNews():
    news_rss_feed = "https://www.moneycontrol.com/rss/business.xml"
    resp = requests.get(news_rss_feed)
    xml_file = resp.text
    data_dict = xmltodict.parse(xml_file)

    news_data = data_dict['rss']['channel']['item']

    for news in range(len(news_data)):
        try:
            date = " ".join(news_data[news]['pubDate'].split(' ')[1:4])
            Date = datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
            responce = requests.get(news_data[news]['link'])
            soup1 = bs(responce.content, 'html.parser')
            bodys = soup1.find_all(class_='content_wrapper arti-flow')
            for body in bodys:
                Body = body.find_all('p')
                allBody = []
                for b in Body:
                    bodyText = b.text.replace("\u2019", "").replace("\n", "").replace("\t", "").strip()
                    allBody.append(bodyText)
                newsBody = " ".join(allBody)

            news_payload['heading'] = news_data[news]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                "\u2013", "")
            news_payload['newsBody'] = newsBody
            news_payload['newsDate'] = Date
            news_payload['link'] = news_data[news]['link']
            write_to_txt(news_payload)
        except:
            pass


############################################# The times of india ########################

def timeOfIndiaNews():
    news_rss_feed = "https://timesofindia.indiatimes.com/rssfeeds/1898055.cms"
    resp = requests.get(news_rss_feed)
    xml_file = resp.text
    data_dict = xmltodict.parse(xml_file)

    news_data = data_dict['rss']['channel']['item']

    for news in range(len(news_data)):
        try:
            Date = "".join(news_data[news]['pubDate'].split('T')[0])
            # Date = datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
            responce = requests.get(news_data[news]['link'], timeout=500)
            soup1 = bs(responce.content, 'html.parser')
            bodys = soup1.find_all(class_='heightCalc')
            # print(bodys)
            for body in bodys:
                Body = body.find_all('a')
                allBody = []
                for b in Body:
                    bodyText = b.text.replace("\u2019", "").replace("\n", "").replace("\t", "").strip()
                    allBody.append(bodyText)
                newsBody = " ".join(allBody)

            news_payload['heading'] = news_data[news]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                "\u2013", "")
            news_payload['newsBody'] = newsBody
            news_payload['newsDate'] = Date
            news_payload['link'] = news_data[news]['link']
            write_to_txt(news_payload)
        except:
            pass


##############################################  CNBC ##################################

def cnbcNews():
    news_rss_feed = "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147"
    resp = requests.get(news_rss_feed)
    xml_file = resp.text
    data_dict = xmltodict.parse(xml_file)

    news_data = data_dict['rss']['channel']['item']

    for news in range(len(news_data)):
        try:
            date = " ".join(news_data[news]['pubDate'].split(' ')[1:4])
            Date = datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')        
            responce = requests.get(news_data[news]['link'], timeout=500)
            soup1 = bs(responce.content, 'html.parser')
            bodys = soup1.find_all(class_='group')
            # print(bodys)
            for body in bodys:
                Body = body.find_all('p')
                allBody = []
                for b in Body:
                    bodyText = b.text.replace("\u2019", "").replace("\n", "").replace("\t", "").strip()
                    allBody.append(bodyText)
                newsBody = " ".join(allBody)

            news_payload['heading'] = news_data[news]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                "\u2013", "").replace("\u00a3", "").replace("\u00a0", "")
            news_payload['newsBody'] = newsBody
            news_payload['newsDate'] = Date
            news_payload['link'] = news_data[news]['link']
            write_to_txt(news_payload)
        except:
            pass


############################################### livemint #############################################

def livemintNews():
    try:
        news_rss_feed = "https://www.livemint.com/rss/markets"
        # news_rss_feed = "https://www.livemint.com/rss/companies"
        resp = requests.get(news_rss_feed)
        xml_file = resp.text
        data_dict = xmltodict.parse(xml_file)
        news_data = data_dict['rss']['channel']['item']
        for news in range(len(news_data)):
            date = " ".join(news_data[news]['pubDate'].split(' ')[1:4])
            Date = datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
            try:
                responce = requests.get(news_data[news]['link'], timeout=500)
                soup1 = bs(responce.content, 'html.parser')
                bodys = soup1.find_all(class_='mainArea')
                for body in bodys:
                    Body = body.find_all('p')
                    allBody = []
                    for b in Body:
                        bodyText = b.text.replace("\u2018", "").replace("\u2019", "").replace("\u2013", "").replace(
                            "\u00a3", "").replace("\u00a0", "").strip()
                        allBody.append(bodyText)
                    newsBody = " ".join(allBody)

                news_payload['heading'] = news_data[news]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                    "\u2013", "").replace("\u00a3", "").replace("\u00a0", "").replace("\u200a", "").strip()
                news_payload['newsBody'] = newsBody
                news_payload['newsDate'] = Date
                news_payload['link'] = news_data[news]['link']
                write_to_txt(news_payload)
            except:
                pass
    except Exception as e:
        print(e)


def livemintNews1():
    try:
        # news_rss_feed = "https://www.livemint.com/rss/markets"
        news_rss_feed = "https://www.livemint.com/rss/companies"
        resp = requests.get(news_rss_feed)
        xml_file = resp.text
        data_dict = xmltodict.parse(xml_file)
        news_data = data_dict['rss']['channel']['item']
        for news in range(len(news_data)):
            date = " ".join(news_data[news]['pubDate'].split(' ')[1:4])
            Date = datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
            try:
                responce = requests.get(news_data[news]['link'], timeout=500)
                soup1 = bs(responce.content, 'html.parser')
                bodys = soup1.find_all(class_='mainArea')
                for body in bodys:
                    Body = body.find_all('p')
                    allBody = []
                    for b in Body:
                        bodyText = b.text.replace("\u2018", "").replace("\u2019", "").replace("\u2013", "").replace(
                            "\u00a3", "").replace("\u00a0", "").strip()
                        allBody.append(bodyText)
                    newsBody = " ".join(allBody)

                news_payload['heading'] = news_data[news]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                    "\u2013", "").replace("\u00a3", "").replace("\u00a0", "").replace("\u200a", "").strip()
                news_payload['newsBody'] = newsBody
                news_payload['newsDate'] = Date
                news_payload['link'] = news_data[news]['link']
                write_to_txt(news_payload)
            except:
                pass
    except Exception as e:
        print(e)


#####################################  economictimes #########################

def economicTimesNews():
    try:
        news_rss_feed = "https://hr.economictimes.indiatimes.com/rss/industry"
        # news_rss_feed = "https://economictimes.indiatimes.com/prime/money-and-markets/rssfeeds/62511286.cms"
        # news_rss_feed = "https://cfo.economictimes.indiatimes.com/rss/corporate-finance"
        resp = requests.get(news_rss_feed)
        xml_file = resp.text
        data_dict = xmltodict.parse(xml_file)
        news_data = data_dict['rss']['channel']['item']
        # print(news_data[0]['title'])
        for i in range(len(news_data)):
            try:
                news_payload['heading'] = news_data[i]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                    "\u2013", "")
                news_payload['newsBody'] = news_data[i]['description']
                news_payload['newsDate'] = news_data[i]['pubDate'].split('T')[0]
                news_payload['link'] = news_data[i]['link']
                write_to_txt(news_payload)
                # print(news_payload)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)


def economicTimesNews1():
    try:
        # news_rss_feed = "https://hr.economictimes.indiatimes.com/rss/industry"
        news_rss_feed = "https://economictimes.indiatimes.com/prime/money-and-markets/rssfeeds/62511286.cms"
        # news_rss_feed = "https://cfo.economictimes.indiatimes.com/rss/corporate-finance"
        resp = requests.get(news_rss_feed)
        xml_file = resp.text
        data_dict = xmltodict.parse(xml_file)
        news_data = data_dict['rss']['channel']['item']
        # print(news_data[0]['title'])
        for i in range(len(news_data)):
            try:
                d = news_data[i]['pubDate']
                date = d[:16].split(',')[1].strip()
                Date = datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d') 
                news_payload['heading'] = news_data[i]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                    "\u2013", "")
                news_payload['newsBody'] = news_data[i]['description']
                news_payload['newsDate'] = Date
                news_payload['link'] = news_data[i]['link']
                write_to_txt(news_payload)
                # print(news_payload)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)


def economicTimesNewsbfsi():
    try:
        news_rss_feed = "https://bfsi.economictimes.indiatimes.com/rss/industry"
        resp = requests.get(news_rss_feed)
        xml_file = resp.text
        data_dict = xmltodict.parse(xml_file)
        news_data = data_dict['rss']['channel']['item']
        # print(news_data[0]['title'])
        for i in range(len(news_data)):
            try:
                news_payload['heading'] = news_data[i]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                    "\u2013", "")
                news_payload['newsBody'] = news_data[i]['description']
                news_payload['newsDate'] = news_data[i]['pubDate'].split('T')[0]
                news_payload['link'] = news_data[i]['link']
                write_to_txt(news_payload)
                # print(news_payload)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)


def economicTimesNewsFinancial():
    try:
        news_rss_feed = "https://bfsi.economictimes.indiatimes.com/rss/financial-services"
        resp = requests.get(news_rss_feed)
        xml_file = resp.text
        data_dict = xmltodict.parse(xml_file)
        news_data = data_dict['rss']['channel']['item']
        # print(news_data[0]['title'])
        for i in range(len(news_data)):
            try:
                news_payload['heading'] = news_data[i]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                    "\u2013", "")
                news_payload['newsBody'] = news_data[i]['description']
                news_payload['newsDate'] = news_data[i]['pubDate'].split('T')[0]
                news_payload['link'] = news_data[i]['link']
                write_to_txt(news_payload)
                #print(news_payload)
            except Exception as e:
                print(e)
    except Exception as e:
        print(e)


def businessStandard():
    try:
        header = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        news_rss_feed = "https://www.business-standard.com/rss/industry-217.rss"
        resp = requests.get(news_rss_feed, headers=header)
        if resp.status_code == 200:
            xml_file = resp.text
            data_dict = xmltodict.parse(xml_file)
            news_data = data_dict['rss']['channel']['item']

            for i in range(len(news_data)):
                try:
                    date = news_data[i]['pubDate']
                    Date = datetime.datetime.strptime(date[5:16], '%d %b %Y').strftime('%Y-%m-%d')
                    news_payload['heading'] = news_data[i]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                        "\u2013", "")
                    news_payload['newsBody'] = news_data[i]['description']
                    news_payload['newsDate'] = Date
                    news_payload['link'] = news_data[i]['link']
                    write_to_txt(news_payload)
                    # print(news_payload)
                except Exception as e:
                    print(e)
        else:
            print("Failed to fetch RSS feed:", resp.status_code)
    except Exception as e:
        print(e)

############################# businessStandardBanking ##################
def businessStandardBanking():
    try:
        header = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
        news_rss_feed = "https://www.business-standard.com/rss/industry/banking-21703.rss"
        resp = requests.get(news_rss_feed, headers=header)
        if resp.status_code == 200:
            xml_file = resp.text
            data_dict = xmltodict.parse(xml_file)
            news_data = data_dict['rss']['channel']['item']

            for i in range(len(news_data)):
                try:
                    date = news_data[i]['pubDate']
                    Date = datetime.datetime.strptime(date[5:16], '%d %b %Y').strftime('%Y-%m-%d')
                    news_payload['heading'] = news_data[i]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                        "\u2013", "")
                    news_payload['newsBody'] = news_data[i]['description']
                    news_payload['newsDate'] = Date
                    news_payload['link'] = news_data[i]['link']
                    write_to_txt(news_payload)
                    # print(news_payload)
                except Exception as e:
                    print(e)
        else:
            print("Failed to fetch RSS feed:", resp.status_code)
    except Exception as e:
        print(e)
    
################################## google news ########################

def googelNews():
    try:
        news_rss_feed = "https://news.google.com/rss/search?q=%50s&hl=en-IN&gl=IN&ceid=IN:en"
        resp = requests.get(news_rss_feed)
        xml_file = resp.text
        data_dict = xmltodict.parse(xml_file)
        news_data = data_dict['rss']['channel']['item']
        for news in range(len(news_data)):
            date = " ".join(news_data[news]['pubDate'].split(' ')[1:4])
            Date = datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
            try:
                responce = requests.get(news_data[news]['link'])
                soup1 = bs(responce.content, 'html.parser')
                bodys = soup1.find_all(class_='FirstEle')
                for body in bodys:
                    Body = body.find_all('p')
                    allBody = []
                    for b in Body:
                        bodyText = b.text.replace("\u2019", "").replace("\n", "").replace("\t", "").strip()
                        allBody.append(bodyText)
                    newsBody = " ".join(allBody)

                news_payload['heading'] = news_data[news]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                    "\u2013", "")
                news_payload['newsBody'] = newsBody
                news_payload['newsDate'] = Date
                news_payload['link'] = news_data[news]['link']
                write_to_txt(news_payload)
            except:
                pass
    except Exception as e:
        print(e)

########################################### ft.com ######################################

def ftNews():
    try:
        news_rss_feed = "https://www.ft.com/world?format=rss"
        resp = requests.get(news_rss_feed)
        xml_file = resp.text
        data_dict = xmltodict.parse(xml_file)
        news_data = data_dict['rss']['channel']['item']
        for news in range(len(news_data)):
            date = " ".join(news_data[news]['pubDate'].split(' ')[1:4])
            Date = datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
            try:
                news_payload['heading'] = news_data[news]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                    "\u2013", "").strip()
                news_payload['newsBody'] = news_data[news]['description'].replace("\u2018", "").replace("\u2019",
                                                                                                        "").replace(
                    "\u2013",
                    "").replace(
                    "\u00a3", "").replace("\u00a0", "").replace("\u200a", "").strip()
                news_payload['newsDate'] = Date
                news_payload['link'] = news_data[news]['link']
                write_to_txt(news_payload)
            except:
                pass
    except Exception as e:
        print(e)


####################################### Thehindubusinessline ######################################
def thehindubusinessline():
    try:
        news_rss_feed = "https://www.thehindubusinessline.com/companies/feeder/default.rss"
        resp = requests.get(news_rss_feed)
        xml_file = resp.text
        data_dict = xmltodict.parse(xml_file)
        news_data = data_dict['rss']['channel']['item']
        for news in range(len(news_data)):
            date = " ".join(news_data[news]['pubDate'].split(' ')[1:4])
            Date = datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')
            try:
                news_payload['heading'] = news_data[news]['title'].replace("\u2018", "").replace("\u2019", "").replace(
                    "\u2013", "").strip()
                news_payload['newsBody'] = news_data[news]['description'].replace("\u2018", "").replace("\u2019",
                                                                                                        "").replace(
                    "\u2013",
                    "").replace(
                    "\u00a3", "").replace("\u00a0", "").replace("\u200a", "").strip()
                news_payload['newsDate'] = Date
                news_payload['link'] = news_data[news]['link']
                write_to_txt(news_payload)
            except:
                pass
    except Exception as e:
        print(e)


def morning_job():
    for i in range(1):
        insolvencynews()
        print("Insolvency News Done")
        time.sleep(5)
        moneycontrolNews()
        print("Money Control News Done")
        time.sleep(5)
        timeOfIndiaNews()
        print("Times of India News Done")
        time.sleep(5)
        cnbcNews()
        print("CNBC News Done")
        time.sleep(5)
        livemintNews()
        print("Live-Mint News Done")
        time.sleep(5)
        economicTimesNewsbfsi()
        print("economic Times bfsi News Done")
        time.sleep(5)
        livemintNews1()
        print("Live-Mint News Done")
        time.sleep(5)
        economicTimesNews()
        print("Economic Times News Done")
        time.sleep(5)
        economicTimesNews1()
        print("Economic Times News Done")
        time.sleep(5)
        businessStandard()
        print("business Standard News Done")
        time.sleep(5)
        businessStandardBanking()
        print("business Standard Banking News Done")
        time.sleep(5)
        economicTimesNewsFinancial()
        print("Economic Financial News Done")
        time.sleep(5)
        ftNews()
        print("Ft News Done")
        time.sleep(5)
        googelNews()
        print("Google News Done")
        time.sleep(5)
        thehindubusinessline()
        print("the hindubusiness line News Done")
        print("All Rss Feeds News Collection Done")
        break


def evening_job():
    for i in range(1):
        insolvencynews()
        print("Insolvency News Done")
        time.sleep(5)
        moneycontrolNews()
        print("Money Control News Done")
        time.sleep(5)
        timeOfIndiaNews()
        print("Times of India News Done")
        time.sleep(5)
        cnbcNews()
        print("CNBC News Done")
        time.sleep(5)
        livemintNews()
        print("Live-Mint News Done")
        time.sleep(5)
        livemintNews1()
        print("Live-Mint News Done")
        time.sleep(5)
        economicTimesNewsbfsi()
        print("economic Times bfsi News Done")
        time.sleep(5)
        economicTimesNews()
        print("Economic Times News Done")
        time.sleep(5)
        economicTimesNewsFinancial()
        print("Economic Financial News Done")
        time.sleep(5)
        economicTimesNews1()
        print("Economic Times News Done")
        time.sleep(5)
        businessStandard()
        print("business Standard News Done")
        time.sleep(5)
        businessStandardBanking()
        print("business Standard Banking News Done")
        time.sleep(5)
        ftNews()
        print("Ft News Done")
        time.sleep(5)
        googelNews()
        print("Google News Done")
        time.sleep(5)
        thehindubusinessline()
        print("the hindubusiness line News Done")
        print("All Rss Feeds News Collection Done")
        break


schedule.every().day.at("08:00").do(morning_job)

# Schedule the evening job to run at 7:00 PM
schedule.every().day.at("16:03").do(evening_job)

while True:
    schedule.run_pending()
    time.sleep(1)
