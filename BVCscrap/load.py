from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import json
import datetime
from .utils import *

def loadata(name, start=None, end=None, decode="utf-8"):
    """
    Load Data with Playwright to avoid blocking
    """
    code = get_code(name)
    if not code and name not in ["MASI", "MSI20"]:
        raise ValueError(f"Unknown name or missing ISIN for: {name}")

    if name not in ["MASI", "MSI20"]:
        if not start or not end:
            start = '2011-09-18'
            end = str(datetime.datetime.today().date())
        link = f"https://medias24.com/content/api?method=getPriceHistory&ISIN={code}&format=json&from={start}&to={end}"
    else:
        if name == "MASI":
            link = "https://medias24.com/content/api?method=getMasiHistory&periode=10y&format=json"
        else:
            link = "https://medias24.com/content/api?method=getIndexHistory&ISIN=msi20&periode=10y&format=json"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=60000)
            
            # Attendre que le contenu soit chargé
            page.wait_for_timeout(3000)
            
            # Essayer de récupérer le contenu JSON
            json_text = page.content()
            
            # Si c'est une page HTML avec un pre, extraire le texte
            if '<pre>' in json_text:
                json_text = page.locator('pre').inner_text(timeout=30000)
            
            browser.close()
            
            if not json_text.strip().startswith('{'):
                raise ValueError(f"Bad API response for {name}: Not a valid JSON")
            
            data = get_data(json_text, decode)
            
            if name in ["MASI", "MSI20"] and start and end:
                data = produce_data(data, start, end)
                
            return data
            
    except Exception as e:
        raise ValueError(f"Error fetching data for {name}: {str(e)}")

def loadata_patch(name, start=None, end=None, decode="utf-8"):
    """
    Patch version with Playwright
    """
    code = get_code(name)
    
    # Construire l'URL
    if name not in ["MASI", "MSI20"]:
        if not (start and end):
            start = '2011-09-18'
            end = str(datetime.date.today())
        link = f"https://medias24.com/content/api?method=getPriceHistory&ISIN={code}&format=json&from={start}&to={end}"
    else:
        if name == "MASI":
            link = "https://medias24.com/content/api?method=getMasiHistory&periode=10y&format=json"
        else:
            link = "https://medias24.com/content/api?method=getIndexHistory&ISIN=msi20&periode=10y&format=json"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=60000)
            page.wait_for_timeout(3000)
            
            json_text = page.content()
            if '<pre>' in json_text:
                json_text = page.locator('pre').inner_text(timeout=30000)
            
            browser.close()

            # Charger le JSON en DataFrame
            table = json.loads(json_text.encode().decode(decode))
            df = pd.DataFrame(table["result"])

            # Renommer selon nombre de colonnes
            if name in ["MASI", "MSI20"] and df.shape[1] == 2:
                df.columns = ["Date", "Value"]
            else:
                df.columns = ["Date", "Value", "Min", "Max", "Variation", "Volume"]

            # Conversion de la colonne Date
            if pd.api.types.is_numeric_dtype(df["Date"]):
                df["Date"] = pd.to_datetime(df["Date"], unit="s", errors="coerce")
            else:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

            return df.set_index("Date")
            
    except Exception as e:
        raise ValueError(f"Error in loadata_patch for {name}: {str(e)}")

def loadmany(*args, start=None, end=None, feature="Value", decode="utf-8"):
    """
    Load the data of many equities with Playwright
    """
    if type(args[0]) == list:
        args = args[0]
    
    data = pd.DataFrame(columns=args)
    for stock in args:
        value = loadata(stock, start, end, decode)
        data[stock] = value[feature]
    return data

def getIntraday(name, decode="utf-8"):
    """
    Load intraday data with Playwright
    """
    if name != "MASI" and name != "MSI20":
        code = get_code(name)
        link = f"https://medias24.com/content/api?method=getStockIntraday&ISIN={code}&format=json"
    elif name == "MASI":
        link = "https://medias24.com/content/api?method=getMarketIntraday&format=json"
    else:
        link = "https://medias24.com/content/api?method=getIndexIntraday&ISIN=msi20&format=json"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=60000)
            page.wait_for_timeout(3000)
            
            json_text = page.content()
            if '<pre>' in json_text:
                json_text = page.locator('pre').inner_text(timeout=30000)
            
            browser.close()
            
            # Utiliser la fonction intradata existante
            soup = BeautifulSoup(json_text, 'html.parser')
            data = intradata(soup, decode)
            return data
            
    except Exception as e:
        raise ValueError(f"Error fetching intraday data for {name}: {str(e)}")
