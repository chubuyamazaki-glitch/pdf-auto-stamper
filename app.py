import streamlit as st
import fitz  # PyMuPDF
from stamper import PdfStamper
from PIL import Image, ImageDraw
import io

st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDFハンコプレビュー機")

# 1. ファイルアップロード
uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    # PDFをメモリに読み込む
    pdf_bytes = uploaded_file.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # サイドバーで操作
    st.sidebar.header("🛠 調整パネル")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc), value=1)
    
    # ページ情報を取得
    page = doc[page_num - 1]
    w, h = page.rect.width, page.rect.height
    
    # 座標・大きさ・回転の調整
    x = st.sidebar.slider("横位置 (x)", 0.0, float(w), float(w/2))
    y = st.sidebar.slider("縦位置 (y)", 0.0, float(h), float(h/2))
    scale = st.sidebar.slider("大きさ倍率", 0.5, 3.0, 1.0)
    rot = st.sidebar.selectbox("回転角", [0, 90, 180, 270])
    name = st.sidebar.text_input("名前", value="中部")

    # --- プレビュー生成 ---
    # ページを画像に変換
    pix = page.get_pixmap()
    img = Image.open(io.BytesIO(pix.tobytes()))
    draw = ImageDraw.Draw(img)
    
    # プレビュー用の赤い円を描画（ハンコの目安）
    r = 30 * scale
    draw.ellipse([x-r, y-r, x+r, y+r], outline="red", width=3)
    # 中心点
    draw.point([x, y], fill="red")

    # メイン画面にプレビューを表示
    st.subheader(f"📄 プレビュー ({page_num} ページ目)")
    st.image(img, use_container_width=True, caption="赤い円がハンコの位置やで")

    # 3. 実行ボタン
    if st.sidebar.button("🚀 この位置でPDFを書き出す"):
        with st.spinner("職人がハンコ押しとるから待ってな..."):
            # 一時ファイルに保存して処理
            with open("input_temp.pdf", "wb") as f:
                f.write(pdf_bytes)
            
            stamper = PdfStamper("input_temp.pdf")
            stamp_list = [{'pNum': page_num, 'x': x, 'y': y, 'scale': scale, 'rot': rot, 'name': name}]
            
            output_path = "stamped_output.pdf"
            stamper.apply_stamps(stamp_list, output_path)
            
            with open(output_path, "rb") as f:
                st.sidebar.download_button(
                    label="✅ 完成版をダウンロード",
                    data=f,
                    file_name="stamped_document.pdf",
                    mime="application/pdf"
                )
