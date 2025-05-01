import streamlit as st
import pandas as pd
from streamlit_js_eval import get_geolocation
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import folium
import io

import db

st.title("現在位置と検索地点をマップに表示")

def st_init():
    if "store_pins" not in st.session_state:
        st.session_state.store_pins = []
    if "lat_min" not in st.session_state:
        st.session_state.lat_min = 0
    if "lat_max" not in st.session_state:
        st.session_state.lat_max = 0
    if "lon_min" not in st.session_state:
        st.session_state.lon_min = 0
    if "lon_max" not in st.session_state:
        st.session_state.lon_max = 0
    if "center_lat" not in st.session_state:
        st.session_state.center_lat = 35.681236  # 東京駅
    if "center_lon" not in st.session_state:
        st.session_state.center_lon = 139.767125
    if "zoom_level" not in st.session_state:
        st.session_state.zoom_level = 15

def get_color(row):
    if row["閉店済"] == 1 or row["閉店済"] == "1":
        return "grey"
    elif row["訪問済"] == 1 or row["訪問済"] == "1":
        return "blue"
    else:
        return "red"

def update_store_pin(map_data):
    if map_data and "bounds" in map_data:
        bounds = map_data["bounds"]
        if "_southWest" in bounds and "_northEast" in bounds:
            # --- セッションに店舗ピンを保存 ---

            lat_min = bounds["_southWest"]["lat"]
            lat_max = bounds["_northEast"]["lat"]
            lon_min = bounds["_southWest"]["lng"]
            lon_max = bounds["_northEast"]["lng"]

            st.session_state.lat_min = lat_min
            st.session_state.lat_max = lat_max
            st.session_state.lon_min = lon_min
            st.session_state.lon_max = lon_max
            # センターとズームを保存
            if "center" in map_data:
                st.session_state.center_lat = map_data["center"]["lat"]
                st.session_state.center_lon = map_data["center"]["lng"]

            if "zoom" in map_data:
                st.session_state.zoom_level = map_data["zoom"]

            store_df = db.get_stores_in_area(lat_min, lat_max, lon_min, lon_max)
            st.write(store_df)

            st.session_state.store_pins = []
            for idx, row in store_df.iterrows():
                pin_info = {
                    "lat": row["緯度"],
                    "lon": row["経度"],
                    "name": row["店舗名"],
                    "color": get_color(row)
                }
                st.session_state.store_pins.append(pin_info)


if __name__ == "__main__":
    # ①イニシャル処理
    st_init()

    # --- 現在位置取得 ---
    location = get_geolocation()

    # --- 検索ボックス ---
    search_query = st.text_input("場所を検索", "")
    search_result = None
    geolocator = Nominatim(user_agent="streamlit_app")

    if search_query:
        try:
            search_result = geolocator.geocode(search_query)
            if search_result:
                st.success(
                    f"検索結果: {search_result.address}（緯度 {search_result.latitude:.6f}, 経度 {search_result.longitude:.6f}）")
            else:
                st.warning("該当する場所が見つかりませんでした。")
        except Exception as e:
            st.error(f"検索中にエラーが発生しました: {e}")

    # --- マップ作成 ---
    if search_result:
        st.session_state.center_lat = search_result.latitude
        st.session_state.center_lon = search_result.longitude
    elif location:
        st.session_state.center_lat = location['coords']['latitude']
        st.session_state.center_lon = location['coords']['longitude']

    m = folium.Map(location=[st.session_state.center_lat, st.session_state.center_lon],
                   zoom_start=st.session_state.zoom_level)

    # --- 既存ピンをマップに追加（store_pins）---
    for pin in st.session_state.store_pins:
        folium.Marker(
            location=[pin["lat"], pin["lon"]],
            popup=pin["name"],
            icon=folium.Icon(color=pin["color"])
        ).add_to(m)


    # --- 現在位置をマップに追加 ---
    if location:
        folium.Marker(
            location=[location['coords']['latitude'], location['coords']['longitude']],
            popup="現在地",
            icon=folium.Icon(color="green")
        ).add_to(m)

    # --- 検索地点をマップに追加 ---
    if search_result:
        folium.Marker(
            location=[search_result.latitude, search_result.longitude],
            popup="検索地点",
            icon=folium.Icon(color="red")
        ).add_to(m)

    # --- マップを表示 ---
    map_data = st_folium(m, width=700, height=500)

    if st.sidebar.button("店舗情報更新"):
        update_store_pin(map_data)
        st.write(st.session_state.store_pins)
        st.rerun()

    # ファイルアップロードウィジェット（ドラッグアンドドロップ対応）
    uploaded_file = st.sidebar.file_uploader("CSVファイルをアップロードしてください", type="csv")

    # ファイルがアップロードされたら読み込む
    if uploaded_file is not None:
        try:
            # pandasで読み込み（文字コードは自動判定またはshift_jisなど指定可）
            df_csv = pd.read_csv(uploaded_file)
            db.update_store_table_from_df(df_csv)


        except Exception as e:
            st.sidebar.error(f"読み込み中にエラーが発生しました: {e}")


    if st.sidebar.button("CSV取得"):
        df_download =  db.get_table_to_df()
        # CSV形式に変換（UTF-8 with BOMにするとExcelでも文字化けしにくい）
        csv = df_download.to_csv(index=False, encoding='utf-8-sig')
        csv_bytes = io.BytesIO(csv.encode('utf-8-sig'))

        st.sidebar.download_button(
            label="📥 CSVをダウンロード",
            data=csv_bytes,
            file_name="store.csv",
            mime="text/csv"
        )