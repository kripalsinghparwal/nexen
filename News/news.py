import json
import csv
import re
import time
import openai
import requests
import pandas as pd
from bs4 import BeautifulSoup
from googlenewsdecoder import GoogleDecoder
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from nltk import pos_tag, word_tokenize
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import requests
import urllib.parse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

project_id = 124

LABOUR_NEWS_TAG = ["Labour Strikes", "Strikes", "Quits", "unrest", "agitation", "lock out", "termination", "ESI",
                   "unrest", "Fired", "Quit", "suicide", "protest", "injury", "injured", "salary", "EPF", "attrition",
                   "Dispute", "harassment", "protests", "Strike"]

RAID_NEWS_TAG = ["Raid", "Raids", "Raided"]

RESIGNATION_NEWS_TAG = ["Resign", "Resigns", "Resigned", "Resignation", "resigning", "management changes", "terminate"]

FRAUD_REGULATORY_ACTION_NEWS_TAG = ["Fraud", "Embezzlement", "Money laundering", "Syphoning", "CBI inquiry", "Bribery",
                                    "Political Influence", "SEBI proceeding", "regulatory action", "Penalties", "Fines",
                                    "Penalty", "Cheating", "NPA", "Default", "Criminal", "Breach", "Scam", "Arrest",
                                    "Warrant Issued", "Probe", "Fined", "Misappropriation", "Inspection",
                                    "Complaint against", "insolvency", "I T notice", "Hawala", "CBI", "FIR", "Jail",
                                    "Illeagal", "Forging", "booked", "scrutinize", "land grab", "RBI", "CBI", "SEBI",
                                    "IRDA", "EXIM", "Fraudulent", "theft", "theif", "bankruptcy", "Black Money",
                                    "Bribe",
                                    "Central Bureau of Investigation", "charge sheet", "chargesheet", "cheat",
                                    "corrupt",
                                    "corruption", "custody", "Due", "Dues", "evading", "Fine", "Fined", "forgery",
                                    "illegal", "Inspect", "Inspector", "investigation", "Labour Dispute", "land grab",
                                    "non compliance", "notices", "Offered Money", "Penalized", "police",
                                    "Serious Fraud",
                                    "SFIO", "violation", "Whistleblower"]

MARKET_STOCK_MOVEMENT_NEWS_TAG = ["plunges", "Slowdown", "Delay", "Delayed", "downgrade", "downgraded", "losses",
                                  "loss", "SEBI", "profit decline", "Wind Up", "plummets", "Decline", "exits", "low",
                                  "pledge", "plummet", "SELL Recommendation", "stake sale", "stress", "suspends",
                                  "worst", "sell", "fall", "down", "drop", "falls", "sells"]

LITIGATION_NEWS_TAG = ["Case Registered", "Court Denies", "Court Rejects", "contempt", "Registered Case",
                       "Settlement", "allegations", "High Court", "District Court", "Lower Court", "Supreme Court",
                       "Judgement", "copyrights", "defamation", "DRT", "NCLT"]

WHISTLEBLOWER_NEWS_TAG = ["Whistleblower"]

ACCIDENT_NEWS_TAG = ["Accident", "Fire", "Death", "Died", "Passed Away", "Die", "casualty", "mishap", "Blast",
                     "casualties", "Died", "killed", "kills", "passes away", "shut down"]

# # Load the sentiment words from CSV
# csv_file_path = r'D:\Ronit_Projects\DailyNews\DailyNews_4\Related_files\SentimentalWords.csv'
# df_csv = pd.read_csv(csv_file_path)
# sentiment_mapping = {'Negative': -1, 'Neutral': 0, 'Positive': 1}
# word_sentiments_csv = dict(zip(df_csv['text'], df_csv['sentiment'].map(sentiment_mapping)))
# sia = SentimentIntensityAnalyzer()
#
#
# # Function to get sentence sentiment
# def get_sentence_sentiment(sentence):
#     words = word_tokenize(sentence.lower())
#     csv_sentiment = sum(word_sentiments_csv.get(word, 0) for word in words)
#     # print("csv_sentiment : ", csv_sentiment)
#     nlp_sentiment = sia.polarity_scores(sentence)['compound']
#     # print("nlp_sentiment : ", nlp_sentiment)
#     combined_sentiment = csv_sentiment + nlp_sentiment
#
#     if combined_sentiment > 0:
#         return 'Positive'
#     elif combined_sentiment < 0:
#         return 'Negative'
#     else:
#         return 'Neutral'







