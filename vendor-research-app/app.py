import streamlit as st
import requests
import json
import time
import os
from datetime import datetime
from urllib.parse import quote
from deep_translator import GoogleTranslator

st.set_page_config(
    page_title="Vendor Research - Purchasing Tool", page_icon="🔍", layout="wide"
)

st.title("🔍 Vendor Research System")
st.caption(
    "Otomatisasi riset vendor - pencarian dokumentasi, perbandingan spesifikasi, dan verifikasi fakta"
)

st.sidebar.header("Menu")
menu = st.sidebar.radio(
    "Pilih Menu",
    ["Riset Vendor", "Perbandingan Produk", "Verifikasi Fakta", "Riwayat Riset"],
)

CATEGORIES = {
    "Laptop/Komputer": ["Dell", "HP", "Lenovo", "Asus", "Acer", "Apple", "Microsoft"],
    "Server": ["Dell EMC", "HP Enterprise", "Lenovo ThinkSystem", "Cisco", "Huawei"],
    "Networking": ["Cisco", "Juniper", "Aruba", "TP-Link", "MikroTik"],
    "Software": ["Microsoft", "Adobe", "Autodesk", "Oracle", "SAP"],
    "Cloud": ["AWS", "Azure", "Google Cloud", "Alibaba Cloud"],
    " Lainnya": ["custom"],
}

if "history" not in st.session_state:
    st.session_state.history = []

_translator = None


def get_translator():
    global _translator
    if _translator is None:
        _translator = GoogleTranslator(source="auto", target="id")
    return _translator


def translate_text(text):
    try:
        if not text or len(text.strip()) < 3:
            return text
        translator = get_translator()
        result = translator.translate(text[:500])
        return result if result else text
    except:
        return text


def search_web(query, num_results=5):
    # Google Custom Search API
    GOOGLE_API_KEY = "AIzaSyCeUOYRKg4S-sHuWumFAC4yTCcCH31hCQg"
    GOOGLE_CX = "c5b310058b63c4868"

    try:
        # Try Google API first
        google_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&q={quote(query)}&num={num_results}&hl=id"
        r = requests.get(google_url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            results = []
            for item in data.get("items", [])[:num_results]:
                results.append(
                    {
                        "title": item.get("title", "")[:100],
                        "url": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                    }
                )
            if results:
                return results
    except:
        pass

    try:
        response = requests.post(
            "http://localhost:4197/websearch",
            json={"query": query, "numResults": num_results},
            timeout=30,
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
    }

    # Try Google Shopping first for Indonesian results
    try:
        shop_url = f"https://www.google.com/search?q={quote(query)}&tbm=shop&hl=id"
        r = requests.get(
            shop_url, headers=headers, timeout=15, proxies={"http": None, "https": None}
        )
        if r.status_code == 200:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            for div in soup.select("div.sh-np7sh")[:num_results]:
                title = div.select_one("div.e4HiGM")
                price = div.select_one("div.kvSW7Y")
                link = div.select_one("a")
                if title:
                    results.append(
                        {
                            "title": title.get_text()[:100],
                            "url": link.get("href", "") if link else "",
                            "snippet": "Harga: " + price.get_text() if price else "",
                        }
                    )
            if results:
                return results
    except:
        pass

    # Try Bing
    try:
        search_url = f"https://www.bing.com/search?q={quote(query)}&count={num_results}&setlang=id"
        r = requests.get(
            search_url,
            timeout=15,
            headers=headers,
            proxies={"http": None, "https": None},
        )
        if r.status_code == 200:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(r.text, "html.parser")
            results = []
            for item in soup.select("li.b_algo")[:num_results]:
                title_elem = item.select_one("h2 a")
                if title_elem:
                    results.append(
                        {
                            "title": title_elem.get_text()[:100],
                            "url": title_elem.get("href", ""),
                            "snippet": item.select_one("p").get_text()
                            if item.select_one("p")
                            else "",
                        }
                    )
            return results
    except:
        pass

    return []


def search_cited(query):
    results = search_web(query, 5)
    if results:
        return {"sources": [r["url"] for r in results]}
    return None


def format_search_results(results):
    if not results:
        return "Tidak ada hasil"

    formatted = []
    for r in results:
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("Highlights", r.get("snippet", ""))[:300]
        formatted.append(f"**{title}**\n{snippet}\n[Link]({url})")

    return "\n\n".join(formatted)


if menu == "Riset Vendor":
    st.header("Riset Vendor Baru")

    with st.form("research_form"):
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Kategori Produk", list(CATEGORIES.keys()))
            custom_category = st.text_input("Atau masukkan kategori custom")
        with col2:
            vendors = st.text_input(
                "Nama Vendor (pisahkan dengan koma)", placeholder="Dell, HP, Lenovo"
            )

        products = st.text_area(
            "Nama Produk (opsional)", placeholder="Laptop: Dell Latitude vs HP ProBook"
        )

        submit = st.form_submit_button("🔍 Mulai Riset", use_container_width=True)

    if submit:
        if vendors:
            vendor_list = [v.strip() for v in vendors.split(",")]
            research_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "category": custom_category if custom_category else category,
                "vendors": vendor_list,
                "products": products,
                "results": [],
            }

            progress_bar = st.progress(0)

            for i, vendor in enumerate(vendor_list):
                progress_bar.progress((i + 1) / len(vendor_list))
                st.subheader(f"🔎 Riset: {vendor}")

                queries = [
                    f"{vendor} {products if products else category} Indonesia harga murah",
                    f"{vendor} {products if products else category} terlengkap Indonesia",
                    f"{vendor} {products if products else category} specs review",
                ]

                vendor_results = {"vendor": vendor, "searches": []}

                for q in queries:
                    with st.spinner(f"Mencari: {q[:50]}..."):
                        result = search_web(q)
                        vendor_results["searches"].append(
                            {"query": q, "results": result if result else []}
                        )
                        time.sleep(0.5)

                research_data["results"].append(vendor_results)

                st.success(f"Riset {vendor} selesai")

            progress_bar.empty()

            st.session_state.history.append(research_data)

            st.divider()
            st.subheader("📊 Hasil Riset")

            for vr in research_data["results"]:
                vendor_name = vr["vendor"]
                with st.expander(f"📁 {vendor_name}", expanded=True):
                    for search in vr["searches"]:
                        query_text = search["query"]
                        st.markdown(f"**Query:** {query_text}")
                        st.markdown(format_search_results(search["results"]))
                        st.divider()

