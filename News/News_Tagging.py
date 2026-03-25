################################ Category mapping and type tag mapping function ##################################
import json
import csv
import re
import time
import openai
import requests
import pandas as pd
from bs4 import BeautifulSoup
# from googlenewsdecoder import GoogleDecoder
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
    with open(r'D:\Nexensus_Projects\News\news_type_tag.csv', mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row['Category'] == category:
                return row['type_tag'].title()
        return "Other"