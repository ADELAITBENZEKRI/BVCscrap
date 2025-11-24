from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from .utils import *

def getCours(name):
    """
    Load session data with Playwright
    """
    code = get_valeur(name)
    data = {"__EVENTTARGET": "SocieteCotee1$LBIndicCle"}
    
    link = f"https://www.casablanca-bourse.com/bourseweb/Societe-Cote.aspx?codeValeur={code}&cat=7"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Faire la requête POST avec les données
            page.goto(link)
            page.wait_for_timeout(2000)
            
            # Simuler le clic sur le bouton/liens qui déclenche l'événement
            page.evaluate("""() => {
                __doPostBack('SocieteCotee1$LBIndicCle', '');
            }""")
            
            page.wait_for_timeout(3000)
            
            content = page.content()
            browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            result = getTables(soup)
            return result
            
    except Exception as e:
        raise ValueError(f"Error fetching cours data for {name}: {str(e)}")

def getKeyIndicators(name, decode='utf-8'):
    """
    Load key indicators with Playwright
    """
    code = get_valeur(name)
    data = {"__EVENTTARGET": "SocieteCotee1$LBFicheTech"}
    
    link = f"https://www.casablanca-bourse.com/bourseweb/Societe-Cote.aspx?codeValeur={code}&cat=7"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(link)
            page.wait_for_timeout(2000)
            
            page.evaluate("""() => {
                __doPostBack('SocieteCotee1$LBFicheTech', '');
            }""")
            
            page.wait_for_timeout(3000)
            
            content = page.content()
            browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            result = getTablesFich(soup)
            return result
            
    except Exception as e:
        raise ValueError(f"Error fetching key indicators for {name}: {str(e)}")

def getDividend(name, decode='utf-8'):
    """
    Load dividends with Playwright
    """
    code = get_valeur(name)
    data = {"__EVENTTARGET": "SocieteCotee1$LBDividende"}
    
    link = f"https://www.casablanca-bourse.com/bourseweb/Societe-Cote.aspx?codeValeur={code}&cat=7"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(link)
            page.wait_for_timeout(2000)
            
            page.evaluate("""() => {
                __doPostBack('SocieteCotee1$LBDividende', '');
            }""")
            
            page.wait_for_timeout(3000)
            
            content = page.content()
            browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            result = getDivi(soup)
            return result
            
    except Exception as e:
        raise ValueError(f"Error fetching dividends for {name}: {str(e)}")

def getIndex():
    """
    Load indexes summary with Playwright
    """
    link = "https://www.casablanca-bourse.com/bourseweb/Activite-marche.aspx?Cat=22&IdLink=297"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(link, timeout=60000)
            page.wait_for_timeout(3000)
            
            content = page.content()
            browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            result = getAllIndex(soup)
            return result
            
    except Exception as e:
        raise ValueError(f"Error fetching index data: {str(e)}")

def getPond():
    """
    Load weights with Playwright
    """
    link = "https://www.casablanca-bourse.com/bourseweb/indice-ponderation.aspx?Cat=22&IdLink=298"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(link, timeout=60000)
            page.wait_for_timeout(3000)
            
            content = page.content()
            browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            return getPondval(soup)
            
    except Exception as e:
        raise ValueError(f"Error fetching ponderation data: {str(e)}")

def getIndexRecap():
    """
    Load session recap with Playwright
    """
    data = {"TopControl1$ScriptManager1": "FrontTabContainer1$ctl00$UpdatePanel1|FrontTabContainer1$ctl00$ImageButton1"}
    link = "https://www.casablanca-bourse.com/bourseweb/index.aspx"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Pour les requêtes POST complexes, on peut utiliser l'API route
            page.goto(link)
            page.wait_for_timeout(3000)
            
            # Simuler la soumission du formulaire
            page.evaluate("""() => {
                // Simuler l'action du ScriptManager
                __doPostBack('FrontTabContainer1$ctl00$ImageButton1', '');
            }""")
            
            page.wait_for_timeout(3000)
            
            content = page.content()
            browser.close()
            
            soup = BeautifulSoup(content, 'html.parser')
            return getIndiceRecapScrap(soup)
            
    except Exception as e:
        raise ValueError(f"Error fetching index recap: {str(e)}")
