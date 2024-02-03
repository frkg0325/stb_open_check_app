import streamlit as st  # streamlit
from streamlit_folium import st_folium  # streamlitでfoliumを使う
import folium  # folium
import pandas as pd  # CSVをデータフレームとして読み込む
import sqlite3
import os
import copy

# CSVデータ
DATA_FILE_DIR_STB = os.path.dirname(__file__) + '/スタバ店舗.csv'
DATA_FILE_DIR_PRE = os.path.dirname(__file__) + '/都道府県.csv'
DATA_FILE_DIR_TOKYO = os.path.dirname(__file__) + '/東京23区.csv'
output_csv = os.path.dirname(__file__) + '/check.csv'

# データベース
db_path = os.path.dirname(__file__) + '/check.db'
# 店舗テーブル
table_name = "CheckTable"
index_name_check = "check"
index_name = "store"
# 設定テーブル
table_name_conf = "ConfTable"
index_name_conf = "conf"
index_name_target = "target"
conf_pre = "prefectures"
conf_tokyo = "tokyo"


MAP_WIDTH = 1200 * 1/3
MAP_HEIGHT = 800 * 5/8


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

def get_conf(conf_target):
    # 1.データベースに接続
    conn = sqlite3.connect(db_path)
    # 2.sqliteを操作するカーソルオブジェクトを作成
    cur = conn.cursor()
    sql = "SELECT * FROM " + table_name_conf
    df = pd.read_sql(sql, con=conn)

    try:
        sql = "SELECT * FROM " + table_name_conf + " WHERE target = '" + conf_target + "'";""
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

def update_conf(conf, target):
    # 1.データベースに接続
    conn = sqlite3.connect(db_path)
    # 2.sqliteを操作するカーソルオブジェクトを作成
    cur = conn.cursor()
    # 3
    try:
        sql = "UPDATE " + table_name_conf + " SET conf = '" +  conf + "'  WHERE target ='" + target + "'";""
        print(sql)
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

def selected_target_to_index(target_csv, selected_target ):
    # データフレーム取得
    df = pd.read_csv(target_csv, dtype=object, encoding="shift-jis", index_col=0)  # CSV 読込
    # リストに変換
    index_list = df.index.to_list()
    # index番号を変更
    return index_list.index(selected_target)

def make_table():
    try:
        conn = sqlite3.connect(db_path)
        sql = "DROP TABLE " + table_name_conf
        conn.execute(sql)  # sql文を実行
    except:
        print("miss")
    df_index = [conf_pre, conf_tokyo]
    df_data = ["東京都",
               "未選択"]
    df_col = [index_name_conf]
    df_db = pd.DataFrame(data=df_data, index= df_index, columns=df_col)
    df_db[index_name_target] = df_db.index
    df_db = df_db.set_index(index_name_target)
    with sqlite3.connect(db_path) as conn:
        df_db.to_sql(table_name_conf, con=conn)  # SQLiteにCSVをインポート
    conn.execute()
    conn.close()

make_table()


# # データベースに接続
# conn = sqlite3.connect(db_path)
# # カーソルを作成
# cursor = conn.cursor()
# # テーブルの一覧を取得するSQLクエリ
# table_list_query = "SELECT name FROM sqlite_master WHERE type='table';"
# # SQLクエリを実行
# cursor.execute(table_list_query)
# # 結果を取得
# tables = cursor.fetchall()
# # テーブルの一覧を表示
# for table in tables:
#     st.write(table[0])
# # 接続を閉じる
# conn.close()



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

# 選択されている都道府県の番号を取得
index_pre_no = selected_target_to_index(DATA_FILE_DIR_PRE,get_conf(conf_pre))
selected_pre = st.sidebar.selectbox("都道府県を選択してください", df_pre["都道府県"].values.tolist(),index=index_pre_no)
# 選択されているもので更新
update_conf(selected_pre,conf_pre)

# 都道府県で絞る
df_store = df[df['住所'].str.contains(selected_pre)]

if selected_pre == "東京都":
    # 東京
    df_tokyo = pd.read_csv(DATA_FILE_DIR_TOKYO, encoding="shift-jis")
    # 選択されている区の番号を取得
    index_tokyo_no = selected_target_to_index(DATA_FILE_DIR_TOKYO, get_conf(conf_tokyo))
    selected_tokyo = st.sidebar.selectbox("区を選択してください", df_tokyo["23区"].values.tolist())
    # 選択されているもので更新
    update_conf(selected_tokyo, conf_tokyo)

    if selected_tokyo == "23区外":
        for tokyo in df_tokyo["23区"].values.tolist():
            if not tokyo == "23区外":
                if not tokyo == "全て":
                    df_store = copy.copy(df_store[~df_store['住所'].str.contains(tokyo)])
    elif selected_tokyo == "未選択":
        print(df_store)
        # df_store = df_store.drop(range(len(df_store)))
        df_store =  pd.DataFrame(columns=df_store.columns)
        print(df_store)

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


# except:
#     st.button("再読み込み")