import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import base64
import os
import json
import uuid  # 💡 追加：ランダムなIDを生成するためのライブラリ

# ==========================================
# 1. ページ設定 & ユーザー管理（マルチユーザー対応）
# ==========================================
st.set_page_config(page_title="けやき台 最速Go", layout="centered", page_icon="icon.png")

JST = timezone(timedelta(hours=+9), 'JST')

# 💡 URLに「ユーザーID」が付いているか確認。なければ新規作成してURLにくっつける
if "uid" not in st.query_params:
    new_uid = str(uuid.uuid4())[:8]  # 8桁のランダムな英数字を作成
    st.query_params["uid"] = new_uid
    st.rerun()

# 💡 現在のユーザーのIDを取得
user_id = st.query_params["uid"]

if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

HAKATA_FILE = '博多駅時刻表.xlsx'
KIYAMA_FILE = '基山駅時刻表.xlsx'

# 💡 ファイル名にユーザーIDを組み込んで、人それぞれ別々のファイルとして保存する！
BG_FILE_PATH = f'my_background_{user_id}.dat'
SETTINGS_PATH = f'settings_{user_id}.json'

# ==========================================
# 2. 設定・背景ロジック
# ==========================================
def load_settings():
    default_settings = {"pos_x": 50, "pos_y": 50, "zoom": 100, "opacity": 0.9, "blur": True, "bg_ext": "png"}
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f:
                return json.load(f)
        except:
            return default_settings
    return default_settings

def save_settings(settings):
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f)