elif menu == "Perbandingan Produk":
    st.header("Perbandingan Spesifikasi Produk")

    col1, col2 = st.columns(2)
    with col1:
        product_a = st.text_input("Produk A", placeholder="Dell Latitude 3540")
    with col2:
        product_b = st.text_input("Produk B", placeholder="HP ProBook 440 G10")

    compare_btn = st.button("🔄 Bandingkan", use_container_width=True)

    if compare_btn and product_a and product_b:
        with st.spinner("Mencari spesifikasi..."):
            result = search_web(
                f"{product_a} vs {product_b} comparison specs 2025", num_results=8
            )

        if result:
            st.subheader("📊 Hasil Perbandingan")
            st.markdown(format_search_results(result))
        else:
            st.warning("Tidak ada hasil ditemukan")

elif menu == "Verifikasi Fakta":
    st.header("Verifikasi Klaim Vendor")

    claim = st.text_area(
        "Masukkan klaim yang ingin diverifikasi",
        placeholder="Contoh: Vendor X menawarkan garansi 5 tahun",
    )

    verify_btn = st.button("✓ Verifikasi Klaim", use_container_width=True)

    if verify_btn and claim:
        with st.spinner("Memverifikasi klaim..."):
            result = search_cited(claim)

        if result:
            st.subheader("Hasil Verifikasi")
            if "sources" in result:
                for src in result["sources"]:
                    st.markdown(f"- [{src}]({src})")
            else:
                st.markdown(result.get("content", str(result)))
        else:
            st.error("Verifikasi gagal")

elif menu == "Riwayat Riset":
    st.header("Riwayat Riset")

    if st.session_state.history:
        for idx, item in enumerate(reversed(st.session_state.history)):
            ts = item["timestamp"]
            cat = item["category"]
            v_key = "vendors"
            p_key = "products"
            r_key = "results"
            c_key = "category"
            with st.expander(f"📅 {ts} - {cat}"):
                vendors_str = ", ".join(item[v_key])
                st.write(f"**Vendor:** {vendors_str}")
                st.write(f"**Kategori:** {item[c_key]}")
                if item[p_key]:
                    st.write(f"**Produk:** {item[p_key]}")
                st.write(f"**Jumlah pencarian:** {len(item[r_key])}")

                if st.button("Hapus", key=f"del_{idx}"):
                    st.session_state.history.remove(item)
                    st.rerun()
    else:
        st.info("Belum ada riwayat riset")

st.divider()
st.caption(
    "💡 Tips: Untuk hasil optimal, gunakan nama produk spesifik dan tambahkan tahun (2025/2026)"
)
