from playwright.sync_api import sync_playwright
import pandas as pd
import json
import datetime
from .utils import get_code, intradata  # vérifier que utils contient bien ces fonctions


def fetch_json_with_playwright(url, decode="utf-8"):
    """
    Fonction utilitaire Playwright : charge une URL API JSON
    et renvoie un texte JSON brut ou None.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=90000)
            json_text = page.locator("pre").inner_text(timeout=30000)
            browser.close()
            return json_text.encode().decode(decode)
    except Exception as e:
        print(f"[Playwright] Erreur lors du chargement: {url}\n{e}")
        return None


def loadata(name, start=None, end=None, decode="utf-8"):
    """
    Load Data using Playwright instead of cloudscraper
    Returns: DataFrame indexed by date
    """

    code = get_code(name)
    if not code and name not in ["MASI", "MSI20"]:
        raise ValueError(f"Unknown name or missing ISIN for: {name}")

    if name not in ["MASI", "MSI20"]:
        if not (start and end):
            start = '2011-09-18'
            end = str(datetime.date.today())

        url = (
            f"https://medias24.com/content/api?method=getPriceHistory"
            f"&ISIN={code}&format=json&from={start}&to={end}"
        )
    else:
        url = (
            "https://medias24.com/content/api?"
            f"method={'getMasiHistory' if name=='MASI' else 'getIndexHistory'}"
            f"{'&ISIN=msi20' if name=='MSI20' else ''}"
            "&periode=10y&format=json"
        )

    json_text = fetch_json_with_playwright(url, decode)
    if not json_text:
        raise ValueError(f"Erreur API Playwright pour : {name}")

    data = json.loads(json_text)
    df = pd.DataFrame(data["result"])

    if name in ["MASI", "MSI20"] and df.shape[1] == 2:
        df.columns = ["Date", "Value"]
    else:
        df.columns = ["Date", "Value", "Min", "Max", "Variation", "Volume"]

    # Conversion des dates
    if pd.api.types.is_numeric_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"], unit="s", errors="coerce")
    else:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    return df.set_index("Date")


def loadata_patch(name, start=None, end=None, method="ffill", decode="utf-8"):
    """
    Version avec patch des dates manquantes.
    """
    df = loadata(name, start=start, end=end, decode=decode)

    full_index = pd.date_range(df.index.min(), df.index.max(), freq="D")
    df = df.reindex(full_index)

    if method == "interpolate":
        df = df.interpolate()
    else:
        df = df.ffill()

    df.index.name = "Date"
    return df


def loadmany(*args, start=None, end=None, feature="Value", decode="utf-8"):
    """
    Load multiple equities
    """
    if isinstance(args[0], list):
        args = args[0]

    data = pd.DataFrame(columns=args)
    for stock in args:
        df_stock = loadata(stock, start, end, decode)
        data[stock] = df_stock[feature]

    return data


def getIntraday(name, decode="utf-8"):
    """
    Load intraday data via Playwright
    """
    if name not in ["MASI", "MSI20"]:
        code = get_code(name)
        url = f"https://medias24.com/content/api?method=getStockIntraday&ISIN={code}&format=json"
    else:
        url = (
            f"https://medias24.com/content/api?method="
            f"{'getMarketIntraday' if name=='MASI' else 'getIndexIntraday'}"
            f"{'&ISIN=msi20' if name=='MSI20' else ''}&format=json"
        )

    json_text = fetch_json_with_playwright(url, decode)
    if not json_text:
        raise ValueError("Erreur dans le chargement des données intraday")

    soup_data = json.loads(json_text)
    df = intradata(soup_data, decode)

    return df
