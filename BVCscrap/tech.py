from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from .utils import *


def getCours(name):
    """
    Load session data, latest transaction, best limit and last 5 sessions.
    """
    code = get_valeur(name)
    data = {"__EVENTTARGET": "SocieteCotee1$LBIndicCle"}
    link = f"https://www.casablanca-bourse.com/bourseweb/Societe-Cote.aspx?codeValeur={code}&cat=7"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=90000)

            # Simulation d'un POST via JS
            page.evaluate(f"""
                () => {{
                    let form = document.querySelector('form');
                    let input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = '__EVENTTARGET';
                    input.value = '{data["__EVENTTARGET"]}';
                    form.appendChild(input);
                    form.submit();
                }}
            """)
            page.wait_for_timeout(5000)  # attendre le chargement

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')
        return getTables(soup)
    except Exception as e:
        print(f"Erreur getCours: {e}")
        return None


def getKeyIndicators(name, decode='utf-8'):
    """
    Load key indicators of a company.
    """
    code = get_valeur(name)
    data = {"__EVENTTARGET": "SocieteCotee1$LBFicheTech"}
    link = f"https://www.casablanca-bourse.com/bourseweb/Societe-Cote.aspx?codeValeur={code}&cat=7"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=90000)

            page.evaluate(f"""
                () => {{
                    let form = document.querySelector('form');
                    let input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = '__EVENTTARGET';
                    input.value = '{data["__EVENTTARGET"]}';
                    form.appendChild(input);
                    form.submit();
                }}
            """)
            page.wait_for_timeout(5000)

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')
        return getTablesFich(soup)
    except Exception as e:
        print(f"Erreur getKeyIndicators: {e}")
        return None


def getDividend(name, decode='utf-8'):
    """
    Load dividends of a company.
    """
    code = get_valeur(name)
    data = {"__EVENTTARGET": "SocieteCotee1$LBDividende"}
    link = f"https://www.casablanca-bourse.com/bourseweb/Societe-Cote.aspx?codeValeur={code}&cat=7"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=90000)

            page.evaluate(f"""
                () => {{
                    let form = document.querySelector('form');
                    let input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = '__EVENTTARGET';
                    input.value = '{data["__EVENTTARGET"]}';
                    form.appendChild(input);
                    form.submit();
                }}
            """)
            page.wait_for_timeout(5000)

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')
        return getDivi(soup)
    except Exception as e:
        print(f"Erreur getDividend: {e}")
        return None


def getIndex():
    """
    Load indexes summary.
    """
    link = "https://www.casablanca-bourse.com/bourseweb/Activite-marche.aspx?Cat=22&IdLink=297"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=90000)
            page.wait_for_timeout(5000)

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')
        return getAllIndex(soup)
    except Exception as e:
        print(f"Erreur getIndex: {e}")
        return None


def getPond():
    """
    Load weights (Pondération).
    """
    link = "https://www.casablanca-bourse.com/bourseweb/indice-ponderation.aspx?Cat=22&IdLink=298"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=90000)
            page.wait_for_timeout(5000)

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')
        return getPondval(soup)
    except Exception as e:
        print(f"Erreur getPond: {e}")
        return None


def getIndexRecap():
    """
    Load session recap.
    """
    data = {"TopControl1$ScriptManager1": "FrontTabContainer1$ctl00$UpdatePanel1|FrontTabContainer1$ctl00$ImageButton1"}
    link = "https://www.casablanca-bourse.com/bourseweb/index.aspx"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(link, timeout=90000)

            page.evaluate(f"""
                () => {{
                    let form = document.querySelector('form');
                    let input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = 'TopControl1$ScriptManager1';
                    input.value = '{data["TopControl1$ScriptManager1"]}';
                    form.appendChild(input);
                    form.submit();
                }}
            """)
            page.wait_for_timeout(5000)

            html = page.content()
            browser.close()

        soup = BeautifulSoup(html, 'html.parser')
        return getIndiceRecapScrap(soup)
    except Exception as e:
        print(f"Erreur getIndexRecap: {e}")
        return None
