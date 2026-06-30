import streamlit as st
import pandas as pd
import requests
import random
import time
import json

from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# =====================================================
# CONFIG
# =====================================================

FORM_URL = (
    "https://docs.google.com/forms/u/0/d/e/"
    "1FAIpQLSdYY2hbRIhrCY_a06uH0keEsBBu8x6P3AzpZ2BmcmVERjaxpQ"
    "/formResponse"
)

PROGRESS_FILE = "progress.json"
# =====================================================
# PICKUP TIME CHAIN
# =====================================================

last_submit_time = None

# =====================================================
# PROGRESS
# =====================================================

def load_progress():

    try:

        if Path(PROGRESS_FILE).exists():

            with open(PROGRESS_FILE, "r") as f:

                data = json.load(f)

            return data.get("last_success", 0)

    except:
        pass

    return 0


def save_progress(row_number):

    with open(PROGRESS_FILE, "w") as f:

        json.dump(
            {"last_success": row_number},
            f
        )


def reset_progress():

    save_progress(0)

# =====================================================
# HELPER
# =====================================================

def clean(value):

    if pd.isna(value):
        return ""

    return str(value).strip()


def get_pickup_time():

    global last_submit_time

    now = datetime.now(
        ZoneInfo("Asia/Jakarta")
    )

    # Data pertama
    if last_submit_time is None:

        pickup = now - timedelta(
            seconds=random.randint(30, 60)
        )

    # Data berikutnya
    else:

        pickup = last_submit_time

    return pickup

# =====================================================
# BUILD PAYLOAD
# =====================================================

def build_payload(row):

    payload = {}

    # ---------------------------------
    # PICK UP TIME
    # ---------------------------------

    pickup = get_pickup_time()

    payload["entry.141665543_hour"] = (
        pickup.strftime("%H")
    )

    payload["entry.141665543_minute"] = (
        pickup.strftime("%M")
    )

    payload["entry.141665543_second"] = (
        pickup.strftime("%S")
    )

    # ---------------------------------
    # CREATE DATE & TIME DARI EXCEL
    # ---------------------------------

    create_dt = pd.to_datetime(
        f"{row['Create Ticket Date']} "
        f"{row['Create Ticket Time']}",
        dayfirst=True
    )

    payload["entry.2062984122_hour"] = (
        create_dt.strftime("%H")
    )

    payload["entry.2062984122_minute"] = (
        create_dt.strftime("%M")
    )

    payload["entry.2062984122_second"] = (
        create_dt.strftime("%S")
    )

    payload["entry.1418866853_day"] = (
        create_dt.strftime("%d")
    )

    payload["entry.1418866853_month"] = (
        create_dt.strftime("%m")
    )

    payload["entry.1418866853_year"] = (
        create_dt.strftime("%Y")
    )

    # ---------------------------------
    # FIELD FORM
    # ---------------------------------

    payload["entry.154565194"] = clean(
        row["Nama"]
    )

    payload["entry.1778899713"] = clean(
        row["SBU"]
    )

    payload["entry.1802806380"] = clean(
        row["ID TICKET"]
    )

    payload["entry.564067612"] = clean(
        row.get(
            "Keterangan Tambahan",
            ""
        )
    )

    payload["entry.822984039"] = clean(
        row["Eskalasi Back Office"]
    )

    payload["entry.49503729"] = clean(
        row["Hasil Eskalasi"]
    )

    # sentinel

    payload["entry.822984039_sentinel"] = ""
    payload["entry.49503729_sentinel"] = ""

    payload["fvv"] = "1"
    payload["pageHistory"] = "0"

    return payload

# =====================================================
# SUBMIT
# =====================================================

def submit_form(session, payload):

    last_error = ""

    for attempt in range(3):

        try:

            response = session.post(
                FORM_URL,
                data=payload,
                headers={
                    "User-Agent":
                    "Mozilla/5.0",

                    "Referer":
                    FORM_URL.replace(
                        "formResponse",
                        "viewform"
                    )
                },
                timeout=60
            )

            if response.status_code in [
                200,
                302
            ]:

                return True, ""

            last_error = (
                f"HTTP "
                f"{response.status_code}"
            )

        except Exception as e:

            last_error = str(e)

        time.sleep(3)

    return False, last_error

