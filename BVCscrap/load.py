import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import json
import datetime
import ssl
import urllib3
from .utils import *

# Désactiver les warnings SSL et configurer le contexte
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration globale du scraper
def create_secure_scraper():
    """Crée un scraper configuré pour contourner les problèmes SSL"""
    return cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        },
        delay=10,
        interpreter='nodejs'
    )

# Scraper global
SCRAPER = create_secure_scraper()

def loadata(name, start=None, end=None, decode="utf-8"):
    """
    Load Data 
    Inputs: 
        name   | string | You must respect the notation. To see the notation see BVCscrap.notation()
        start  | string "YYYY-MM-DD" | starting date Must respect the notation
        end    | string "YYYY-MM-DD" | Must respect the notation
        decode | string | type of decoder. default value is utf-8. If it is not working use utf-8-sig
    Outputs:
        pandas.DataFrame (4 columns) | Value, Min, Max, Variation, Volume
    """
    code = get_code(name)
    if not code and name not in ["MASI", "MSI20"]:
        raise ValueError(f"Unknown name or missing ISIN for: {name}")

    # Construction de l'URL
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
        # Utilisation du scraper global avec gestion SSL
        request_data = SCRAPER.get(link, verify=False, timeout=30)
        
        if request_data.status_code != 200:
            raise ValueError(f"HTTP Error {request_data.status_code} for {name}")
            
        if not request_data.text.strip().startswith('{'):
            raise ValueError(f"Bad API response for {name}: {request_data.text[:150]}")

        data = get_data(request_data.text, decode)

        if name in ["MASI", "MSI20"] and start and end:
            data = produce_data(data, start, end)

        return data
        
    except Exception as e:
        raise Exception(f"Error loading data for {name}: {str(e)}")

def loadata_patch(name, start=None, end=None, decode="utf-8"):
    """
    Patch de bvc.loadata() qui gère le cas MASI/MSI20 avec dates en epoch ms.
    """
    code = get_code(name)
    
    # Construction de l'URL
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
        # Utilisation du scraper global
        resp = SCRAPER.get(link, verify=False, timeout=30)
        if resp.status_code != 200 or not resp.text.strip().startswith('{'):
            raise ValueError(f"Bad API response for {name}: {resp.status_code}")

        # Charger le JSON
        table = json.loads(resp.text.encode().decode(decode))
        df = pd.DataFrame(table["result"])

        # Renommer les colonnes
        if name in ["MASI", "MSI20"] and df.shape[1] == 2:
            df.columns = ["Date", "Value"]
        else:
            df.columns = ["Date", "Value", "Min", "Max", "Variation", "Volume"]

        # Conversion de la colonne Date
        if pd.api.types.is_numeric_dtype(df["Date"]):
            df["Date"] = pd.to_datetime(df["Date"], unit="ms", errors="coerce")  # Changé de 's' à 'ms'
        else:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        return df.set_index("Date")
        
    except Exception as e:
        raise Exception(f"Error in loadata_patch for {name}: {str(e)}")

def loadmany(*args, start=None, end=None, feature="Value", decode="utf-8"):
    """
    Load the data of many equities  
    Inputs: 
        *args  | strings | You must respect the notation. To see the notation see BVCscrap.notation
        start  | string "YYYY-MM-DD" | starting date Must respect the notation
        end    | string "YYYY-MM-DD" | Must respect the notation
        feature| string | Variable : Value, Min, Max, Variation or Volume
        decode | string | type of decoder. default value is utf-8. If it is not working use utf-8-sig
    Outputs:
        pandas.DataFrame (len(args) columns) | close prices of selected equities
    """
    if type(args[0]) == list:
        args = args[0]
        
    data = pd.DataFrame(columns=args)
    
    for stock in args:
        try:
            value = loadata(stock, start, end, decode)
            data[stock] = value[feature]
        except Exception as e:
            print(f"Warning: Could not load data for {stock}: {str(e)}")
            continue
            
    return data

def getIntraday(name, decode="utf-8"):
    """
    Load intraday data
    Inputs: 
        - Name: stock, index 
        - decode: default value is "utf-8", if it is not working use : "utf-8-sig"
    """
    try:
        # Construction de l'URL
        if name not in ["MASI", "MSI20"]:
            code = get_code(name)
            if not code:
                raise ValueError(f"Code not found for: {name}")
            link = f"https://medias24.com/content/api?method=getStockIntraday&ISIN={code}&format=json"
        elif name == "MASI":
            link = "https://medias24.com/content/api?method=getMarketIntraday&format=json"
        else:
            link = "https://medias24.com/content/api?method=getIndexIntraday&ISIN=msi20&format=json"

        # Utilisation du scraper global avec headers
        request_data = SCRAPER.get(
            link, 
            verify=False,
            timeout=30,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Referer': 'https://medias24.com/'
            }
        )
        
        if request_data.status_code != 200:
            raise ValueError(f"HTTP Error: {request_data.status_code}")
            
        # Vérification du contenu JSON
        if not request_data.text.strip().startswith(('{', '[')):
            raise ValueError(f"Invalid JSON response: {request_data.text[:100]}")
            
        soup = BeautifulSoup(request_data.text, features="lxml")
        data = intradata(soup, decode)
        return data
        
    except cloudscraper.CloudflareChallengeError as e:
        raise Exception(f"Cloudflare challenge failed: {str(e)}")
    except json.JSONDecodeError as e:
        raise Exception(f"JSON decode error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error fetching intraday data for {name}: {str(e)}")

def getCours(name, start=None, end=None, decode="utf-8"):
    """
    Fonction wrapper pour récupérer les cours - version corrigée SSL
    """
    return loadata(name, start, end, decode)

# Fonction de test
def test_connection():
    """Teste la connexion avec les différents endpoints"""
    test_cases = [
        "BOA",
        "MASI", 
        "MSI20"
    ]
    
    for test_case in test_cases:
        try:
            print(f"Testing {test_case}...")
            if test_case in ["MASI", "MSI20"]:
                data = getIntraday(test_case)
            else:
                data = getCours(test_case)
            print(f"✓ {test_case}: SUCCESS - Shape: {data.shape}")
        except Exception as e:
            print(f"✗ {test_case}: ERROR - {str(e)}")

# Si exécuté directement
if __name__ == "__main__":
    test_connection()
	
