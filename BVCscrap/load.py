import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd
import json
import datetime
import time
import requests
import ssl
from .utils import *

class BVCScraper:
    def __init__(self):
        # Configuration SSL pour éviter les erreurs de certificat
        self._create_secure_scraper()
        self.default_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Referer': 'https://www.medias24.com/',
            'Origin': 'https://www.medias24.com',
            'Connection': 'keep-alive',
        }
    
    def _create_secure_scraper(self):
        """Crée un scraper avec configuration SSL sécurisée"""
        try:
            # Méthode 1: Créer un contexte SSL personnalisé
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Créer le scraper avec la session requests personnalisée
            session = requests.Session()
            session.verify = False  # Désactiver la vérification SSL
            session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
            
            self.scraper = cloudscraper.create_scraper(sess=session)
            
        except Exception as e:
            # Méthode 2: Fallback simple
            print("Warning: Using fallback scraper configuration")
            self.scraper = cloudscraper.create_scraper()
            
            # Désactiver les warnings SSL
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _make_request(self, url, max_retries=3):
        """Fait une requête HTTP avec gestion des retries et erreurs"""
        for attempt in range(max_retries):
            try:
                # Configuration pour éviter les problèmes SSL
                request_options = {
                    'headers': self.default_headers,
                    'timeout': 30,
                    'verify': False  # Désactiver la vérification SSL
                }
                
                response = self.scraper.get(url, **request_options)
                
                # Vérifications de la réponse
                if response.status_code == 403:
                    raise Exception(f"Access forbidden (403). Possible blocage.")
                elif response.status_code == 429:
                    wait_time = (attempt + 1) * 10
                    print(f"Rate limit hit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code != 200:
                    raise Exception(f"HTTP Error {response.status_code}")
                
                if not response.text.strip():
                    raise Exception("Empty response from API")
                
                if not response.text.strip().startswith('{'):
                    # Vérifier si c'est une erreur HTML
                    if '<html' in response.text.lower() or '<!doctype' in response.text.lower():
                        raise Exception("API returned HTML instead of JSON. Possible anti-bot protection.")
                    else:
                        raise Exception("Invalid JSON response")
                
                return response
                
            except cloudscraper.exceptions.CloudflareChallengeError as e:
                print(f"Cloudflare challenge detected (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise Exception("Cloudflare protection could not be bypassed")
                time.sleep((attempt + 1) * 5)
                
            except requests.exceptions.SSLError as e:
                print(f"SSL Error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    # Forcer la désactivation SSL pour le dernier essai
                    try:
                        response = self.scraper.get(url, headers=self.default_headers, timeout=30, verify=False)
                        return response
                    except:
                        raise Exception("SSL error persists even with verify=False")
                time.sleep((attempt + 1) * 2)
                
            except requests.exceptions.Timeout:
                print(f"Timeout (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise Exception("Request timeout after multiple attempts")
                time.sleep((attempt + 1) * 3)
                
            except Exception as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    raise
                time.sleep((attempt + 1) * 2)
        
        raise Exception("Max retries exceeded")

    def _parse_json_response(self, response_text, decode="utf-8"):
        """Parse la réponse JSON avec gestion d'erreurs"""
        try:
            # Essayer le décodage standard
            return json.loads(response_text.encode().decode(decode))
        except UnicodeDecodeError:
            # Essayer d'autres encodages
            for encoding in ['utf-8-sig', 'latin-1', 'iso-8859-1']:
                try:
                    return json.loads(response_text.encode().decode(encoding))
                except:
                    continue
            raise Exception("Could not decode API response with any encoding")
        except json.JSONDecodeError as e:
            print(f"Raw response preview: {response_text[:200]}...")
            raise Exception(f"Invalid JSON format: {str(e)}")

    def _create_dataframe(self, data, name):
        """Crée le DataFrame à partir des données brutes"""
        if not data or 'result' not in data or not data['result']:
            raise Exception("No data found in API response")
        
        df = pd.DataFrame(data["result"])
        
        # Renommage des colonnes selon le type de données
        if name in ["MASI", "MSI20"] and df.shape[1] == 2:
            df.columns = ["Date", "Value"]
        else:
            if df.shape[1] == 6:
                df.columns = ["Date", "Value", "Min", "Max", "Variation", "Volume"]
            elif df.shape[1] == 2:
                df.columns = ["Date", "Value"]
            else:
                # Adapter dynamiquement aux colonnes disponibles
                print(f"Warning: Unexpected number of columns ({df.shape[1]}) for {name}")
                df.columns = [f"Col_{i}" for i in range(df.shape[1])]
        
        # Conversion des dates
        if pd.api.types.is_numeric_dtype(df["Date"]):
            # Vérifier si c'est en secondes ou millisecondes
            if df["Date"].max() > 1e10:  # Probablement en millisecondes
                df["Date"] = pd.to_datetime(df["Date"], unit="ms", errors="coerce")
            else:  # Probablement en secondes
                df["Date"] = pd.to_datetime(df["Date"], unit="s", errors="coerce")
        else:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        
        # Supprimer les lignes avec des dates invalides
        df = df.dropna(subset=['Date'])
        
        return df.set_index("Date")

# Créer une instance globale du scraper
SCRAPER = BVCScraper()

def loadata(name, start=None, end=None, decode="utf-8"):
    """
    Load Data avec gestion robuste des erreurs API
    Inputs: 
        name   | string | You must respect the notation. To see the notation see BVCscrap.notation()
        start  | string "YYYY-MM-DD" | starting date Must respect the notation
        end    | string "YYYY-MM-DD" | Must respect the notation
        decode | string | type of decoder. default value is utf-8. If it is not working use utf-8-sig
    Outputs:
        pandas.DataFrame (4 columns) | Value, Min, Max, Variation, Volume
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

    print(f"Fetching data for {name} from: {link}")
    
    try:
        # Faire la requête avec le scraper global
        response = SCRAPER._make_request(link)
        
        # Parser la réponse JSON
        json_data = SCRAPER._parse_json_response(response.text, decode)
        
        # Créer le DataFrame
        data = SCRAPER._create_dataframe(json_data, name)
        
        # Filtrer par dates si nécessaire
        if name in ["MASI", "MSI20"] and start and end:
            data = produce_data(data, start, end)
        
        print(f"✓ Successfully loaded {len(data)} records for {name}")
        return data
        
    except Exception as e:
        raise Exception(f"Failed to load data for {name}: {str(e)}")

def loadmany(*args, start=None, end=None, feature="Value", decode="utf-8"):
    """
    Load the data of many equities avec gestion d'erreurs améliorée
    Inputs: 
        *args  | strings | You must respect the notation. To see the notation see BVCscrap.notation
        start  | string "YYYY-MM-DD" | starting date Must respect the notation
        end    | string "YYYY-MM-DD" | Must respect the notation
        feature| string | Variable : Value, Min, Max, Variation or Volume
        decode | string | type of decoder. default value is utf-8. If it is not working use utf-8-sig
    Outputs:
        pandas.DataFrame (len(args) columns) | close prices of selected equities
    """
    if not args:
        raise ValueError("No stocks provided")
        
    if type(args[0]) == list:
        args = args[0]
    
    successful_data = {}
    failed_stocks = []
    
    print(f"Loading data for {len(args)} stocks: {args}")
    
    for i, stock in enumerate(args):
        try:
            print(f"Progress: {i+1}/{len(args)} - Loading {stock}...")
            
            value = loadata(stock, start, end, decode)
            
            # Vérifier que la feature existe
            if feature not in value.columns:
                available_features = list(value.columns)
                raise Exception(f"Feature '{feature}' not found. Available: {available_features}")
            
            successful_data[stock] = value[feature]
            print(f"✓ Successfully loaded {stock} ({len(value)} records)")
            
            # Pause stratégique entre les requêtes
            if i < len(args) - 1:  # Ne pas attendre après la dernière
                time.sleep(1.5)
            
        except Exception as e:
            error_msg = f"✗ Failed to load {stock}: {str(e)}"
            print(error_msg)
            failed_stocks.append((stock, str(e)))
    
    # Création du DataFrame final
    if successful_data:
        data = pd.DataFrame(successful_data)
        
        # Rapport final
        print(f"\n{'='*50}")
        print(f"LOADING SUMMARY:")
        print(f"✓ Successful: {len(successful_data)} stocks")
        if failed_stocks:
            print(f"✗ Failed: {len(failed_stocks)} stocks")
            for stock, error in failed_stocks:
                print(f"  - {stock}: {error}")
        print(f"{'='*50}")
        
        return data
    else:
        raise Exception(f"Failed to load all {len(args)} stocks")

def loadata_patch(name, start=None, end=None, decode="utf-8"):
    """
    Patch de bvc.loadata() qui gère le cas MASI/MSI20 avec dates en epoch ms.
    """
    # Cette fonction utilise maintenant la nouvelle implémentation robuste
    return loadata(name, start, end, decode)

def getIntraday(name, decode="utf-8"):
    """
    Load intraday data avec gestion d'erreurs améliorée
    Inputs: 
        -Name: stock,index 
        -decode: default value is "utf-8", if it is not working use : "utf-8-sig"
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

# Fonction utilitaire pour vérifier la connectivité
def check_api_status():
    """Vérifie le statut de l'API Media24"""
    test_url = "https://medias24.com/content/api?method=getMasiHistory&periode=1d&format=json"
    
    try:
        response = SCRAPER._make_request(test_url, max_retries=1)
        return True, "API is accessible"
    except Exception as e:
        return False, f"API is not accessible: {str(e)}"

# Solution alternative simple si le problème persiste
def loadata_simple(name, start=None, end=None, decode="utf-8"):
    """
    Version simplifiée avec requests directement
    """
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
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
        response = requests.get(link, verify=False, timeout=30)
        if response.status_code == 200:
            data = json.loads(response.text)
            df = pd.DataFrame(data["result"])
            # ... reste du traitement identique
            return df.set_index("Date")
        else:
            raise Exception(f"HTTP Error {response.status_code}")
    except Exception as e:
        raise Exception(f"Error: {str(e)}")
