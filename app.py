import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import base64
import os
import json

# ==========================================
# 1. ページ設定 & セッション状態の初期化
# ==========================================
st.set_page_config(page_title="けやき台 最速Go", layout="centered", page_icon="🚃")

# アップロードボタンを強制的にリセットするためのキー
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

HAKATA_FILE = '博多駅時刻表.xlsx'
KIYAMA_FILE = '基山駅時刻表.xlsx'
BG_IMAGE_PATH = 'my_background.png'
SETTINGS_PATH = 'settings.json'

# ==========================================
# 2. 設定・背景ロジック
# ==========================================

# 設定読み込み
def load_settings():
    default_settings = {"pos_x": 50, "pos_y": 50, "zoom": 100, "opacity": 0.9, "blur": True}
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r') as f:
                return json.load(f)
        except:
            return default_settings
    return default_settings

# 設定保存
def save_settings(settings):
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(settings, f)

# 背景適用（ファイルから読み込む）
def apply_background_style(image_path, settings):
    if not os.path.exists(image_path):
        # デフォルト背景
        st.markdown("""
        <style>
        .stApp { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        h1, h2, h3, h4, h5, h6, p, label, span { color: white !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
        </style>
        """, unsafe_allow_html=True)
        return False

    try:
        with open(image_path, "rb") as f:
            data = f.read()
        b64_str = base64.b64encode(data).decode()
        
        bg_pos = f"{settings['pos_x']}% {settings['pos_y']}%"
        bg_size = f"{settings['zoom']}%"
        
        # WebPなどが来ても正しいMIMEタイプでCSSを作るために拡張子判定などはせず、
        # Streamlitが判定したtypeを使うか、汎用的に image/png として扱う（ブラウザは大抵解釈してくれる）
        # ここでは保存時に拡張子が変わる可能性があるため、汎用的な data URI scheme を使います
        
        css = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{b64_str}");
            background-size: {bg_size};
            background-position: {bg_pos};
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        h1, h2, h3, h4, h5, h6, .stMarkdown, p, label, span {{
            text-shadow: 0px 0px 5px rgba(0,0,0,0.8);
            color: white !important;
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
    
    # 画像アップロード (webpを追加しました)
    uploaded_file = st.file_uploader(
        "背景画像を変更", 
        type=['jpg', 'png', 'jpeg', 'webp'], 
        key=f"uploader_{st.session_state.uploader_key}"
    )
    
    # 画像が選択された瞬間の処理
    if uploaded_file is not None:
        # 1. 画像を保存 (拡張子に関わらず my_background.png として保存して扱います)
        with open(BG_IMAGE_PATH, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 2. キーを更新してアップローダーを次回強制リセット
        st.session_state.uploader_key += 1
        
        # 3. 再読み込みして即座に反映
        st.rerun()

    # 以下、調整UI
    has_image = os.path.exists(BG_IMAGE_PATH)
    
    if has_image:
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

    # 設定保存
    save_settings(current_settings)

    # リセット
    if st.button("設定をリセット"):
        if os.path.exists(BG_IMAGE_PATH): os.remove(BG_IMAGE_PATH)
        if os.path.exists(SETTINGS_PATH): os.remove(SETTINGS_PATH)
        st.rerun()

# 背景適用
apply_background_style(BG_IMAGE_PATH, current_settings)

# ==========================================
# 4. CSS (共通・UIデザイン)
# ==========================================
backdrop_val = "blur(5px)" if current_settings['blur'] else "none"

st.markdown(f"""
    <style>
    html, body, [class*="css"] {{ font-family: "Helvetica Neue", Arial, sans-serif; }}
    
    /* カードデザイン */
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
    
    /* アップロードボタン（常時見やすく） */
    [data-testid='stFileUploader'] {{
        background-color: rgba(255, 255, 255, 0.95);
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #007bff;
    }}
    [data-testid='stFileUploader'] label, 
    [data-testid='stFileUploader'] span, 
    [data-testid='stFileUploader'] small, 
    [data-testid='stFileUploader'] div {{
        color: #333 !important; text-shadow: none !important;
    }}
    
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
    now_dt = datetime.combine(datetime.today(), target_time_obj)
    
    for _, train1 in df_h.iterrows():
        my_dep_time = parse_time(train1[start_col_name])
        if my_dep_time is None: continue
        
        train1_dep_dt = datetime.combine(datetime.today(), my_dep_time)
        if train1_dep_dt < now_dt: continue
        if (train1_dep_dt - now_dt).seconds > 1800: continue

        # A. 直行
        keyaki_arr_time = parse_time(train1['keyaki_arr'])
        if keyaki_arr_time:
            arrival_dt = datetime.combine(datetime.today(), keyaki_arr_time)
            if arrival_dt < train1_dep_dt: arrival_dt += timedelta(days=1)
            
            if arrival_dt > train1_dep_dt:
                routes.append({
                    "type": "直行",
                    "dep_time": my_dep_time,
                    "arr_time": keyaki_arr_time,
                    "train1_type": train1['type'],
                    "arrival_obj": arrival_dt,
                    "total_minutes": (arrival_dt - train1_dep_dt).seconds // 60,
                    "timeline": [
                        {"icon": "🔵", "time": my_dep_time.strftime('%H:%M'), "text": f"{start_station_name} 発 ({train1['type']}・{train1['dest']}行)"},
                        {"icon": "🏁", "time": keyaki_arr_time.strftime('%H:%M'), "text": "けやき台 着"}
                    ]
                })
            
        # B. 二日市乗換
        if start_station_name != "二日市":
            futsuka_arr_time1 = parse_time(train1['futsuka_arr'])
            if futsuka_arr_time1:
                futsuka_arr_dt1 = datetime.combine(datetime.today(), futsuka_arr_time1)
                if futsuka_arr_dt1 < train1_dep_dt: futsuka_arr_dt1 += timedelta(days=1)
                if futsuka_arr_dt1 > train1_dep_dt:
                    transfer_ready_dt = futsuka_arr_dt1 + timedelta(minutes=2)
                    for _, train2 in df_h.iterrows():
                        keyaki_arr_time2 = parse_time(train2['keyaki_arr'])
                        if not keyaki_arr_time2: continue
                        futsuka_arr_time2 = parse_time(train2['futsuka_arr'])
                        if not futsuka_arr_time2: continue
                        futsuka_arr_dt2 = datetime.combine(datetime.today(), futsuka_arr_time2)
                        if futsuka_arr_dt2 < train1_dep_dt: futsuka_arr_dt2 += timedelta(days=1)
                        if futsuka_arr_dt2 >= transfer_ready_dt:
                            final_arr_dt = datetime.combine(datetime.today(), keyaki_arr_time2)
                            if final_arr_dt < futsuka_arr_dt2: final_arr_dt += timedelta(days=1)
                            if (futsuka_arr_dt2 - futsuka_arr_dt1).seconds > 1200: continue
                            wait_min = (futsuka_arr_dt2 - futsuka_arr_dt1).seconds // 60
                            routes.append({
                                "type": "二日市乗換",
                                "dep_time": my_dep_time,
                                "arr_time": keyaki_arr_time2,
                                "arrival_obj": final_arr_dt,
                                "total_minutes": (final_arr_dt - train1_dep_dt).seconds // 60,
                                "timeline": [
                                    {"icon": "🔵", "time": my_dep_time.strftime('%H:%M'), "text": f"{start_station_name} 発 ({train1['type']}・{train1['dest']}行)"},
                                    {"icon": "🔶", "time": futsuka_arr_time1.strftime('%H:%M'), "text": f"二日市 着 (待ち{wait_min}分)"},
                                    {"icon": "🔻", "time": futsuka_arr_time2.strftime('%H:%M'), "text": f"二日市 発 ({train2['type']}・{train2['dest']}行)"},
                                    {"icon": "🏁", "time": keyaki_arr_time2.strftime('%H:%M'), "text": "けやき台 着"}
                                ]
                            })
                            break 

        # C. 基山乗換
        kiyama_arr_time = parse_time(train1['kiyama_arr'])
        if kiyama_arr_time:
            kiyama_arr_dt = datetime.combine(datetime.today(), kiyama_arr_time)
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
                        final_arr_dt = datetime.combine(datetime.today(), final_arr_time)
                        if final_arr_dt < kiyama_arr_dt: final_arr_dt += timedelta(days=1)
                        k_dep_time = parse_time(connected_train['dep_time'])
                        wait_min = (datetime.combine(datetime.today(), k_dep_time) - kiyama_arr_dt).seconds // 60
                        routes.append({
                            "type": "基山経由",
                            "dep_time": my_dep_time,
                            "arr_time": final_arr_time,
                            "arrival_obj": final_arr_dt,
                            "total_minutes": (final_arr_dt - train1_dep_dt).seconds // 60,
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

now = datetime.now().time()
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