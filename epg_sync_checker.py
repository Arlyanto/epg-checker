# -*- coding: utf-8 -*-
"""
EPG vs CMS Schedule Sync Checker
Deskripsi: Script untuk mencocokkan data jadwal dari Google Sheets (EPG) dengan CMS streaming platform secara otomatis.
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime

# ==================== CONFIGURATION ====================
# 1. Google Sheets Export URL (Pastikan link di-set ke "Anyone with the link can view")
# Ganti [SPREADSHEET_ID] dan [GID] sesuai dengan URL Google Sheets Anda
SHEET_ID = "YOUR_SPREADSHEET_ID"
GID = "0"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# 2. CMS URL
CMS_URL = "https://cms.example.com/admin/livestreamings/0000/schedules?selected_date=" # Tanggal akan ditambahkan otomatis
# =======================================================

def fetch_google_sheets_data():
    print("[-] Mengambil data dari Google Sheets EPG...")
    try:
        # Membaca CSV langsung dari Google Sheets
        df = pd.read_csv(GOOGLE_SHEET_URL)
        
        # Mapping nama kolom sesuai gambar
        # attribute[title], attribute[description], attribute[start_time], attribute[end_time]
        df_cleaned = df[['attribute[title]', 'attribute[start_time]', 'attribute[end_time]']].copy()
        df_cleaned.columns = ['title', 'start_time', 'end_time']
        
        # Bersihkan whitespace
        df_cleaned['title'] = df_cleaned['title'].str.strip()
        df_cleaned['start_time'] = df_cleaned['start_time'].str.strip()
        df_cleaned['end_time'] = df_cleaned['end_time'].str.strip()
        
        return df_cleaned
    except Exception as e:
        print(f"[X] Gagal mengambil data Google Sheets: {e}")
        return None

def fetch_cms_data(target_date, session_cookie):
    print(f"[-] Mengambil data dari CMS untuk tanggal {target_date}...")
    url = f"{CMS_URL}{target_date}"
    
    # Karena CMS membutuhkan login, kita perlu mengirimkan cookie session
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Cookie": session_cookie # Diambil dari browser setelah login
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[X] Gagal akses CMS. Status code: {response.status_code}")
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mencari tabel "Livestreaming Schedules"
        table = soup.find('table') # Sesuai dengan struktur HTML CMS Anda
        
        if not table:
            print("[X] Tabel jadwal tidak ditemukan di halaman CMS.")
            return None
            
        records = []
        rows = table.find_all('tr')[1:] # Skip header
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 5:
                # Kolom di CMS: STATUS, TITLE, DESCRIPTION, START TIME, END TIME
                title = cols[1].text.strip()
                start_time = cols[3].text.strip()
                end_time = cols[4].text.strip()
                
                records.append({
                    'title': title,
                    'start_time': start_time,
                    'end_time': end_time
                })
                
        return pd.DataFrame(records)
    except Exception as e:
        print(f"[X] Gagal mengambil data CMS: {e}")
        return None

def check_sync(df_epg, df_cms):
    print("[-] Memulai proses pengecekan keselarasan (Sync Check)...\n")
    
    # Buat Unique Key untuk komparasi: "JUDUL | START | END"
    df_epg['unique_key'] = df_epg['title'] + " | " + df_epg['start_time'] + " | " + df_epg['end_time']
    df_cms['unique_key'] = df_cms['title'] + " | " + df_cms['start_time'] + " | " + df_cms['end_time']
    
    epg_keys = set(df_epg['unique_key'])
    cms_keys = set(df_cms['unique_key'])
    
    # 1. Cek apa yang ada di EPG tapi TIDAK ADA di CMS
    missing_in_cms = df_epg[~df_epg['unique_key'].isin(cms_keys)]
    
    # 2. Cek apa yang ada di CMS tapi TIDAK ADA di EPG (Jadwal liar/tambahan)
    extra_in_cms = df_cms[~df_cms['unique_key'].isin(epg_keys)]
    
    print("=================== HASIL ANALISIS ===================")
    if missing_in_cms.empty and extra_in_cms.empty:
        print("[✓] SEMPURNA! Data EPG dan CMS 100% Selaras (Synced).")
    else:
        if not missing_in_cms.empty:
            print(f"[X] DITEMUKAN {len(missing_in_cms)} JADWAL EPG YANG BELUM MASUK/BERBEDA DI CMS:")
            for idx, row in missing_in_cms.iterrows():
                print(f"    - {row['title']} ({row['start_time']} - {row['end_time']})")
                
        if not extra_in_cms.empty:
            print(f"\n[!] DITEMUKAN {len(extra_in_cms)} JADWAL DI CMS YANG TIDAK ADA DI EPG:")
            for idx, row in extra_in_cms.iterrows():
                print(f"    - {row['title']} ({row['start_time']} - {row['end_time']})")
    print("======================================================")

if __name__ == "__main__":
    # Masukkan tanggal yang ingin dicek hari ini (format YYYY-MM-DD sesuai CMS)
    target_date = datetime.date.today().strftime("%Y-%m-%d")
    
    # Masukkan cookie session Anda dari browser (bisa dicari di Inspect Element -> Network / Application -> Cookies)
    # Ini wajib karena CMS membutuhkan autentikasi login
    SESSION_COOKIE = "YOUR_SESSION_COOKIE_HERE"
    
    df_epg = fetch_google_sheets_data()
    df_cms = fetch_cms_data(target_date, SESSION_COOKIE)
    
    if df_epg is not None and df_cms is not None:
        check_sync(df_epg, df_cms)
