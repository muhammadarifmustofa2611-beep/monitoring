import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# =====================================================
# GOOGLE FORM
# =====================================================

FORM_URL = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSdYY2hbRIhrCY_a06uH0keEsBBu8x6P3AzpZ2BmcmVERjaxpQ/formResponse"

# =====================================================
# FUNGSI
# =====================================================

def clean_value(val):

    if pd.isna(val):
        return ""

    return str(val).strip()


def parse_time_excel(value):

    """
    Support:
    13:09:09
    1900-01-19 13:09:09
    datetime
    """

    if pd.isna(value):
        return None

    try:

        if isinstance(value, datetime):
            return value.strftime("%H:%M:%S")

        value = str(value).strip()

        if " " in value:
            value = value.split(" ")[-1]

        datetime.strptime(value, "%H:%M:%S")

        return value

    except:
        return None


def build_payload(row):

    payload = {}

    # ==========================================
    # TEXT FIELD
    # ==========================================

    payload["entry.154565194"] = clean_value(
        row.get("Nama")
    )

    payload["entry.1778899713"] = clean_value(
        row.get("SBU")
    )

    payload["entry.1802806380"] = clean_value(
        row.get("ID TICKET")
    )

    payload["entry.822984039"] = clean_value(
        row.get("Eskalasi Back Office")
    )

    payload["entry.49503729"] = (
        clean_value(
            row.get("Hasil Eskalasi")
        )
        or "No respon"
    )

    payload["entry.564067612"] = (
        clean_value(
            row.get("Keterangan Tambahan")
        )
        or "-"
    )

    # ==========================================
    # PICK UP TIME
    # ==========================================

    pickup = parse_time_excel(
        row.get("Pick Up Time")
    )

    if pickup:

        h, m, s = pickup.split(":")

        payload["entry.141665543_hour"] = h
        payload["entry.141665543_minute"] = m
        payload["entry.141665543_second"] = s

    # ==========================================
    # CREATE TICKET DATE
    # ==========================================

    try:

        tanggal = pd.to_datetime(
            row.get("Create Ticket Date")
        )

        payload["entry.1418866853_day"] = str(
            tanggal.day
        )

        payload["entry.1418866853_month"] = str(
            tanggal.month
        )

        payload["entry.1418866853_year"] = str(
            tanggal.year
        )

    except:
        pass

    # ==========================================
    # CREATE TICKET TIME
    # ==========================================

    create_time = parse_time_excel(
        row.get("Create Ticket Time")
    )

    if create_time:

        h, m, s = create_time.split(":")

        payload["entry.2062984122_hour"] = h
        payload["entry.2062984122_minute"] = m
        payload["entry.2062984122_second"] = s

    return payload


# =====================================================
# UI
# =====================================================

st.title("Excel ➜ Google Form Importer")

delay = st.slider(
    "Jeda antar data (detik)",
    min_value=1,
    max_value=30,
    value=10,
    step=1
)

file = st.file_uploader(
    "Upload Excel",
    type=["xlsx"]
)

if file:

    df = pd.read_excel(file)

    # hapus baris kosong
    df = df.dropna(how="all")

    st.dataframe(df.head())

    st.write(
        f"Total data: {len(df)}"
    )

    estimasi = len(df) * delay

    menit = estimasi // 60
    detik = estimasi % 60

    st.info(
        f"Estimasi waktu proses: "
        f"{menit} menit {detik} detik"
    )

    if st.button("Kirim ke Google Form"):

        progress = st.progress(0)

        status_box = st.empty()
        countdown_box = st.empty()

        sukses = 0
        gagal = 0

        session = requests.Session()

        for nomor, (_, row) in enumerate(
            df.iterrows(),
            start=1
        ):

            try:

                payload = build_payload(row)

                if payload["entry.154565194"] == "":

                    gagal += 1

                    status_box.warning(
                        f"Baris {nomor} dilewati "
                        f"(Nama kosong)"
                    )

                    continue

                response = session.post(
                    FORM_URL,
                    data=payload,
                    headers={
                        "User-Agent":
                        "Mozilla/5.0"
                    },
                    timeout=30
                )

                if response.status_code == 200:

                    sukses += 1

                    status_box.success(
                        f"✓ Baris {nomor} berhasil "
                        f"({payload['entry.1802806380']})"
                    )

                else:

                    gagal += 1

                    status_box.error(
                        f"✗ Baris {nomor} gagal "
                        f"({response.status_code})"
                    )

                progress.progress(
                    nomor / len(df)
                )

                # =====================
                # DELAY
                # =====================

                if nomor < len(df):

                    for sisa in range(
                        delay,
                        0,
                        -1
                    ):

                        countdown_box.info(
                            f"Menunggu "
                            f"{sisa} detik "
                            f"sebelum kirim "
                            f"data berikutnya..."
                        )

                        time.sleep(1)

                    countdown_box.empty()

            except Exception as e:

                gagal += 1

                status_box.error(
                    f"Baris {nomor} error: {e}"
                )

        st.success(
            f"""
Selesai

Berhasil : {sukses}

Gagal : {gagal}

Total : {len(df)}
"""
        )