# =====================================================
# UI
# =====================================================

st.set_page_config(
    page_title="MONIT Importer",
    layout="wide"
)

st.markdown(
    """
    <h1 style="color:#FF0000;">
        MONITORING BACK OFFICE
    </h1>
    """,
    unsafe_allow_html=True
)
col1, col2 = st.columns(2)

with col1:

    if st.button(
        "Mulai Ulang"
    ):

        reset_progress()

        st.success(
            "Mendapatkan Nilai 100"
        )

with col2:

    st.info(
        f"Terkirim : "
        f"{load_progress()}"
    )

min_delay = st.number_input(
    "Detik Minimal",
    min_value=1,
    max_value=60,
    value=10
)

max_delay = st.number_input(
    "Detik Maksimal",
    min_value=1,
    max_value=120,
    value=30
)

file = st.file_uploader(
    "Unggah Excel",
    type=["xlsx"]
)

# =====================================================
# PROCESS
# =====================================================

if file:

    df = pd.read_excel(
        file,
        engine="openpyxl"
    )

    st.dataframe(df.head())

    required_cols = [

        "Nama",
        "ID TICKET",
        "SBU",
        "Eskalasi Back Office",
        "Create Ticket Date",
        "Create Ticket Time",
        "Hasil Eskalasi"

    ]

    missing = [

        c for c in required_cols

        if c not in df.columns
    ]

    if missing:

        st.error(
            f"Kolom tidak ditemukan: "
            f"{missing}"
        )

        st.stop()

    st.write(
        f"Total Data : {len(df)}"
    )

    if st.button(
        "Kirim"
    ):

        start_row = load_progress()

        session = requests.Session()

        progress_bar = st.progress(0)

        status_box = st.empty()
        progress_text = st.empty()

        success = 0
        failed = 0

        start_time = time.time()

        for idx in range(
            start_row,
            len(df)
        ):

            row = df.iloc[idx]

            payload = build_payload(
                row
            )

            ok, err = submit_form(
                session,
                payload
            )

            if ok:
                
                last_submit_time = datetime.now(
                    ZoneInfo("Asia/Jakarta")
                )
            
                save_progress(
                    idx + 1
                )
            
                success += 1

                status_box.success(
                    f"✓ {row['ID TICKET']}"
                )

            else:

                failed += 1

                status_box.error(
                    f"✗ {row['ID TICKET']} | {err}"
                )

            # ==========================
            # Progress + Estimasi Waktu
            # ==========================
            current = idx + 1
            total = len(df)

            percent = current / total

            progress_bar.progress(percent)

            elapsed = time.time() - start_time

            avg_time = elapsed / (current - start_row)

            remaining = total - current

            eta_seconds = avg_time * remaining

            eta_minutes = int(eta_seconds // 60)
            eta_secs = int(eta_seconds % 60)

            progress_text.markdown(
                f"""
            ### 📊 Progress

            **{percent*100:.1f}%**

            **Data : {current}/{total}**

            ✅ Berhasil : **{success}**

            ❌ Gagal : **{failed}**

            ⏳ Estimasi sisa waktu : **{eta_minutes} menit {eta_secs} detik**
            """
            )

            if idx < len(df) - 1:

                delay = random.randint(
                    min_delay,
                    max_delay
                )

                time.sleep(delay)

        st.success(
            f"""
Import selesai

Berhasil : {success}

Gagal : {failed}
"""
        )

st.markdown("""
<style>
.marquee {
    overflow: hidden;
    white-space: nowrap;
    background: #000000;   /* Hitam */
    color: white;
    padding: 10px;
    font-size:18px;
    font-weight:bold;
}

.marquee span{
    display:inline-block;
    padding-left:100%;
    animation: marquee 20s linear infinite;
}

@keyframes marquee{
    0%{
        transform:translateX(0);
    }
    100%{
        transform:translateX(-100%);
    }
}
</style>

<div class="marquee">
    <span>
    Barang siapa yang mempersulit urusan orang lain, maka Allah akan mempersulitnya di hari kiamat (HR. Muslim)
    </span>
</div>
""", unsafe_allow_html=True)
