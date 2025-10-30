import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import datetime
import time
import urllib3
from .utils import *

# Désactiver les warnings SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BVCScraper:
    def __init__(self):
        self.session = requests.Session()
        # Configuration pour éviter les problèmes SSL
        self.session.verify = False
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Referer': 'https://www.medias24.com/',
            'Origin': 'https://www.medias24.com',
        }
        self.session.headers.update(self.default_headers)
    
    def _make_request(self, url, max_retries=3):
        """Fait une requête HTTP avec gestion des retries"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 403:
                    raise Exception("Access forbidden (403)")
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 10
                    print(f"Rate limit hit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code != 200:
                    raise Exception(f"HTTP Error {response.status_code}")
                
                if not response.text.strip():
                    raise Exception("Empty response from API")
                
                return response
                
            except requests.exceptions.Timeout:
                print(f"Timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise Exception("Request timeout")
                time.sleep((attempt + 1) * 3)
                
            except Exception as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep((attempt + 1) * 2)
        
        raise Exception("Max retries exceeded")

    def _parse_json_response(self, response_text, decode="utf-8"):
        """Parse la réponse JSON"""
        try:
            return json.loads(response_text)
        except UnicodeDecodeError:
            for encoding in ['utf-8-sig', 'latin-1', 'iso-8859-1']:
                try:
                    return json.loads(response_text.encode().decode(encoding))
                except:
                    continue
            raise Exception("Could not decode API response")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON: {str(e)}")

# Instance globale
SCRAPER = BVCScraper()

def loadata(name, start=None, end=None, decode="utf-8"):
    """
    Load Data - Version simplifiée et corrigée
    """
    # Validation des inputs
    if not name:
        raise ValueError("Name cannot be empty")
    
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

    print(f"Fetching data for {name}")
    
    try:
        # Faire la requête
        response = SCRAPER._make_request(link)
        
        # Parser la réponse JSON
        json_data = SCRAPER._parse_json_response(response.text, decode)
        
        # Créer le DataFrame
        if not json_data or 'result' not in json_data:
            raise Exception("No data in API response")
        
        df = pd.DataFrame(json_data["result"])
        
        # Renommage des colonnes
        if name in ["MASI", "MSI20"] and df.shape[1] == 2:
            df.columns = ["Date", "Value"]
        else:
            if df.shape[1] == 6:
                df.columns = ["Date", "Value", "Min", "Max", "Variation", "Volume"]
            elif df.shape[1] == 2:
                df.columns = ["Date", "Value"]
        
        # Conversion des dates
        if pd.api.types.is_numeric_dtype(df["Date"]):
            if df["Date"].max() > 1e10:
                df["Date"] = pd.to_datetime(df["Date"], unit="ms", errors="coerce")
            else:
                df["Date"] = pd.to_datetime(df["Date"], unit="s", errors="coerce")
        else:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        
        df = df.dropna(subset=['Date'])
        df = df.set_index("Date")
        
        # Filtrer par dates si nécessaire
        if name in ["MASI", "MSI20"] and start and end:
            df = produce_data(df, start, end)
        
        print(f"✓ Successfully loaded {len(df)} records for {name}")
        return df
        
    except Exception as e:
        raise Exception(f"Failed to load data for {name}: {str(e)}")

def loadmany(*args, start=None, end=None, feature="Value", decode="utf-8"):
    """
    Load the data of many equities
    """
    if not args:
        raise ValueError("No stocks provided")
        
    if type(args[0]) == list:
        args = args[0]
    
    successful_data = {}
    failed_stocks = []
    
    print(f"Loading data for {len(args)} stocks")
    
    for i, stock in enumerate(args):
        try:
            print(f"Progress: {i+1}/{len(args)} - Loading {stock}...")
            
            value = loadata(stock, start, end, decode)
            
            if feature not in value.columns:
                available_features = list(value.columns)
                raise Exception(f"Feature '{feature}' not found. Available: {available_features}")
            
            successful_data[stock] = value[feature]
            print(f"✓ Successfully loaded {stock}")
            
            # Pause entre les requêtes
            if i < len(args) - 1:
                time.sleep(1)
            
        except Exception as e:
            error_msg = f"✗ Failed to load {stock}: {str(e)}"
            print(error_msg)
            failed_stocks.append((stock, str(e)))
    
    if successful_data:
        data = pd.DataFrame(successful_data)
        
        # Rapport final
        print(f"\nSUMMARY: Successful: {len(successful_data)}, Failed: {len(failed_stocks)}")
        if failed_stocks:
            for stock, error in failed_stocks:
                print(f"  - {stock}: {error}")
        
        return data
    else:
        raise Exception(f"Failed to load all stocks")

def loadata_patch(name, start=None, end=None, decode="utf-8"):
    """
    Patch de bvc.loadata()
    """
    return loadata(name, start, end, decode)

def getIntraday(name, decode="utf-8"):
    """
    Load intraday data
    """
    try:
        if name != "MASI" and name != "MSI20":
            code = get_code(name)
            if not code:
                raise ValueError(f"Unknown stock: {name}")
            link = f"https://medias24.com/content/api?method=getStockIntraday&ISIN={code}&format=json"
        elif name == "MASI":
            link = "https://medias24.com/content/api?method=getMarketIntraday&format=json"
        else:
            link = "https://medias24.com/content/api?method=getIndexIntraday&ISIN=msi20&format=json"

        response = SCRAPER._make_request(link)
        soup = BeautifulSoup(response.text, features="lxml")
        data = intradata(soup, decode)
        
        print(f"✓ Successfully loaded intraday data for {name}")
        return data
        
    except Exception as e:
        raise Exception(f"Failed to load intraday data for {name}: {str(e)}")

# Version ultra-simple sans classe
def loadata_simple(name, start=None, end=None, decode="utf-8"):
    """
    Version ultra-simplifiée sans cloudscraper
    """
    code = get_code(name)
    if not code and name not in ["MASI", "MSI20"]:
        raise ValueError(f"Unknown name: {name}")

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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(link, headers=headers, verify=False, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"HTTP Error {response.status_code}")
        
        data = json.loads(response.text)
        df = pd.DataFrame(data["result"])
        
        if name in ["MASI", "MSI20"] and df.shape[1] == 2:
            df.columns = ["Date", "Value"]
        else:
            if df.shape[1] == 6:
                df.columns = ["Date", "Value", "Min", "Max", "Variation", "Volume"]
        
        # Conversion date
        if pd.api.types.is_numeric_dtype(df["Date"]):
            df["Date"] = pd.to_datetime(df["Date"], unit="ms", errors="coerce")
        else:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        
        df = df.dropna(subset=['Date'])
        df = df.set_index("Date")
        
        if name in ["MASI", "MSI20"] and start and end:
            df = produce_data(df, start, end)
            
        return df
        
    except Exception as e:
        raise Exception(f"Error loading {name}: {str(e)}")
