import streamlit as st

st.header('Proline :arrow_right: GSEA konvertor')
files = st.file_uploader('Nahrajte subor', accept_multiple_files=True)

def print_files():
    for file in files:
        st.write(file.name)


st.button('Execute', on_click=print_files)
