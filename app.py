import streamlit as st
import fitz
from stamper import PdfStamper
import io
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

# 画面設定：ワイドモードで使いやすく
st.set_page_config(page_title="PDF職人", layout="wide")
st.title("🎯 PDF直感ハンコ押し機 (座標同期・クリーン版)")

# 十字カーソルのCSS
st.markdown("<style>.stImage { cursor: crosshair; border: 1px solid #ccc; }</style>", unsafe_allow_html=True)

# ファイルアップローダー
uploaded_file = st.file_uploader("PDFをアップロードしてな", type="pdf")

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    
    st.sidebar.header("🛠 ハンコの設定")
    doc_temp = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_num = st.sidebar.number_input("ページ選択", min_value=1, max_value=len(doc_temp), value=1)
    
    # 選択されたページの情報を取得
    page = doc_temp[page_num - 1]
    rect = page.rect  # PDF内部の物理サイズ

    # ページごとに内部座標を保持（セッション管理）
    x_key = f"pdf_x_{page_num}"
    y_key = f"pdf_y_{page_num}"
    click_key = f"last_click_{page_num}"

    if x_key not in st.session_state:
        st.session_state[x_key] = rect.width / 2
        st.session_state[y_key] = rect.height / 2
        st.session_state[click_key] = None

    # 各種パラメータの調整
    scale = st.sidebar.slider("大きさ倍率", 0.5, 3.0, 1.0)
    rot = st.sidebar.selectbox("ハンコの向き(度)", [0, 90, 180, 270])
    name = st.sidebar.text_input("名前", value="中部")

    # --- プレビュー生成 ---
    # メモリ上で一時的にPDFを開いてハンコを描く
    with fitz.open(stream=pdf_bytes, filetype="pdf") as preview_doc:
        stamper = PdfStamper(None)
        stamper.doc = preview_doc
        
        # 描画用データ
        stamp_data = [{
            'pNum': page_num, 
            'x': st.session_state[x_key], 
            'y': st.session_state[y_key], 
            'scale': scale, 
            'rot': rot, 
            'name': name
        }]
        stamper.apply_stamps(stamp_data)
        
        # プレビュー画像の作成（拡大率 zoom を適用）
        zoom = 1.5
        # 「ページの回転」と「画面の拡大」を掛け合わせた行列
        display_mat = page.get_matrix() @ fitz.Matrix(zoom, zoom)
        pix = preview_doc[page_num - 1].get_pixmap(matrix=display_mat)
        img = Image.open(io.BytesIO(pix.tobytes()))

    st.subheader(f"📄 {page_num} ページ目： クリックした場所にハンコが移動するで！")
    
    # 画像を表示してクリックを取得（keyを更新して安定化）
    value = streamlit_image_coordinates(img, key=f"coords_final_v4_{page_num}")

    # クリックされた時の座標変換処理
    if value and value != st.session_state[click_key]:
        # 画面のピクセル座標を逆行列で「PDF内部の真実の座標」に戻す
        click_point = fitz.Point(value["x"], value["y"])
        pdf_point = click_point * display_mat.inverse()
        
        # セッションの座標を更新
        st.session_state[x_key] = pdf_point.x
        st.session_state[y_key] = pdf_point.y
        st.session_state[click_key] = value
        
        # 即座に画面を更新
        st.rerun()

    # --- 保存・ダウンロード処理 ---
    st.sidebar.markdown("---")
    if st.sidebar.button("🚀 この位置でPDFを確定保存"):
        final_path = "stamped_final.pdf"
        
        # 処理用に一時書き出し
        with open("input_temp.pdf", "wb") as f:
            f.write(pdf_bytes)
        
        final_stamper = PdfStamper("input_temp.pdf")
        final_stamper.apply_stamps(stamp_data, final_path)
        
        # ダウンロードボタンの表示
        with open(final_path, "rb") as f:
            st.sidebar.download_button(
                label="✅ 完成版をダウンロード",
                data=f,
                file_name="stamped_document.pdf",
                mime="application/pdf"
            )
    
    doc_temp.close()
