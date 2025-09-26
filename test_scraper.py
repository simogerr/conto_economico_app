import time
import pandas as pd
import streamlit as st
import io
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ---------------- UTILS ----------------
def make_driver(headless: bool, user_agent: str):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument(f"user-agent={user_agent}")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_window_size(1280, 1500)
    return driver


def scroll_lazy(driver, steps=6, pause=1.2):
    """Scrolla per caricare annunci lazy."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(steps):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# ---------------- SCRAPER SUBITO ----------------
def scrape_subito(url, headless=True, scroll_steps=8):
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    driver = make_driver(headless=headless, user_agent=ua)
    wait = WebDriverWait(driver, 20)

    driver.get(url)

    try:
        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class,'items__item')]")
        ))
    except Exception:
        pass

    scroll_lazy(driver, steps=scroll_steps, pause=1.5)

    # Trova tutti gli annunci
    cards = driver.find_elements(By.XPATH, "//div[contains(@class,'items__item')]")

    data = []
    for card in cards:
        try:
            titolo = card.find_element(By.XPATH, ".//h2[contains(@class,'item-title')]").text.strip()
        except Exception:
            titolo = ""

        try:
            prezzo = card.find_element(By.XPATH, ".//p[contains(@class,'price')]").text.strip()
        except Exception:
            prezzo = ""

        try:
            luogo_data = card.find_element(
                By.XPATH, ".//div[contains(@class,'PostingTimeAndPlace-module_date-location')]"
            ).text.strip()
        except Exception:
            luogo_data = ""

        try:
            info_extra = [x.text.strip() for x in card.find_elements(
                By.XPATH, ".//p[contains(@class,'index-module_info__GDGgZ')]"
            )]
            info_extra = " | ".join(info_extra)
        except Exception:
            info_extra = ""

        try:
            link = card.find_element(By.XPATH, ".//a[@href]").get_attribute("href")
        except Exception:
            link = ""

        if titolo or prezzo:
            data.append({
                "titolo": titolo,
                "prezzo": prezzo,
                "luogo/data": luogo_data,
                "info": info_extra,
                "link": link
            })

    driver.quit()
    return pd.DataFrame(data)


# ---------------- PARSING €/mq ----------------
def parse_price(prezzo_str):
    try:
        return int(re.sub(r"[^\d]", "", prezzo_str))
    except:
        return None

def parse_mq(info_str):
    match = re.search(r"(\d+)\s*mq", info_str.lower())
    if match:
        return int(match.group(1))
    return None


# ---------------- STREAMLIT DASHBOARD ----------------
st.set_page_config(page_title="Scraper Subito.it", page_icon="🏠", layout="wide")
st.title("🏠 Scraping annunci – Subito.it")

# Input URL
url = st.text_input("🔗 Incolla qui l’URL della ricerca Subito.it",
    "https://www.subito.it/annunci-lombardia/vendita/appartamenti/")

# Opzioni
headless = st.checkbox("Esegui headless (senza finestra browser)", value=True)
scroll_steps = st.slider("Scroll pass (più scroll = più annunci)", 1, 20, 8)

# Bottone
if st.button("🔄 Scarica dati"):
    with st.spinner("Raccolgo gli annunci..."):
        df = scrape_subito(url, headless=headless, scroll_steps=scroll_steps)

    if df.empty:
        st.error("Nessun dato trovato.")
    else:
        # Calcolo €/mq
        df["prezzo_num"] = df["prezzo"].apply(parse_price)
        df["mq"] = df["info"].apply(parse_mq)
        df["€/mq"] = df.apply(
            lambda row: round(row["prezzo_num"] / row["mq"], 0)
            if row["prezzo_num"] and row["mq"] else None,
            axis=1
        )

        st.success(f"Trovati {len(df)} annunci")
        st.dataframe(df)

        # ----- EXPORT SOLO EXCEL CON COLONNE ADATTATE -----
        from openpyxl.utils import get_column_letter

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Annunci")
            ws = writer.sheets["Annunci"]

            # Adatta la larghezza delle colonne
            for col_idx, col in enumerate(df.columns, 1):
                max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                ws.column_dimensions[get_column_letter(col_idx)].width = max_len

        excel_data = output.getvalue()
        st.download_button(
            "💾 Scarica Excel con €/mq",
            data=excel_data,
            file_name="annunci.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
