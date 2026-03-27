import streamlit as st
import fitz
from stamper import PdfStamper
import io
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDF直感ハンコ押し機 (エラー修正済・完成版)")

st.markdown("<style>.stImage { cursor: crosshair; border: 1px solid #ccc; }</style>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    
    st.sidebar.header("🛠 ハンコの設定")
    doc_temp = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc_temp), value=1)
    
    page = doc_temp[page_num - 1]
    rect = page.rect

    x_key = f"pdf_x_{page_num}"
    y_key = f"pdf_y_{page_num}"
    click_key = f"last_click_{page_num}"

    if x_key not in st.session_state:
        st.session_state[x_key] = rect.width / 2
        st.session_state[y_key] = rect.height / 2
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
            'scale': scale, 
            'rot': rot, 
            'name': name
        }]
        stamper.apply_stamps(stamp_data)
        
        zoom = 1.5
        # display_mat: 内部座標を画面表示座標に変換する行列
        display_mat = page.get_matrix() @ fitz.Matrix(zoom, zoom)
        pix = preview_doc[page_num - 1].get_pixmap(matrix=display_mat)
        img = Image.open(io.BytesIO(pix.tobytes()))

    st.subheader(f"📄 {page_num} ページ目： クリックした場所にハンコが移動するで！")
    
    # 座標取得コンポーネント
    value = streamlit_image_coordinates(img, key=f"coords_fix_final_{page_num}")

    if value and value != st.session_state[click_key]:
        # クリック座標を逆行列で変換
        click_point = fitz.Point(value["x"], value["y"])
        # ~演算子を使って逆行列を適用（ここが修正ポイント！）
        pdf_point = click_point * ~display_mat
        
        st.session_state[x_key] = pdf_point.x
        st.session_state[y_key] = pdf_point.y
        st.session_state[click_key] = value
        st.rerun()

    st.sidebar.markdown("---")
    if st.sidebar.button("🚀 この位置でPDFを確定保存"):
        final_path = "stamped_final.pdf"
        with open("input_temp.pdf", "wb") as f:
            f.write(pdf_bytes)
        
        final_stamper = PdfStamper("input_temp.pdf")
        final_stamper.apply_stamps(stamp_data, final_path)
        
        with open(final_path, "rb") as f:
            st.sidebar.download_button("✅ 完成版をダウンロード", f, file_name="stamped_document.pdf")
    
    doc_temp.close()
