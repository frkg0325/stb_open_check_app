import streamlit as st  # streamlit
from streamlit_folium import st_folium  # streamlitでfoliumを使う
import folium  # folium
import pandas as pd  # CSVをデータフレームとして読み込む
import sqlite3
import os
import copy

DATA_FILE_DIR_STB = os.path.dirname(__file__) + '/スタバ店舗.csv'
DATA_FILE_DIR_PRE = os.path.dirname(__file__) + '/都道府県.csv'
DATA_FILE_DIR_TOKYO = os.path.dirname(__file__) + '/東京23区.csv'
db_path = os.path.dirname(__file__) + '/check.db'
output_csv = os.path.dirname(__file__) + '/check.csv'
table_name = "CheckTable"
index_name = "store"

MAP_WIDTH = 1200 * 1/3
MAP_HEIGHT = 800 * 3/4

def get_check(store):
    # 1.データベースに接続
    conn = sqlite3.connect(db_path)
    # 2.sqliteを操作するカーソルオブジェクトを作成
    cur = conn.cursor()
    # 3
    try:
        sql = "SELECT * FROM " + table_name + " WHERE store = '" + store + "';"
        cur.execute(sql)
        res = cur.fetchone()
    except sqlite3.Error as e:
        print("失敗")
        print(e)
    conn.commit()
    conn.close()
    return res[1]

def update_check(check, store):
    # 1.データベースに接続
    conn = sqlite3.connect(db_path)
    # 2.sqliteを操作するカーソルオブジェクトを作成
    cur = conn.cursor()
    # 3
    try:
        sql = "UPDATE " + table_name + " SET 'check' = '" + str(check) + "' WHERE store = '" + store + "';"
        cur.execute(sql)
    except sqlite3.Error as e:
        print("失敗")
    conn.commit()
    conn.close()

def popup_spot(m, df):
    # 読み込んだデータ(緯度・経度、ポップアップ用文字、アイコンを表示)
    for i, row in df.iterrows():
        # ポップアップの作成(都道府県名＋都道府県庁所在地＋人口＋面積)
        pop = f"{row['店舗名']}<br>({row['住所']})"
        if get_check(row['店舗名']) == 0:
            icon_color = "red"
        else:
            icon_color = "blue"
        folium.Marker(
            # 緯度と経度を指定
            location=[row['緯度'], row['経度']],
            # ツールチップの指定(都道府県名)
            tooltip=row['店舗名'],
            # ポップアップの指定ana
            popup=folium.Popup(pop, max_width=300),
            # アイコンの指定(アイコン、色)
            icon=folium.Icon(icon="home", icon_color="white", color=icon_color)
        ).add_to(m)



# ページ設定
st.set_page_config(
    page_title="streamlit-foliumテスト",
    page_icon="🗾",
    layout="wide"
)

# 表示するデータを読み込み
df = pd.read_csv(DATA_FILE_DIR_STB, encoding="shift-jis")
# 都道府県の読み込み
df_pre = pd.read_csv(DATA_FILE_DIR_PRE, encoding="shift-jis")
selected_pre = st.sidebar.selectbox("都道府県を選択してください", df_pre["都道府県"].values.tolist())

# 都道府県で絞る
df_store = df[df['住所'].str.contains(selected_pre)]

if selected_pre == "東京都":
    # 東京
    df_tokyo = pd.read_csv(DATA_FILE_DIR_TOKYO, encoding="shift-jis")
    selected_tokyo = st.sidebar.selectbox("区を選択してください", df_tokyo["23区"].values.tolist())

    if selected_tokyo == "23区外":
        for tokyo in df_tokyo["23区"].values.tolist():
            if not tokyo == "23区外":
                if not tokyo == "全て":
                    df_store = copy.copy(df_store[~df_store['住所'].str.contains(tokyo)])

    elif not selected_tokyo == "全て":
        # 23区で絞る
        df_store = df_store[df_store['住所'].str.contains(selected_tokyo)]

    # 緯度、経度
    ido = df_tokyo[df_tokyo["23区"] == selected_tokyo]["緯度"].values[0]
    keido = df_tokyo[df_tokyo["23区"] == selected_tokyo]["経度"].values[0]
    # 拡大率
    df_zoom = df_tokyo[df_tokyo["23区"].str.contains(selected_tokyo)]
    zoom_set = df_tokyo["拡大率"].values.tolist()[0]


else:
    # 東京以外
    #緯度、経度
    ido = df_pre[df_pre["都道府県"] == selected_pre]["緯度"].values[0]
    keido = df_pre[df_pre["都道府県"] == selected_pre]["経度"].values[0]
    # 拡大率
    df_zoom = df_pre[df_pre["都道府県"].str.contains(selected_pre)]
    zoom_set = df_zoom["拡大率"].values.tolist()[0]


ds_store = df_store["店舗名"]

# print(ds_store)

list_store = ds_store.to_list()

# 地図の中心の緯度/経度、タイル、初期のズームサイズを指定します。
m = folium.Map(
    # 地図の中心位置の指定(選択された都道府県の中心）
    location=[ido, keido],
    # タイル、アトリビュートの指定
    tiles='https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png',
    attr='スターバックス店舗 2024/01/01',
    # ズームを指定
    zoom_start=zoom_set
)
if st.checkbox("表示"):
    popup_spot(m, df_store)

for store in list_store:
    index_no = df[df["店舗名"] == store].index.values[0]
    if get_check(store) == 1:
        check_init = True
    else:
        check_init = False

    if st.sidebar.checkbox(store,value=check_init):
        update_check(1, store)
        df.to_csv(DATA_FILE_DIR_STB, encoding="shift-jis", index=False)
    else:
        update_check(0, store)
        df.to_csv(DATA_FILE_DIR_STB, encoding="shift-jis", index=False)

st_data = st_folium(m, width=MAP_WIDTH, height=MAP_HEIGHT)

# 1.データベースに接続
conn = sqlite3.connect(db_path)
# 作成したテーブルをpandasで読み出す
df_db = pd.read_sql("SELECT * FROM " + table_name, conn)

st.download_button(
    label="チェックした店舗のCSVデータ",
    data=df_db.to_csv(index=False).encode("shift-jis"),
    file_name=DATA_FILE_DIR_STB,  # ダウンロードするファイル名を指定
    key='download-csv'
)


