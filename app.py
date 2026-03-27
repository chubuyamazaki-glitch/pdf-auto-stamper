import streamlit as st
import fitz
from stamper import PdfStamper
import io
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDF連続ハンコ押し機 (実用レンジ 1.2倍まで)")

# 十字カーソル設定
st.markdown("<style>.stImage { cursor: crosshair; border: 1px solid #ccc; }</style>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    
    st.sidebar.header("🛠 現在のハンコ設定")
    doc_temp = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc_temp), value=1)
    
    # 【修正】最大値を 1.2倍 に制限。これで 0.6付近の微調整がやりやすくなるで。
    scale = st.sidebar.slider("大きさ倍率", 0.1, 1.2, 0.6, step=0.1)
    rot = st.sidebar.selectbox("ハンコの向き(度)", [0, 90, 180, 270])
    name = st.sidebar.text_input("名前", value="中部")

    # ページごとにハンコのリストを管理
    stamps_key = f"stamps_list_{page_num}"
    if stamps_key not in st.session_state:
        st.session_state[stamps_key] = []
    
    # 操作ボタン
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
        
        # 保存されている全てのハンコを描画
        stamper.apply_stamps(st.session_state[stamps_key])
        
        zoom = 1.5
        display_mat = fitz.Matrix(zoom, zoom).prerotate(page.rotation)
        pix = preview_doc[page_num - 1].get_pixmap(matrix=display_mat)
        img = Image.open(io.BytesIO(pix.tobytes()))

    st.subheader(f"📄 {page_num} ページ目： クリックでハンコを配置！")
    
    value = streamlit_image_coordinates(img, key=f"coords_v6_{page_num}")

    # クリック判定
    click_key = f"last_click_{page_num}"
    if value and value != st.session_state.get(click_key):
        click_point = fitz.Point(value["x"], value["y"])
        pdf_point = click_point * ~display_mat
        
        new_stamp = {
            'pNum': page_num,
            'x': pdf_point.x,
            'y': pdf_point.y,
            'scale': scale,
            'rot': rot,
            'name': name
        }
        st.session_state[stamps_key].append(new_stamp)
        st.session_state[click_key] = value
        st.rerun()

    # --- 保存処理 ---
    st.sidebar.markdown("---")
    if st.sidebar.button("🚀 PDFを確定保存してダウンロード"):
        all_stamps = []
        for key in st.session_state.keys():
            if key.startswith("stamps_list_"):
                all_stamps.extend(st.session_state[key])
        
        if all_stamps:
            final_path = "stamped_final.pdf"
            with open("input_temp.pdf", "wb") as f:
                f.write(pdf_bytes)
            
            final_stamper = PdfStamper("input_temp.pdf")
            final_stamper.apply_stamps(all_stamps, final_path)
            
            with open(final_path, "rb") as f:
                st.sidebar.download_button("✅ ダウンロード開始", f, file_name="stamped_complete.pdf")
    
    doc_temp.close()
