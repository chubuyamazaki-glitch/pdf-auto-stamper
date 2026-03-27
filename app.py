import streamlit as st
import fitz
from stamper import PdfStamper
import io
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDF直感ハンコ押し機 (クリック同期修正版)")

# 十字カーソルのCSS
st.markdown("<style>.stImage { cursor: crosshair; border: 1px solid #ccc; }</style>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    
    st.sidebar.header("🛠 ハンコの設定")
    doc_temp = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc_temp), value=1)
    
    page = doc_temp[page_num - 1]
    
    # 内部の物理座標サイズを取得
    rect = page.rect
    # 表示上のサイズを取得（回転考慮）
    pix_orig = page.get_pixmap()
    view_w, view_h = pix_orig.width, pix_orig.height

    # セッション状態でPDF内部の物理座標を管理
    if f"pdf_x_{page_num}" not in st.session_state:
        st.session_state[f"pdf_x_{page_num}"] = rect.width / 2
        st.session_state[f"pdf_y_{page_num}"] = rect.height / 2
        st.session_state[f"last_click_{page_num}"] = None # 最後のクリックを記憶

    scale = st.sidebar.slider("大きさ倍率", 0.5, 3.0, 1.0)
    rot = st.sidebar.selectbox("ハンコの向き(度)", [0, 90, 180, 270])
    name = st.sidebar.text_input("名前", value="中部")

    # --- プレビュー生成 ---
    with fitz.open(stream=pdf_bytes, filetype="pdf") as preview_doc:
        stamper = PdfStamper(None)
        stamper.doc = preview_doc
        
        # 現在セッションにある座標でハンコを描画
        stamp_data = [{
            'pNum': page_num, 
            'x': st.session_state[f"pdf_x_{page_num}"], 
            'y': st.session_state[f"pdf_y_{page_num}"], 
            'scale': scale, 'rot': rot, 'name': name
        }]
        stamper.apply_stamps(stamp_data)
        
        # プレビュー用画像（Matrixで倍率固定して安定させる）
        pix = preview_doc[page_num - 1].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
        img = Image.open(io.BytesIO(pix.tobytes()))

    st.subheader(f"📄 {page_num} ページ目： 好きな場所をクリックしてな")
    
    # 画像表示＆クリック取得
    # keyを固定することでコンポーネントを安定させる
    value = streamlit_image_coordinates(img, key=f"coords_v3_{page_num}")

    # クリックされた座標が「前回のクリック」と違う場合のみ更新
    if value and value != st.session_state[f"last_click_{page_num}"]:
        # 1. 表示上のポイント座標に換算
        v_x = (value["x"] / img.width) * view_w
        v_y = (value["y"] / img.height) * view_h
        v_point = fitz.Point(v_x, v_y)

        # 2. 内部物理座標に逆変換（ここがひっくり返すキモ！）
        mat_inv = page.get_matrix().inverse()
        pdf_point = v_point * mat_inv
        
        # 3. 座標を更新して、今回のクリックを記憶
        st.session_state[f"pdf_x_{page_num}"] = pdf_point.x
        st.session_state[f"pdf_y_{page_num}"] = pdf_point.y
        st.session_state[f"last_click_{page_num}"] = value
        
        st.rerun()

    # --- 保存処理 ---
    if st.sidebar.button("🚀 この位置でPDFを保存"):
        final_path = "stamped_final.pdf"
        # 一時ファイルを作成
        with open("input_temp.pdf", "wb") as f:
            f.write(pdf_bytes)
        
        final_stamper = PdfStamper("input_temp.pdf")
        final_stamper.apply_stamps(stamp_data, final_path)
        
        with open(final_path, "rb") as f:
            st.sidebar.download_button("✅ ダウンロード", f, file_name="stamped.pdf")
    
    doc_temp.close()