def call_openai_model(prompt, model, retries, timeout):
    for attempt in range(1, retries + 1):
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                timeout=timeout
            )

            content = response['choices'][0]['message']['content'].strip()

            # Remove markdown-wrapped JSON if present
            if content.startswith("```"):
                content = content.split("```")[1].strip()
                if content.startswith("json"):
                    content = content[len("json"):].strip()

            result = json.loads(content)
            return result["sentiment"]

        except json.JSONDecodeError:
            raise ValueError(f"⚠️ Invalid JSON returned by {model}:\n{content}")

        except (openai.error.Timeout,
                openai.error.APIConnectionError,
                openai.error.RateLimitError,
                openai.error.ServiceUnavailableError,
                openai.error.OpenAIError,
                OSError) as e:

            print(f"⏳ [{model}] Attempt {attempt}/{retries} failed: {e}")
            if attempt < retries:
                time.sleep(5)
            else:
                return None  # Allow fallback

        except Exception as e:
            raise RuntimeError(f"❌ Unexpected error with {model}: {e}")

    return None


def get_sentence_sentiment(sentence, retries=5, timeout=60):
    prompt = f"""
    Classify the following news sentence for sentiment.

    Choose strictly one of: Positive, Negative, or Neutral.

    Respond strictly in this JSON format:
    {{
      "sentiment": "Your Sentiment"
    }}

    Sentence: "{sentence}"
    Respond only with the JSON. No explanation.
    """

    # Primary: gpt-3.5-turbo
    sentiment = call_openai_model(prompt, "gpt-3.5-turbo", retries, timeout)

    # Fallback: gpt-4o
    if sentiment is None:
        print("🔁 Falling back to gpt-4o...")
        sentiment = call_openai_model(prompt, "gpt-4o", retries, timeout)

    if sentiment is None:
        raise TimeoutError("❌ Request failed on both gpt-3.5-turbo and gpt-4o after multiple retries.")

    return sentiment


def get_category_tag(sentence):
    define_tags = (LABOUR_NEWS_TAG + RAID_NEWS_TAG + RESIGNATION_NEWS_TAG + FRAUD_REGULATORY_ACTION_NEWS_TAG +
                   MARKET_STOCK_MOVEMENT_NEWS_TAG + LITIGATION_NEWS_TAG + WHISTLEBLOWER_NEWS_TAG + ACCIDENT_NEWS_TAG)

    tokens = word_tokenize(sentence)
    tagged_words = pos_tag(tokens)

    verbs = [word for word, pos in tagged_words if pos.startswith('V')]
    adjectives = [word for word, pos in tagged_words if pos.startswith('J')]
    adverbs = [word for word, pos in tagged_words if pos.startswith('R')]
    nouns = [word for word, pos in tagged_words if pos.startswith('N')]
    all_tags = verbs + adjectives + adverbs + nouns
    filtered_tags = [tag.title() for tag in all_tags if tag.title() in define_tags or tag in define_tags]

    if filtered_tags:
        return filtered_tags[0]
    return 'Other'


def get_type_tag(category):
    with open(r'D:\\News\\input\\news_type_tag.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Category'] == category:
                return row['type_tag'].title()
        return "Other"


