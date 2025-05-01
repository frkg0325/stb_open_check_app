import sqlite3
import pandas as pd
import os

db_path = os.path.join(os.path.dirname(__file__), 'store.db')
table_name = 'store_table'


def get_stores_in_area(lat_min, lat_max, lon_min, lon_max):
    conn = sqlite3.connect(db_path,check_same_thread=False)

    query = f"""
    SELECT 店舗名, 緯度, 経度 ,訪問済, 閉店済
    FROM {table_name}
    WHERE 緯度 BETWEEN ? AND ?
      AND 経度 BETWEEN ? AND ?;
    """
    df = pd.read_sql_query(query, conn, params=(lat_min, lat_max, lon_min, lon_max))

    conn.close()
    return df

def get_table_to_df():
    """
    store_table の内容を CSV ファイルとしてエクスポートする関数。

    Parameters:
        csv_path (str): 保存するCSVファイルのパス（デフォルトはカレントディレクトリ）。
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)

    # テーブルをDataFrameに読み込む
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    return df


def update_store_table_from_df(df):
    """
    DataFrameの内容でstore_tableを全て更新する関数。
    既存のデータは削除され、引数dfの内容で上書きされる。

    Parameters:
        df (pd.DataFrame): 書き込むデータフレーム。カラム名はテーブルと一致している必要があります。
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()

    # 既存データを削除
    cursor.execute(f"DELETE FROM {table_name};")
    conn.commit()

    # データを挿入（to_sql）
    df.to_sql(table_name, conn, if_exists='append', index=False)

    conn.close()
