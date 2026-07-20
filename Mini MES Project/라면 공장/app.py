import streamlit as st
import sqlite3
import pandas as pd

st.title('테스트 화면')
st.write('### [item table]')

conn = sqlite3.connect('./sql/mini_mes.db')

cur = conn.cursor()
query1 = 'SELECT * FROM item'
query2 = 'SELECT * FROM lot'
query3 = 'SELECT * FROM production'
query4 = 'SELECT * FROM production_material'
query5 = 'SELECT p.production_id, i.item_name FROM production AS p JOIN item AS i ON p.item_id = i.item_id'

df1 = pd.read_sql(query1, conn)
df2 = pd.read_sql(query2, conn)
df3 = pd.read_sql(query3, conn)
df4 = pd.read_sql(query4, conn)
df5 = pd.read_sql(query5, conn)

st.dataframe(df1)
st.write('### [lot table]')
st.dataframe(df2)
st.write('### [production table]')
st.dataframe(df3)
st.write('### [production_material table]')
st.dataframe(df4)
st.dataframe(df5)
