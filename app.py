import streamlit as st
import fitz
from stamper import PdfStamper
import os

st.title("職人のPDFハンコ押し機")

# 1. ファイルアップロード
uploaded_file = st.file_uploader("PDFを選択してな", type="pdf")

if uploaded_file:
    # 一時保存
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success("PDF読み込み完了！")
    
    # 2. 押印設定（簡易版）
    st.sidebar.header("ハンコの設定")
    x = st.sidebar.slider("横位置 (x)", 0, 800, 300)
    y = st.sidebar.slider("縦位置 (y)", 0, 1000, 400)
    scale = st.sidebar.slider("大きさ", 0.5, 2.0, 1.0)
    rot = st.sidebar.selectbox("回転角", [0, 90, 180, 270])

    if st.button("ハンコを押してダウンロード！"):
        stamper = PdfStamper("temp.pdf")
        stamp_list = [{'pNum': 1, 'x': x, 'y': y, 'scale': scale, 'rot': rot}]
        
        output_path = "stamped_result.pdf"
        stamper.apply_stamps(stamp_list, output_path)
        
        with open(output_path, "rb") as f:
            st.download_button("完成したPDFを保存", f, file_name="stamped.pdf")
