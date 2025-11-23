from playwright.sync_api import sync_playwright
import pandas as pd
import json
import datetime
from .utils import *  # Assure-toi que get_code, intradata, etc. sont disponibles


def loadata(name, start=None, end=None, decode="utf-8"):
    """
    Charge les données d'une action ou d'un indice depuis medias24.com via Playwright.
    Inputs: 
        name   : string - Nom ou ISIN de l'action / indice (ex: MASI, MSI20)
        start  : string "YYYY-MM-DD" - date de début
        end    : string "YYYY-MM-DD" - date de fin
        decode : string - type d'encodage, default="utf-8"
    Outputs:
        pandas.DataFrame avec colonnes : Date, Value, Min, Max, Variation, Volume
    """
    code = get_code(name)

    # Construire l'URL
    if name not in ["MASI", "MSI20"]:
        if not start or not end:
            start = '2011-09-18'
            end = str(datetime.date.today())
        link = f"https://medias24.com/content/api?method=getPriceHistory&ISIN={code}&format=json&from={start}&to={end}"
    else:
        if name == "MASI":
            link = "https://medias24.com/content/api?method=getMasiHistory&periode=10y&format=json"
        else:  # MSI20
            link = "https://medias24.com/content/api?method=getIndexHistory&ISIN=msi20&periode=10y&format=json"

    # Requête via Playwright
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=90000)
            json_text = page.locator('pre').inner_text(timeout=30000)
            browser.close()

        # Charger le JSON en DataFrame
        data = json.loads(json_text.encode().decode(decode))
        df = pd.DataFrame(data['result'])

        # Gestion des colonnes
        if name in ["MASI", "MSI20"] and df.shape[1] == 2:
            df.columns = ["Date", "Value"]
        else:
            df.columns = ["Date", "Value", "Min", "Max", "Variation", "Volume"]

        # Conversion Date
        if pd.api.types.is_numeric_dtype(df["Date"]):
            df["Date"] = pd.to_datetime(df["Date"], unit="s", errors="coerce")
        else:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        return df.set_index("Date").sort_values("Date", ascending=False)

    except Exception as e:
        print(f"Erreur Playwright pour {name}: {e}")
        return None


def loadmany(*args, start=None, end=None, feature="Value", decode="utf-8"):
    """
    Charge les données de plusieurs actions / indices.
    Inputs:
        *args  : liste de noms ou ISIN
        start  : date de début
        end    : date de fin
        feature: variable à extraire ["Value","Min","Max","Variation","Volume"]
        decode : encodage
    Output:
        DataFrame avec colonnes pour chaque action
    """
    if type(args[0]) == list:
        args = args[0]

    data = pd.DataFrame(columns=args)

    for stock in args:
        df_stock = loadata(stock, start, end, decode)
        if df_stock is not None and feature in df_stock.columns:
            data[stock] = df_stock[feature]
        else:
            data[stock] = None

    return data


def getIntraday(name, decode="utf-8"):
    """
    Charge les données intraday d'une action ou indice via Playwright.
    """
    if name != "MASI" and name != "MSI20":
        code = get_code(name)
        link = f"https://medias24.com/content/api?method=getStockIntraday&ISIN={code}&format=json"
    elif name == "MASI":
        link = "https://medias24.com/content/api?method=getMarketIntraday&format=json"
    else:  # MSI20
        link = "https://medias24.com/content/api?method=getIndexIntraday&ISIN=msi20&format=json"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=90000)
            json_text = page.locator('pre').inner_text(timeout=30000)
            browser.close()

        soup_data = json.loads(json_text.encode().decode(decode))
        df = intradata(soup_data, decode)
        return df

    except Exception as e:
        print(f"Erreur Playwright intraday pour {name}: {e}")
        return None
