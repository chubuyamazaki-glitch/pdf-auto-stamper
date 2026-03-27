import streamlit as st
import fitz
from stamper import PdfStamper
import io
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDF直感ハンコ押し機 (クリックで位置決め)")

# CSSでプレビューを見やすく調整
st.markdown("""
    <style>
    .stImage { cursor: crosshair; border: 2px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    
    st.sidebar.header("🛠 ハンコの設定")
    doc_temp = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc_temp), value=1)
    
    # ページ情報の取得
    page = doc_temp[page_num - 1]
    rect = page.rect
    pdf_w, pdf_h = rect.width, rect.height

    # セッション状態で座標を管理（クリックで更新するため）
    if "stamp_x" not in st.session_state: st.session_state.stamp_x = pdf_w / 2
    if "stamp_y" not in st.session_state: st.session_state.stamp_y = pdf_h / 2

    scale = st.sidebar.slider("大きさ倍率", 0.5, 3.0, 1.0)
    rot = st.sidebar.selectbox("ハンコの向き(度)", [0, 90, 180, 270])
    name = st.sidebar.text_input("名前", value="中部")
    doc_temp.close()

    # --- プレビュー生成 ---
    with fitz.open(stream=pdf_bytes, filetype="pdf") as preview_doc:
        stamper = PdfStamper(None)
        stamper.doc = preview_doc
        stamp_data = [{'pNum': page_num, 'x': st.session_state.stamp_x, 'y': st.session_state.stamp_y, 'scale': scale, 'rot': rot, 'name': name}]
        stamper.apply_stamps(stamp_data)
        
        # プレビュー画像生成（解像度調整）
        pix = preview_doc[page_num - 1].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img = Image.open(io.BytesIO(pix.tobytes()))

    st.subheader(f"📄 プレビュー ({page_num} ページ目) - 好きな場所をクリックしてな！")
    
    # 画像を表示し、クリック座標を取得
    # use_column_width=Trueだと座標変換が難しくなるため、元画像の幅で表示
    value = streamlit_image_coordinates(img, key="coords")

    # クリックされたら、そのピクセル座標をPDFポイント座標に変換して保存
    if value:
        # 画像表示時のサイズとピクセル座標の比率からPDF座標を算出
        # streamlit-image-coordinatesは表示サイズでの座標を返してくれる
        st.session_state.stamp_x = (value["x"] / img.width) * pdf_w
        st.session_state.stamp_y = (value["y"] / img.height) * pdf_h
        st.rerun() # 再描画してハンコを移動させる

    # 保存処理
    if st.sidebar.button("🚀 この位置でPDFを保存"):
        with open("input_temp.pdf", "wb") as f:
            f.write(pdf_bytes)
        
        final_stamper = PdfStamper("input_temp.pdf")
        final_stamper.apply_stamps(stamp_data, "stamped_final.pdf")
        
        with open("stamped_final.pdf", "rb") as f:
            st.sidebar.download_button("✅ 完成版をダウンロード", f, file_name="stamped.pdf")
