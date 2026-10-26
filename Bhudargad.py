"""युवा आवाज – राधानगरी आणि भुदरगड

सर्वेक्षण:  https://<app>.streamlit.app
डॅशबोर्ड:  https://<app>.streamlit.app/?page=admin   (ADMIN_PIN लागतो)

माहिती Google Sheet मध्ये जतन होते (secrets मध्ये service account).
secrets नसल्यास, चाचणीसाठी स्थानिक responses.csv वापरली जाते.
"""

import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

TITLE = "युवा आवाज – राधानगरी आणि भुदरगड"
IST = ZoneInfo("Asia/Kolkata")
LOCAL_CSV = Path(__file__).with_name("responses.csv")

HEADERS = [
    "timestamp", "response_id", "taluka", "village", "age_group", "gender",
    "education", "employment", "problems", "main_problem", "help_needed", "suggestion",
]

TALUKA = ["राधानगरी", "भुदरगड"]
AGE = ["15–18", "19–22", "23–26", "27–30", "31–35"]
GENDER = ["पुरुष", "स्त्री", "इतर", "सांगू इच्छित नाही"]
EDUCATION = ["10वी पेक्षा कमी", "10वी", "12वी", "ITI / डिप्लोमा", "पदवी", "पदव्युत्तर", "इतर"]
EMPLOYMENT = [
    "शिक्षण घेत आहे", "खाजगी नोकरी", "सरकारी नोकरी", "स्वतःचा व्यवसाय", "शेती",
    "रोजंदारी / मजुरी", "बेरोजगार – नोकरी शोधत आहे", "बेरोजगार – सध्या शोधत नाही",
]
PROBLEMS = [
    "शिक्षण", "बेरोजगारी", "व्यवसाय", "आर्थिक अडचणी", "मानसिक ताण",
    "व्यसन", "नातेसंबंध", "इंटरनेट", "वाहतूक", "गावातील सुविधा",
]
HELP = [
    "करिअर मार्गदर्शन", "कौशल्य प्रशिक्षण", "नोकरीच्या संधी", "व्यवसायासाठी कर्ज / भांडवल",
    "सरकारी योजनांची माहिती", "समुपदेशन / मानसिक आधार", "व्यसनमुक्ती मदत",
    "स्पर्धा परीक्षा मार्गदर्शन", "इंटरनेट / डिजिटल सुविधा", "वाहतूक सुविधा",
]

