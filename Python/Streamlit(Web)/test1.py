import streamlit as st

st.title("스마트팩토리")

st.header("MES")

st.subheader("생산관리")

st.write("MES는 Manufacturing Execution System입니다.")

st.caption("Version 1.0")

st.markdown("""
# Python

## Streamlit

- AI
- Dashboard
- MES

**Python Web**
""")

code = '''
for i in range(10):
    print(i)
'''

st.code(code, language="python")

sql = '''
SELECT *
FROM employee
WHERE dept='AI';
'''

st.code(sql, language="sql")