class GoogleRSSFEEDScraper:
    def __init__(self):
        self.data = []
        self.decoder = GoogleDecoder()

    def parse_date(self, date_str):
        try:
            date_str = date_str.replace('GMT', '+0000')
            date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
            return date_obj
        except ValueError:
            return None           

    def extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text

    def get_pet_resp_names(self, Comp):
        """Extract petitioner and respondent names from the text."""
        pattern = r'M/S\s+([A-Za-z\s]+(?:PVT\.?\s+LTD\.?|PRIVATE\s+LTD\.?|LLP\.?))'
        company_names = re.findall(pattern, Comp, re.IGNORECASE)
        return company_names
        
    def decode_link(self, link):
        """Decodes Google News RSS link to get the original URL."""
        if len(link) > 1000:
            original_url = self.decoder.decode_google_news_url(link)
            return original_url.get('decoded_url', link)
        else:
            return link

    def news_data(self, news_business, url, Comp, Cin):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            response = requests.get(url, headers=headers)
            # print(url)
            # print(response)
            response.raise_for_status()
            xml_content = response.content
            root = ET.fromstring(xml_content)
            items = root.findall('.//item')

            # print(items)
            # Define date range (this month and previous month)
            today = datetime.today()
            # start_of_current_month = today.replace(day=1)
            # start_of_previous_month = (start_of_current_month - timedelta(days=1)).replace(day=1)
            # start_of_previous_month = start_of_current_month - relativedelta(months=18)
            start_of_previous_month = today - timedelta(days=360)  # for 3 days  


            for item in items:
                try:
                    title = item.find('title').text.strip() if item.find('title') is not None and item.find(
                        'title').text else 'No title'
                    link = item.find('link').text.strip() if item.find('link') is not None and item.find(
                        'link').text else 'No link'
                    description_html = item.find('description').text.strip() if item.find(
                        'description') is not None and item.find('description').text else 'No description'
                    description_text = self.extract_text_from_html(description_html)
                    pubDate = item.find('pubDate').text.strip() if item.find('pubDate') is not None and item.find(
                        'pubDate').text else 'No pubDate'
                    date_obj = self.parse_date(pubDate)
                    if date_obj:
                        # Convert aware datetime (with timezone) to naive (without timezone)
                        date_obj_naive = date_obj.replace(tzinfo=None)

                        # Only add news items that are within the current or previous month
                        if start_of_previous_month <= date_obj_naive < today:
                            formatted_date = date_obj_naive.strftime('%Y-%m-%d')
                            print("Date : ", formatted_date)
                            category = get_category_tag(title)
                            sf_comp_name = Comp.title()

                            CompName = sf_comp_name.replace("Limited", "").replace("Ltd", "").replace("Private",
                                                                                                      "").replace("Pvt",
                                                                                                                  "").replace(
                                ".", "").strip()
                            modify_description = description_text.replace("&", "And")
                            modify_title = title.replace("&", "And")
                            print("Company name : ", CompName)
                            # print("title : ", modify_title)
                            # print("description : ", modify_description)
                            # print("link : ", link)
                            if CompName in modify_title.title() or CompName in modify_description.title():
                                # if get_sentence_sentiment(title) == "Negative":
                                # if CompName:
                                self.data.append({
                                    'companyName': Comp,
                                    'cin': Cin,
                                    'heading': title,
                                    'newsDate': formatted_date,
                                    # 'newsBody': description_text,
                                    'link': self.decode_link(link),
                                    'category': category,
                                    'typeTag': get_type_tag(category),
                                    # 'sentiment': get_sentence_sentiment(title)
                                    'sentiment': None
                                })
                            else:
                                print("Company name not found in news title or description")

                except AttributeError as e:
                    print(f"Error processing item: {e}")
            self.save_to_file(news_business)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching the URL: {e}")
            
        except ET.ParseError as e:
            print(f"Error parsing the XML: {e}")

    def save_to_file(self, news_name):
        today = datetime.today().strftime(r"%d%m%Y")
        file_path = rf"D:\News\output\NEXENSUS_{news_name}_{today}.txt"
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                for entry in self.data:
                    file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"Data successfully written to {file_path}")
        except IOError as e:
            print(f"Error writing to file: {e}")


def google_rssfeed_run():
    scraper = GoogleRSSFEEDScraper()
    # try:
    #     requests.post(f"https://nexensus.club/jobautomation//api/dashboard-data/{project_id}/{urllib.parse.quote('Start Project')}/", verify=False)
    # except Exception as e:
    #     print(e)
    ###################################################################################################################################
    # company_file_path = r'D:\Ronit_Projects\DailyNews\DailyNews_4\Company_list\companies_part_4.csv'
    # df = pd.read_csv(company_file_path, encoding='ISO-8859-1')
    #
    # cins = df['cin'].to_list()[0:]
    # names = df['name'].to_list()[0:]
    # try:
    #     requests.post(f"https://nexensus.club/jobautomation//api/dashboard-data/{project_id}/{urllib.parse.quote('Data Collecting')}/", verify=False)
    # except Exception as e:
    #     print(e)
    # for i, cin in enumerate(cins):
    #     print("Count : ", i)
    #     cin = cin
    #     company_name = names[i].replace("&", "and")
    #     print(cin, company_name)
    #     scraper.news_data('Google_RSSFEED', f'https://news.google.com/rss/search?q={company_name}', company_name, cin)
    #     time.sleep(1)
    ###################################################################################################################################

    df = pd.read_csv(r'D:\\News\\input\\filtered_above_50L.csv')
    cins = df['cin'].to_list()[:10002]
    names = df['company_name'].to_list()[:10002]
    # url = "https://nexensus.co.in/client/client_companies"

    
    for i, cin in enumerate(cins) :
        company_name = names[i]
        if "business standard" in str(company_name).lower():
            pass
        else:
            scraper.news_data('Google_RSSFEED', f'https://news.google.com/rss/search?q={company_name}', company_name, cin)
            time.sleep(1)
    
    ###############################################################################
    print("=================== Google RSSFEED Completed ====================")


if __name__ == "__main__":
    google_rssfeed_run()
