import streamlit as st
import fitz
from stamper import PdfStamper
import io
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDF直感ハンコ押し機 (最終安定版)")

st.markdown("<style>.stImage { cursor: crosshair; border: 1px solid #ccc; }</style>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    
    st.sidebar.header("🛠 ハンコの設定")
    doc_temp = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc_temp), value=1)
    
    page = doc_temp[page_num - 1]

    # セッション状態でPDF内部の物理座標を管理
    x_key = f"pdf_x_{page_num}"
    y_key = f"pdf_y_{page_num}"
    click_key = f"last_click_{page_num}"

    if x_key not in st.session_state:
        st.session_state[x_key] = page.rect.width / 2
        st.session_state[y_key] = page.rect.height / 2
        st.session_state[click_key] = None

    scale = st.sidebar.slider("大きさ倍率", 0.5, 3.0, 1.0)
    rot = st.sidebar.selectbox("ハンコの向き(度)", [0, 90, 180, 270])
    name = st.sidebar.text_input("名前", value="中部")

    # --- プレビュー生成 ---
    with fitz.open(stream=pdf_bytes, filetype="pdf") as preview_doc:
        stamper = PdfStamper(None)
        stamper.doc = preview_doc
        
        stamp_data = [{
            'pNum': page_num, 
            'x': st.session_state[x_key], 
            'y': st.session_state[y_key], 
            'scale': scale, 'rot': rot, 'name': name
        }]
        stamper.apply_stamps(stamp_data)
        
        # プレビュー画像生成（拡大率 1.5倍）
        zoom = 1.5
        zoom_mat = fitz.Matrix(zoom, zoom)
        # get_pixmapは自動でPDFの回転フラグを考慮して描画する
        pix = preview_doc[page_num - 1].get_pixmap(matrix=zoom_mat)
        img = Image.open(io.BytesIO(pix.tobytes()))

    st.subheader(f"📄 {page_num} ページ目： クリックしてな！")
    
    # 画像表示。width固定をせず、画像の生サイズでクリックを受け取る
    value = streamlit_image_coordinates(img, key=f"coords_final_stable_{page_num}")

    if value and value != st.session_state[click_key]:
        # 1. まず「拡大分」をキャンセルして「表示上のポイント座標」に戻す
        pt = fitz.Point(value["x"], value["y"]) * ~zoom_mat
        
        # 2. PDFの「回転フラグ」をキャンセルして「内部の物理座標」に変換する
        # rotation_matrixは 物理 -> 表示 への変換。その逆(~)を使えば 表示 -> 物理 に戻る。
        pdf_point = pt * ~page.rotation_matrix
        
        st.session_state[x_key] = pdf_point.x
        st.session_state[y_key] = pdf_point.y
        st.session_state[click_key] = value
        st.rerun()

    if st.sidebar.button("🚀 この位置でPDFを確定保存"):
        final_path = "stamped_final.pdf"
        with open("input_temp.pdf", "wb") as f:
            f.write(pdf_bytes)
        final_stamper = PdfStamper("input_temp.pdf")
        final_stamper.apply_stamps(stamp_data, final_path)
        with open(final_path, "rb") as f:
            st.sidebar.download_button("✅ ダウンロード", f, file_name="stamped.pdf")
    
    doc_temp.close()