def apply_background_style(file_path, settings):
    if not os.path.exists(file_path):
        st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        h1, h2, h3, h4, h5, h6, p, label, span { color: white !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
        </style>
        """, unsafe_allow_html=True)
        return False

    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64_str = base64.b64encode(data).decode()
        
        bg_ext = settings.get('bg_ext', 'png')
        bg_pos = f"{settings['pos_x']}% {settings['pos_y']}%"
        bg_size = f"{settings['zoom']}%"
        
        if bg_ext in ['mp4', 'webm']:
            mime_type = f"video/{bg_ext}"
            scale_val = settings['zoom'] / 100.0
            html_code = f"""
            <video autoplay loop muted playsinline class="bg-video">
                <source src="data:{mime_type};base64,{b64_str}" type="{mime_type}">
            </video>
            <style>
            .bg-video {{
                position: fixed;
                top: 0; left: 0;
                width: 100vw; height: 100vh;
                object-fit: cover;
                object-position: {bg_pos};
                transform: scale({scale_val});
                z-index: -999;
            }}
            .stApp {{ background: transparent !important; }}
            h1, h2, h3, h4, h5, h6, .stMarkdown, p, label, span {{
                text-shadow: 0px 0px 5px rgba(0,0,0,0.8); color: white !important;
            }}
            </style>
            """
            st.markdown(html_code, unsafe_allow_html=True)
        else:
            mime_type = "image/jpeg" if bg_ext in ['jpg', 'jpeg'] else f"image/{bg_ext}"
            css = f"""
            <style>
            .stApp {{
                background-image: url("data:{mime_type};base64,{b64_str}");
                background-size: {bg_size};
                background-position: {bg_pos};
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            h1, h2, h3, h4, h5, h6, .stMarkdown, p, label, span {{
                text-shadow: 0px 0px 5px rgba(0,0,0,0.8); color: white !important;
            }}
            </style>
            """
            st.markdown(css, unsafe_allow_html=True)
            
        return True
    except Exception:
        return False

# ==========================================
# 3. サイドバーUI
# ==========================================
current_settings = load_settings()

with st.sidebar:
    st.header("🎨 デザイン設定")
    
    uploaded_file = st.file_uploader(
        "背景アップロード", 
        type=['jpg', 'png', 'jpeg', 'webp', 'gif', 'mp4'], 
        key=f"uploader_{st.session_state.uploader_key}",
        label_visibility="collapsed"
    )
    
    if uploaded_file is not None:
        ext = uploaded_file.name.split('.')[-1].lower()
        current_settings['bg_ext'] = ext
        save_settings(current_settings)
        
        with open(BG_FILE_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.session_state.uploader_key += 1
        st.rerun()

    has_file = os.path.exists(BG_FILE_PATH)
    if has_file:
        st.subheader("🔍 サイズと位置")
        new_zoom = st.slider("拡大・縮小 (%)", 50, 300, current_settings['zoom'], step=10)
        st.caption("位置の微調整")
        new_x = st.slider("横位置 (左 ↔ 右)", 0, 100, current_settings['pos_x'])
        new_y = st.slider("縦位置 (上 ↔ 下)", 0, 100, current_settings['pos_y'])
        
        current_settings['zoom'] = new_zoom
        current_settings['pos_x'] = new_x
        current_settings['pos_y'] = new_y
        
    st.write("---")
    st.subheader("🔮 カード設定")
    new_opacity = st.slider("濃さ (透明度)", 0.0, 1.0, current_settings['opacity'], 0.05)
    new_blur = st.checkbox("すりガラス効果", value=current_settings['blur'])
    
    current_settings['opacity'] = new_opacity
    current_settings['blur'] = new_blur
    save_settings(current_settings)

    if st.button("設定をリセット"):
        if os.path.exists(BG_FILE_PATH): os.remove(BG_FILE_PATH)
        if os.path.exists(SETTINGS_PATH): os.remove(SETTINGS_PATH)
        st.rerun()

apply_background_style(BG_FILE_PATH, current_settings)

# ==========================================
# 4. CSS (共通・UIデザイン & ボタン日本語化)
# ==========================================
backdrop_val = "blur(5px)" if current_settings['blur'] else "none"

st.markdown(f"""
    <style>
    html, body, [class*="css"] {{ font-family: "Helvetica Neue", Arial, sans-serif; }}
    .result-card {{
        background-color: rgba(255, 255, 255, {current_settings['opacity']});
        border-left: 8px solid #007bff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        backdrop-filter: {backdrop_val};
        -webkit-backdrop-filter: {backdrop_val};
    }}
    .result-card, .result-card * {{ text-shadow: none !important; color: #333 !important; }}
    
    [data-testid='stFileUploader'] {{
        background-color: rgba(255, 255, 255, 0.95);
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #007bff;
        text-align: center;
    }}
    [data-testid='stFileUploadDropzone'] > div > div > span,
    [data-testid='stFileUploadDropzone'] > div > div > small {{ display: none !important; }}
    [data-testid='stFileUploadDropzone'] button {{
        position: relative !important; color: transparent !important; background-color: #007bff !important;
        width: 100% !important; border-radius: 8px !important; padding: 12px !important;
        margin-top: 5px !important; border: none !important;
    }}
    [data-testid='stFileUploadDropzone'] button::after {{
        content: '📁 背景をアップロード' !important; position: absolute !important; top: 50% !important;
        left: 50% !important; transform: translate(-50%, -50%) !important; color: white !important;
        font-weight: bold !important; font-size: 1rem !important; visibility: visible !important;
    }}
    [data-testid='stFileUploader'] label, [data-testid='stFileUploader'] span, 
    [data-testid='stFileUploader'] small, [data-testid='stFileUploader'] div {{ color: #333 !important; text-shadow: none !important; }}

    .big-time {{ font-size: 2.5rem; font-weight: bold; color: #333; line-height: 1.0; }}
    .station-name {{ font-size: 0.9rem; color: #666; margin-bottom: 5px; }}
    .duration-badge {{ background-color: #ff4b4b; color: white; padding: 5px 12px; border-radius: 20px; font-size: 0.9rem; font-weight: bold; }}
    .timeline {{ border-left: 2px solid #ddd; margin-left: 8px; padding-left: 20px; margin-top: 15px; margin-bottom: 10px; }}
    .timeline-item {{ margin-bottom: 15px; position: relative; }}
    .timeline-icon {{ position: absolute; left: -29px; top: 0; background: rgba(255,255,255,0.8); border-radius: 50%; font-size: 1.2rem; line-height: 1.2; }}
    .stRadio label {{ color: white !important; font-weight: bold; }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 5. データ処理 & ルート検索
# ==========================================
def parse_time(t_val):
    if pd.isna(t_val) or t_val == "": return None
    if isinstance(t_val, datetime): return t_val.time()
    if isinstance(t_val, type(datetime.now().time())): return t_val
    try:
        t_str = str(t_val).split(".")[0]
        if len(t_str) == 8: return datetime.strptime(t_str, "%H:%M:%S").time()
        elif len(t_str) == 5: return datetime.strptime(t_str, "%H:%M").time()
    except: return None
    return None

@st.cache_data
def load_data():
    df_h = pd.read_excel(HAKATA_FILE, header=1, usecols="A:G")
    df_h.columns = ['dep_time', 'dest', 'type', 'minami_arr', 'futsuka_arr', 'keyaki_arr', 'kiyama_arr']
    df_k = pd.read_excel(KIYAMA_FILE, header=1, usecols="A:D")
    df_k.columns = ['dep_time', 'dest', 'type', 'keyaki_arr']
    return df_h, df_k

def find_routes(start_station_name, start_col_name, target_time_obj, df_h, df_k):
    routes = []
    today_date = datetime.now(JST).date()
    now_dt = datetime.combine(today_date, target_time_obj)
    
    for _, train1 in df_h.iterrows():
        my_dep_time = parse_time(train1[start_col_name])
        if my_dep_time is None: continue
        
        train1_dep_dt = datetime.combine(today_date, my_dep_time)
        if train1_dep_dt < now_dt: continue
        if (train1_dep_dt - now_dt).seconds > 1800: continue

        keyaki_arr_time = parse_time(train1['keyaki_arr'])
        if keyaki_arr_time:
            arrival_dt = datetime.combine(today_date, keyaki_arr_time)
            if arrival_dt < train1_dep_dt: arrival_dt += timedelta(days=1)
            
            if arrival_dt > train1_dep_dt:
                routes.append({
                    "type": "直行",
                    "dep_time": my_dep_time, "arr_time": keyaki_arr_time, "train1_type": train1['type'],
                    "arrival_obj": arrival_dt, "total_minutes": (arrival_dt - train1_dep_dt).seconds // 60,
                    "timeline": [
                        {"icon": "🔵", "time": my_dep_time.strftime('%H:%M'), "text": f"{start_station_name} 発 ({train1['type']}・{train1['dest']}行)"},
                        {"icon": "🏁", "time": keyaki_arr_time.strftime('%H:%M'), "text": "けやき台 着"}
                    ]
                })
            
        if start_station_name != "二日市":
            futsuka_arr_time1 = parse_time(train1['futsuka_arr'])
            if futsuka_arr_time1:
                futsuka_arr_dt1 = datetime.combine(today_date, futsuka_arr_time1)
                if futsuka_arr_dt1 < train1_dep_dt: futsuka_arr_dt1 += timedelta(days=1)
                if futsuka_arr_dt1 > train1_dep_dt:
                    transfer_ready_dt = futsuka_arr_dt1 + timedelta(minutes=2)
                    for _, train2 in df_h.iterrows():
                        keyaki_arr_time2 = parse_time(train2['keyaki_arr'])
                        if not keyaki_arr_time2: continue
                        futsuka_arr_time2 = parse_time(train2['futsuka_arr'])
                        if not futsuka_arr_time2: continue
                        futsuka_arr_dt2 = datetime.combine(today_date, futsuka_arr_time2)
                        if futsuka_arr_dt2 < train1_dep_dt: futsuka_arr_dt2 += timedelta(days=1)
                        if futsuka_arr_dt2 >= transfer_ready_dt:
                            final_arr_dt = datetime.combine(today_date, keyaki_arr_time2)
                            if final_arr_dt < futsuka_arr_dt2: final_arr_dt += timedelta(days=1)
                            if (futsuka_arr_dt2 - futsuka_arr_dt1).seconds > 1200: continue
                            wait_min = (futsuka_arr_dt2 - futsuka_arr_dt1).seconds // 60
                            routes.append({
                                "type": "二日市乗換",
                                "dep_time": my_dep_time, "arr_time": keyaki_arr_time2,
                                "arrival_obj": final_arr_dt, "total_minutes": (final_arr_dt - train1_dep_dt).seconds // 60,
                                "timeline": [
                                    {"icon": "🔵", "time": my_dep_time.strftime('%H:%M'), "text": f"{start_station_name} 発 ({train1['type']}・{train1['dest']}行)"},
                                    {"icon": "🔶", "time": futsuka_arr_time1.strftime('%H:%M'), "text": f"二日市 着 (待ち{wait_min}分)"},
                                    {"icon": "🔻", "time": futsuka_arr_time2.strftime('%H:%M'), "text": f"二日市 発 ({train2['type']}・{train2['dest']}行)"},
                                    {"icon": "🏁", "time": keyaki_arr_time2.strftime('%H:%M'), "text": "けやき台 着"}
                                ]
                            })
                            break 

        kiyama_arr_time = parse_time(train1['kiyama_arr'])
        if kiyama_arr_time:
            kiyama_arr_dt = datetime.combine(today_date, kiyama_arr_time)
            if kiyama_arr_dt < train1_dep_dt: kiyama_arr_dt += timedelta(days=1)
            if kiyama_arr_dt > train1_dep_dt:
                transfer_ready_time = (kiyama_arr_dt + timedelta(minutes=3)).time()
                connected_train = None
                for _, k_train in df_k.iterrows():
                    k_dep = parse_time(k_train['dep_time'])
                    if k_dep and k_dep >= transfer_ready_time:
                        connected_train = k_train
                        break 
                if connected_train is not None:
                    final_arr_time = parse_time(connected_train['keyaki_arr'])
                    if final_arr_time:
                        final_arr_dt = datetime.combine(today_date, final_arr_time)
                        if final_arr_dt < kiyama_arr_dt: final_arr_dt += timedelta(days=1)
                        k_dep_time = parse_time(connected_train['dep_time'])
                        wait_min = (datetime.combine(today_date, k_dep_time) - kiyama_arr_dt).seconds // 60
                        routes.append({
                            "type": "基山経由",
                            "dep_time": my_dep_time, "arr_time": final_arr_time,
                            "arrival_obj": final_arr_dt, "total_minutes": (final_arr_dt - train1_dep_dt).seconds // 60,
                            "timeline": [
                                {"icon": "🔵", "time": my_dep_time.strftime('%H:%M'), "text": f"{start_station_name} 発 ({train1['type']}・{train1['dest']}行)"},
                                {"icon": "🔶", "time": kiyama_arr_time.strftime('%H:%M'), "text": f"基山 着 (待ち{wait_min}分)"},
                                {"icon": "🔻", "time": k_dep_time.strftime('%H:%M'), "text": f"基山 発 ({connected_train['type']}・{connected_train['dest']}行)"},
                                {"icon": "🏁", "time": final_arr_time.strftime('%H:%M'), "text": "けやき台 着"}
                            ]
                        })

    routes.sort(key=lambda x: x['arrival_obj'])
    return routes

# ==========================================
# 6. UI 表示
# ==========================================
try:
    df_hakata, df_kiyama = load_data()
except Exception as e:
    st.error(f"データ読み込みエラー: {e}")
    st.stop()

st.markdown("<h3 style='color:white; text-shadow: 2px 2px 4px black;'>🚃 けやき台 最速Go</h3>", unsafe_allow_html=True)

station_map = {"博多": "dep_time", "南福岡": "minami_arr", "二日市": "futsuka_arr"}
selected_station = st.radio("出発駅", list(station_map.keys()), horizontal=True, label_visibility="collapsed")
target_col = station_map[selected_station]

raw_times = df_hakata[target_col].apply(parse_time).dropna().unique()
sorted_times = sorted(raw_times)
if len(sorted_times) == 0:
    st.warning("データなし")
    st.stop()

now = datetime.now(JST).time()
future_times = [t for t in sorted_times if t >= now]
past_times = [t for t in sorted_times if t < now]
display_times = future_times + past_times
if not display_times: display_times = sorted_times

time_labels = [t.strftime("%H:%M") for t in display_times]

st.markdown(f"<p style='color:white; text-shadow: 1px 1px 2px black;'>▼ <strong>{selected_station}</strong> 発</p>", unsafe_allow_html=True)

selected_label = st.selectbox("時刻", options=time_labels, index=0, label_visibility="collapsed")
selected_time_obj = datetime.strptime(selected_label, "%H:%M").time()

results = find_routes(selected_station, target_col, selected_time_obj, df_hakata, df_kiyama)

if not results:
    st.warning("ルートが見つかりません")
else:
    best = results[0]
    
    html_content = f"""<div class="result-card">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div style="text-align: left;">
<div class="station-name">{selected_station} 発</div>
<div class="big-time">{best['dep_time'].strftime('%H:%M')}</div>
</div>
<div style="font-size: 1.5rem; color: #aaa;">➡</div>
<div style="text-align: right;">
<div class="station-name">けやき台 着</div>
<div class="big-time">{best['arr_time'].strftime('%H:%M')}</div>
</div>
</div>
<div style="margin-top: 10px; display: flex; justify-content: space-between; align-items: center;">
<span class="duration-badge">所要 {best['total_minutes']}分</span>
<span style="color: #666; font-size: 0.9rem;">{best['type']}</span>
</div>
<div class="timeline">"""
    
    for item in best['timeline']:
        html_content += f"""<div class="timeline-item">
<span class="timeline-icon">{item['icon']}</span>
<strong>{item['time']}</strong> <span style="color: #555; margin-left: 5px;">{item['text']}</span>
</div>"""
    
    html_content += "</div></div>"
    st.markdown(html_content, unsafe_allow_html=True)
    
    if len(results) > 1:
        with st.expander("その他のルート"):
            for r in results[1:]:
                diff_min = r['total_minutes'] - best['total_minutes']
                st.markdown(f"<span style='color:black;'>**{r['arr_time'].strftime('%H:%M')} 着** | {r['type']} <small>(+{diff_min if diff_min > 0 else 0}分)</small></span>", unsafe_allow_html=True)
                for item in r['timeline']:
                     st.caption(f"{item['time']} {item['text']}")
