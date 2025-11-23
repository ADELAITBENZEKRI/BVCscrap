from bs4 import BeautifulSoup
import pandas as pd
import json
import datetime
from .Notation import *
from playwright.sync_api import sync_playwright

def fetch_page_content(url, wait=3000):
    """Ouvre l'URL avec Playwright et retourne le HTML."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=90000)
            page.wait_for_timeout(wait)  # attendre que la page se charge
            html = page.content()
            browser.close()
        return html
    except Exception as e:
        print(f"Erreur fetch_page_content: {e}")
        return None

def getCours(name):
    code = get_valeur(name)
    link = f"https://www.casablanca-bourse.com/bourseweb/Societe-Cote.aspx?codeValeur={code}&cat=7"
    html = fetch_page_content(link)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        return getTables(soup)
    return None

def getKeyIndicators(name, decode='utf-8'):
    code = get_valeur(name)
    link = f"https://www.casablanca-bourse.com/bourseweb/Societe-Cote.aspx?codeValeur={code}&cat=7"
    html = fetch_page_content(link)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        return getTablesFich(soup)
    return None

def getDividend(name, decode='utf-8'):
    code = get_valeur(name)
    link = f"https://www.casablanca-bourse.com/bourseweb/Societe-Cote.aspx?codeValeur={code}&cat=7"
    html = fetch_page_content(link)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        return getDivi(soup)
    return None

def getIndex():
    link = "https://www.casablanca-bourse.com/bourseweb/Activite-marche.aspx?Cat=22&IdLink=297"
    html = fetch_page_content(link)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        return getAllIndex(soup)
    return None

def getPond():
    link = "https://www.casablanca-bourse.com/bourseweb/indice-ponderation.aspx?Cat=22&IdLink=298"
    html = fetch_page_content(link)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        return getPondval(soup)
    return None

def getIndexRecap():
    link = "https://www.casablanca-bourse.com/bourseweb/index.aspx"
    html = fetch_page_content(link)
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        return getIndiceRecapScrap(soup)
    return None

# Les fonctions JSON/DataFrame restent inchangées
def get_data(json_text, decode='utf-8'):
    table = json.loads(json_text.encode().decode(decode))
    row_data = pd.DataFrame(table["result"])
    row_data.columns = ["Date", "Value", "Min", "Max", "Variation", "Volume"]
    date = row_data['Date']
    row_data.drop(['Date'], axis=1, inplace=True)
    row_data.index = date
    return row_data

def intradata(json_text, decode='utf-8'):
    table = json.loads(json_text.encode().decode(decode))
    row_data = pd.DataFrame(table["result"][0])
    index = row_data['labels'].values
    row_data.drop(['labels'], axis=1, inplace=True)
    row_data.index = index
    row_data.columns = ["Value"]
    return row_data

def produce_data(data, start, end):
    start = pd.to_datetime(start).date()
    end = pd.to_datetime(end).date()
    return data.loc[start:end]