st.set_page_config(page_title=TITLE, page_icon="🗣️", layout="centered")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700&family=Mukta:wght@400;500;700&display=swap');
    html, body, [class*="st-"], .stMarkdown, button, input, textarea { font-family: "Mukta", "Noto Sans Devanagari", sans-serif; }
    h1, h2, h3 { font-family: "Baloo 2", "Mukta", sans-serif !important; }
    .block-container { padding-top: 3.5rem; max-width: 680px; }
    .eyebrow { color: #d9901a; font-weight: 700; font-size: .85rem; letter-spacing: .06em; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------- साठवण (Google Sheet किंवा स्थानिक CSV) ----------------

def using_sheet() -> bool:
    try:
        return "gcp_service_account" in st.secrets and "sheet_url" in st.secrets
    except Exception:
        return False


@st.cache_resource
def get_worksheet():
    import gspread

    gc = gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    sh = gc.open_by_url(st.secrets["sheet_url"])
    try:
        ws = sh.worksheet("Responses")
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet("Responses", rows=1000, cols=len(HEADERS))
    if ws.row_values(1) != HEADERS:
        ws.update([HEADERS], "A1")
        ws.freeze(rows=1)
    return ws


def clean(text: str, limit: int) -> str:
    s = " ".join(str(text or "").split())[:limit]
    # Sheet मध्ये सूत्र म्हणून चालू नये
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


def save_row(row: list) -> None:
    if using_sheet():
        get_worksheet().append_row(row, value_input_option="RAW")
    else:
        df = pd.DataFrame([row], columns=HEADERS)
        df.to_csv(LOCAL_CSV, mode="a", header=not LOCAL_CSV.exists(), index=False)
    load_responses.clear()


@st.cache_data(ttl=60)
def load_responses() -> pd.DataFrame:
    if using_sheet():
        rows = get_worksheet().get_all_values()
        df = pd.DataFrame(rows[1:], columns=HEADERS) if len(rows) > 1 else pd.DataFrame(columns=HEADERS)
    elif LOCAL_CSV.exists():
        df = pd.read_csv(LOCAL_CSV, dtype=str).fillna("")
    else:
        df = pd.DataFrame(columns=HEADERS)
    return df


# ---------------- सर्वेक्षण ----------------

def survey_page() -> None:
    st.markdown('<div class="eyebrow">राधानगरी · भुदरगड</div>', unsafe_allow_html=True)
    st.title("युवा आवाज")
    st.write("तुमच्या गावातील तरुणांना कोणत्या अडचणी येतात, ते आम्हाला सांगा. तुमची उत्तरे उपाय शोधण्यासाठी वापरली जातील.")

    if st.session_state.get("submitted"):
        st.success("**धन्यवाद!** तुमची उत्तरे जतन झाली आहेत. तुमच्या मित्रांनाही ही लिंक पाठवा.")
        if st.session_state.pop("celebrate", False):
            st.balloons()
        if st.button("दुसरा प्रतिसाद भरा"):
            st.session_state.submitted = False
            st.rerun()
        return

    st.info("नाव किंवा मोबाईल नंबर विचारला जात नाही. उत्तर द्यायला साधारण ३ मिनिटे लागतील.")

    with st.form("survey"):
        taluka = st.pills("१. तुमचा तालुका *", TALUKA, selection_mode="single")
        village = st.text_input("२. तुमचे गाव *", max_chars=80, placeholder="गावाचे नाव")
        age = st.pills("३. वयोगट *", AGE, selection_mode="single")
        gender = st.pills("४. लिंग", GENDER, selection_mode="single")
        education = st.pills("५. शिक्षण", EDUCATION, selection_mode="single")
        employment = st.pills("६. सध्या तुम्ही काय करता?", EMPLOYMENT, selection_mode="single")
        problems = st.pills("७. तुम्हाला कोणत्या अडचणी येतात? * (एकापेक्षा जास्त निवडू शकता)", PROBLEMS, selection_mode="multi")
        main_problem = st.text_area("८. तुमची सर्वात मोठी अडचण थोडक्यात सांगा", max_chars=1000)
        help_needed = st.pills("९. तुम्हाला कोणत्या मदतीची गरज आहे? (एकापेक्षा जास्त निवडू शकता)", HELP, selection_mode="multi")
        suggestion = st.text_area("१०. गावासाठी किंवा तरुणांसाठी तुमची सूचना", max_chars=1000, placeholder="ऐच्छिक")
        sent = st.form_submit_button("उत्तरे पाठवा", type="primary", width="stretch")

    if not sent:
        return

    missing = [name for name, v in [("तालुका", taluka), ("गाव", village.strip()), ("वयोगट", age), ("किमान एक अडचण", problems)] if not v]
    if missing:
        st.error("कृपया भरा: " + ", ".join(missing))
        return

    row = [
        datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
        uuid.uuid4().hex[:8],
        taluka,
        clean(village, 80),
        age,
        gender or "",
        education or "",
        employment or "",
        "; ".join(problems),
        clean(main_problem, 1000),
        "; ".join(help_needed or []),
        clean(suggestion, 1000),
    ]
    try:
        save_row(row)
    except Exception:
        st.error("उत्तरे पाठवता आली नाहीत. इंटरनेट तपासून पुन्हा प्रयत्न करा.")
        return
    st.session_state.submitted = True
    st.session_state.celebrate = True
    st.rerun()


# ---------------- डॅशबोर्ड (फक्त PIN सह) ----------------

def count_multi(series: pd.Series, options: list) -> pd.Series:
    items = series.fillna("").str.split("; ").explode()
    return items[items != ""].value_counts().reindex(options, fill_value=0)


def admin_page() -> None:
    st.markdown('<div class="eyebrow">राधानगरी · भुदरगड</div>', unsafe_allow_html=True)
    st.title("युवा आवाज डॅशबोर्ड")

    pin_expected = str(st.secrets.get("admin_pin", "")) if _has_secrets() else ""
    if not st.session_state.get("admin_ok"):
        if not pin_expected:
            st.error("`admin_pin` secrets मध्ये सेट केलेला नाही. सेटअप मार्गदर्शक पाहा.")
            return
        with st.form("pin"):
            pin = st.text_input("PIN", type="password")
            ok = st.form_submit_button("उघडा", type="primary")
        if ok:
            if pin.strip() == pin_expected:
                st.session_state.admin_ok = True
                st.rerun()
            st.error("PIN चुकीचा आहे.")
        return

    if not using_sheet():
        st.warning("Google Sheet जोडलेली नाही; चाचणीसाठी स्थानिक फाईल वापरली जात आहे.")

    top = st.columns([3, 1])
    if top[1].button("🔄 पुन्हा लोड"):
        load_responses.clear()
        st.rerun()

    df = load_responses()
    total = len(df)
    by_taluka = df["taluka"].value_counts().reindex(TALUKA, fill_value=0)

    c = st.columns(3)
    c[0].metric("एकूण प्रतिसाद", total)
    c[1].metric("राधानगरी", int(by_taluka["राधानगरी"]))
    c[2].metric("भुदरगड", int(by_taluka["भुदरगड"]))

    if total == 0:
        st.info("अजून एकही प्रतिसाद नाही. सर्वेक्षणाची लिंक युवकांना पाठवा.")
        return

    st.subheader("तालुकानिहाय समस्या")
    st.caption("त्या तालुक्यातील किती टक्के युवकांनी ही समस्या नोंदवली.")
    pct = {}
    for t in TALUKA:
        sub = df[df["taluka"] == t]
        counts = count_multi(sub["problems"], PROBLEMS)
        pct[t] = (counts / len(sub) * 100).round(0) if len(sub) else counts * 0
    prob_df = pd.DataFrame(pct)
    prob_df = prob_df.loc[prob_df.sum(axis=1).sort_values(ascending=False).index]
    st.bar_chart(prob_df, horizontal=True, stack=False, color=["#1f5c4a", "#d9901a"], height=480)

    st.subheader("युवकांना हवी असलेली मदत")
    st.bar_chart(count_multi(df["help_needed"], HELP).sort_values(), horizontal=True, color="#1f5c4a")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("रोजगाराची स्थिती")
        st.dataframe(df["employment"].replace("", "नोंद नाही").value_counts().rename("संख्या"), width="stretch")
    with col2:
        st.subheader("वयोगट")
        st.dataframe(df["age_group"].value_counts().reindex(AGE, fill_value=0).rename("संख्या"), width="stretch")

    st.subheader("सर्वाधिक प्रतिसाद आलेली गावे")
    villages = (df["taluka"] + " · " + df["village"]).value_counts().head(10).rename("संख्या")
    st.dataframe(villages, width="stretch")

    st.subheader("अलीकडील नोंदी")
    recent = df[df["main_problem"].str.strip() != ""].tail(8).iloc[::-1]
    for _, r in recent.iterrows():
        st.markdown(f"> {r['main_problem']}  \n<small>{r['village']}, {r['taluka']} · {r['age_group']}</small>", unsafe_allow_html=True)

    st.subheader("डेटा डाउनलोड")
    st.caption("सर्व प्रतिसाद CSV फाईलमध्ये. Excel किंवा Python मध्ये उघडता येईल.")
    csv = df.to_csv(index=False).encode("utf-8-sig")  # BOM: Excel मध्ये मराठी नीट दिसते
    st.download_button(
        "⬇️ CSV डाउनलोड करा", csv,
        file_name=f"yuva-awaaz-{datetime.now(IST):%Y-%m-%d}.csv", mime="text/csv", type="primary",
    )

    if st.button("बाहेर पडा"):
        st.session_state.admin_ok = False
        st.rerun()


def _has_secrets() -> bool:
    try:
        return "admin_pin" in st.secrets
    except Exception:
        return False


if st.query_params.get("page") == "admin":
    admin_page()
else:
    survey_page()
