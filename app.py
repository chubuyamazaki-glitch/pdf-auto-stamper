import streamlit as st
import fitz
from stamper import PdfStamper
import io
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDF直感ハンコ押し機 (回転・座標完全補正版)")

# クリック時の十字カーソル
st.markdown("<style>.stImage { cursor: crosshair; border: 1px solid #ccc; }</style>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    
    st.sidebar.header("🛠 ハンコの設定")
    doc_temp = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc_temp), value=1)
    
    page = doc_temp[page_num - 1]
    
    # 見た目上のサイズ（w, h）を取得（回転考慮済み）
    pix_orig = page.get_pixmap()
    view_w, view_h = pix_orig.width, pix_orig.height

    # セッション状態でPDF内部の物理座標を管理
    if f"pdf_x_{page_num}" not in st.session_state:
        # 初期位置は中央（物理座標のサイズから算出する必要があるが、とりあえず表示サイズから）
        rect = page.rect
        st.session_state[f"pdf_x_{page_num}"] = rect.width / 2
        st.session_state[f"pdf_y_{page_num}"] = rect.height / 2

    scale = st.sidebar.slider("大きさ倍率", 0.5, 3.0, 1.0)
    rot = st.sidebar.selectbox("ハンコの向き(度)", [0, 90, 180, 270])
    name = st.sidebar.text_input("名前", value="中部")

    # --- プレビュー生成 ---
    with fitz.open(stream=pdf_bytes, filetype="pdf") as preview_doc:
        stamper = PdfStamper(None)
        stamper.doc = preview_doc
        
        # セッションに保存されている内部物理座標で試し押し
        stamp_data = [{
            'pNum': page_num, 
            'x': st.session_state[f"pdf_x_{page_num}"], 
            'y': st.session_state[f"pdf_y_{page_num}"], 
            'scale': scale, 'rot': rot, 'name': name
        }]
        stamper.apply_stamps(stamp_data)
        
        # 画面表示用に画像化（Matrix(2, 2)で少し高画質に）
        zoom = 1.5
        mat = fitz.Matrix(zoom, zoom)
        pix = preview_doc[page_num - 1].get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes()))

    st.subheader(f"📄 {page_num} ページ目： 欲しい場所を【クリック】してな！")
    
    # 画像を表示してクリック座標を取得
    value = streamlit_image_coordinates(img, key=f"coords_{page_num}")

    if value:
        # --- 【ここが修正のキモ！】 ---
        # 1. 画面上のピクセル座標を表示上のポイント座標に換算 (比率計算)
        v_x = (value["x"] / img.width) * view_w # 表示上のX座標
        v_y = (value["y"] / img.height) * view_h # 表示上のY座標
        v_point = fitz.Point(v_x, v_y)

        # 2. 表示上のポイント座標を、PDF内部物理座標に逆算して戻す (逆行列を使用)
        # fitzのpage.get_matrix()は「内部座標 -> 表示座標」の行列を返す。
        # その逆行列（inverse()）を使えば、表示座標から内部物理座標を求められる。
        mat_inv = page.get_matrix().inverse()
        pdf_point = v_point * mat_inv # これで内部物理座標が求まる！
        
        # 3. 座標を更新して再描画
        st.session_state[f"pdf_x_{page_num}"] = pdf_point.x
        st.session_state[f"pdf_y_{page_num}"] = pdf_point.y
        st.rerun()

    # --- 書き出し処理 ---
    if st.sidebar.button("🚀 この位置でPDFを保存"):
        with open("input_temp.pdf", "wb") as f:
            f.write(pdf_bytes)
        
        final_stamper = PdfStamper("input_temp.pdf")
        final_stamper.apply_stamps(stamp_data, "stamped_final.pdf")
        
        with open("stamped_final.pdf", "rb") as f:
            st.sidebar.download_button("✅ 完成版をダウンロード", f, file_name="stamped.pdf")
    
    doc_temp.close()
