import streamlit as st
import fitz
from stamper import PdfStamper
import io
from PIL import Image

st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDFハンコプレビュー機 (A3横・回転完全対応)")

uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    # 1. データを読み込む
    pdf_bytes = uploaded_file.read()
    
    # サイドバー設定
    st.sidebar.header("🛠 調整パネル")
    doc_temp = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc_temp), value=1)
    
    # ページ情報を取得して、スライダーの最大値を決める
    page = doc_temp[page_num - 1]
    # 見た目上の幅と高さを取得（回転考慮済み）
    rect = page.rect
    w, h = rect.width, rect.height

    x = st.sidebar.slider("横位置 (x)", 0.0, float(w), float(w/2))
    y = st.sidebar.slider("縦位置 (y)", 0.0, float(h), float(h/2))
    scale = st.sidebar.slider("大きさ倍率", 0.5, 3.0, 1.0)
    rot = st.sidebar.selectbox("ハンコの向き(度)", [0, 90, 180, 270])
    name = st.sidebar.text_input("名前", value="中部")
    doc_temp.close()

    # --- プレビュー生成 (WYSIWYG方式) ---
    # メモリ上でPDFを開き直して、実際に描画してみる
    with fitz.open(stream=pdf_bytes, filetype="pdf") as preview_doc:
        stamper = PdfStamper(None)
        stamper.doc = preview_doc
        stamp_data = [{'pNum': page_num, 'x': x, 'y': y, 'scale': scale, 'rot': rot, 'name': name}]
        
        # 実際にPDFに描き込む（保存はしない）
        stamper.apply_stamps(stamp_data)
        
        # 描き込んだページを画像化
        pix = preview_doc[page_num - 1].get_pixmap(matrix=fitz.Matrix(2, 2)) # 高画質プレビュー
        img = Image.open(io.BytesIO(pix.tobytes()))

    st.subheader(f"📄 プレビュー ({page_num} ページ目)")
    st.image(img, use_container_width=True)

    # 保存処理
    if st.sidebar.button("🚀 この位置でPDFを保存"):
        # 実際のファイルとして書き出し
        with open("input_temp.pdf", "wb") as f:
            f.write(pdf_bytes)
        
        final_stamper = PdfStamper("input_temp.pdf")
        final_stamper.apply_stamps(stamp_data, "stamped_final.pdf")
        
        with open("stamped_final.pdf", "rb") as f:
            st.sidebar.download_button("✅ 完成版をダウンロード", f, file_name="stamped.pdf")
