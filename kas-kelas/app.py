import streamlit as st
from datetime import date
from database import get_user_by_username, add_transaction, get_transactions, get_balance
from auth import login

st.set_page_config(page_title="Kas Kelas", page_icon="💰")

if 'user_id' not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

def init():
    from database import get_user_by_username, add_user
    from auth import hash_password
    if not get_user_by_username("admin"):
        add_user("admin", hash_password("admin123"))
        add_user("admin", hash_password("admin123"))

def show_login():
    st.title("💰 Kas Kelas - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login(username, password):
            user = get_user_by_username(username)
            st.session_state.user_id = user.id
            st.session_state.username = user.username
            st.rerun()
        else:
            st.error("Username atau password salah")

def show_dashboard():
    st.title(f"💰 Kas Kelas - {st.session_state.username}")
    
    saldo = get_balance(st.session_state.user_id)
    st.metric("Saldo Kas", f"Rp {saldo:,.0f}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("➕ Pemasukan")
        with st.form("form_masuk"):
            jumlah = st.number_input("Jumlah (Rp)", min_value=0.0, step=1000.0)
            deskripsi = st.text_input("Deskripsi")
            tanggal = st.date_input("Tanggal", date.today())
            if st.form_submit_button("Simpan"):
                add_transaction(st.session_state.user_id, "masuk", jumlah, deskripsi, tanggal)
                st.success("Pemasukan berhasil!")
                st.rerun()
    
    with col2:
        st.subheader("➖ Pengeluaran")
        with st.form("form_keluar"):
            jumlah_keluar = st.number_input("Jumlah (Rp)", min_value=0.0, step=1000.0)
            deskripsi_keluar = st.text_input("Deskripsi")
            tanggal_keluar = st.date_input("Tanggal", date.today())
            if st.form_submit_button("Simpan"):
                saldo = get_balance(st.session_state.user_id)
                if jumlah_keluar > saldo:
                    st.error("Saldo tidak cukup!")
                else:
                    add_transaction(st.session_state.user_id, "keluar", jumlah_keluar, deskripsi_keluar, tanggal_keluar)
                    st.success("Pengeluaran berhasil!")
                    st.rerun()

def show_history():
    st.title("📋 History Transaksi")
    trans = get_transactions(st.session_state.user_id)
    if trans:
        data = [{"Tanggal": t.tanggal, "Type": t.type, "Jumlah": t.jumlah, "Deskripsi": t.deskripsi} for t in trans]
        st.table(data)
    else:
        st.info("Belum ada transaksi")

def main():
    init()
    if not st.session_state.user_id:
        show_login()
    else:
        menu = st.sidebar.selectbox("Menu", ["Dashboard", "History", "Logout"])
        if menu == "Dashboard":
            show_dashboard()
        elif menu == "History":
            show_history()
        elif menu == "Logout":
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

if __name__ == "__main__":
    main()