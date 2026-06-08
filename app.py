
import streamlit as st
import pandas as pd
import requests

FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdJzVCp0QswGlQN_eWWT8zCbUq4tHcv4u9RfYEpjWE54vst1g/formResponse"

FIELD_MAP = {
    "Nama": "entry.756027671",
    "ID TICKET": "entry.1901165043",
    "SBU": "entry.143185955",
    "Eskalasi Back Office": "entry.1818729194",
    "Pick Up Time": "entry.1592591966",
    "Create Ticket Date": "entry.995121463",
    "Create Ticket Time": "entry.1672136407",
    "Hasil Eskalasi": "entry.49705214",
    "Keterangan Tambahan": "entry.679011578"
}

st.title("Excel ➜ Google Form Importer")

file = st.file_uploader("Upload Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    st.dataframe(df.head())
    st.write(f"Total data: {len(df)}")

    if st.button("Kirim ke Google Form"):
        progress = st.progress(0)
        sukses = 0

        for idx, (_, row) in enumerate(df.iterrows()):
            payload = {
                FIELD_MAP["Nama"]: row.get("Nama",""),
                FIELD_MAP["ID TICKET"]: row.get("ID TICKET",""),
                FIELD_MAP["SBU"]: row.get("SBU",""),
                FIELD_MAP["Eskalasi Back Office"]: row.get("Eskalasi Back Office",""),
                FIELD_MAP["Pick Up Time"]: str(row.get("Pick Up Time","")),
                FIELD_MAP["Create Ticket Date"]: str(row.get("Create Ticket Date","")),
                FIELD_MAP["Create Ticket Time"]: str(row.get("Create Ticket Time","")),
                FIELD_MAP["Hasil Eskalasi"]: row.get("Hasil Eskalasi",""),
                FIELD_MAP["Keterangan Tambahan"]: row.get("Keterangan Tambahan","")
            }

            try:
                requests.post(FORM_URL, data=payload, timeout=20)
                sukses += 1
            except:
                pass

            progress.progress((idx + 1) / len(df))

        st.success(f"Selesai. Berhasil memproses {sukses} data.")
