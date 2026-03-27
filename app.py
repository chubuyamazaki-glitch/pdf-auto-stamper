import streamlit as st
import fitz
from stamper import PdfStamper
import io
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDF連続ハンコ押し機 (向き修正・1.2倍制限版)")

# 十字カーソル
st.markdown("<style>.stImage { cursor: crosshair; border: 1px solid #ccc; }</style>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    
    st.sidebar.header("🛠 ハンコの設定")
    doc_temp = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc_temp), value=1)
    
    # 0.6デフォルト、最大1.2
    scale = st.sidebar.slider("大きさ倍率", 0.1, 1.2, 0.6, step=0.1)
    rot = st.sidebar.selectbox("ハンコの向き(度)", [0, 90, 180, 270])
    name = st.sidebar.text_input("名前", value="中部")

    # ページごとにハンコを保持
    stamps_key = f"stamps_list_{page_num}"
    if stamps_key not in st.session_state:
        st.session_state[stamps_key] = []
    
    # ボタン類
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("⏮ 戻す"):
            if st.session_state[stamps_key]:
                st.session_state[stamps_key].pop()
                st.rerun()
    with col2:
        if st.button("🗑 クリア"):
            st.session_state[stamps_key] = []
            st.rerun()

    # --- プレビュー生成 ---
    page = doc_temp[page_num - 1]
    with fitz.open(stream=pdf_bytes, filetype="pdf") as preview_doc:
        stamper = PdfStamper(None)
        stamper.doc = preview_doc
        stamper.apply_stamps(st.session_state[stamps_key])
        
        # 【修正！】余計なprerotateを削除。fitzに任せるのが一番。
        zoom = 1.5
        zoom_mat = fitz.Matrix(zoom, zoom)
        pix = preview_doc[page_num - 1].get_pixmap(matrix=zoom_mat)
        img = Image.open(io.BytesIO(pix.tobytes()))

    st.subheader(f"📄 {page_num} ページ目： クリックした場所に配置されるで！")
    
    value = streamlit_image_coordinates(img, key=f"coords_v_final_{page_num}")

    # クリック座標の逆算
    click_key = f"last_click_{page_num}"
    if value and value != st.session_state.get(click_key):
        # 1. 拡大分をキャンセル
        pt = fitz.Point(value["x"], value["y"]) * ~zoom_mat
        # 2. PDFの回転フラグをキャンセルして「物理座標」に戻す
        pdf_point = pt * ~page.rotation_matrix
        
        new_stamp = {
            'pNum': page_num, 'x': pdf_point.x, 'y': pdf_point.y,
            'scale': scale, 'rot': rot, 'name': name
        }
        st.session_state[stamps_key].append(new_stamp)
        st.session_state[click_key] = value
        st.rerun()

    # --- 保存処理 ---
    st.sidebar.markdown("---")
    if st.sidebar.button("🚀 PDFを確定保存"):
        all_stamps = []
        for key in st.session_state.keys():
            if key.startswith("stamps_list_"):
                all_stamps.extend(st.session_state[key])
        
        if all_stamps:
            final_path = "stamped_final.pdf"
            with open("input_temp.pdf", "wb") as f: f.write(pdf_bytes)
            final_stamper = PdfStamper("input_temp.pdf")
            final_stamper.apply_stamps(all_stamps, final_path)
            with open(final_path, "rb") as f:
                st.sidebar.download_button("✅ ダウンロード", f, file_name="stamped.pdf")
    
    doc_temp.close()
