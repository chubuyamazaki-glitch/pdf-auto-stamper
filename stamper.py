import fitz
import datetime

class PdfStamper:
    def __init__(self, input_path):
        self.doc = fitz.open(input_path) if input_path else None
        self.today = datetime.date.today().strftime("%Y.%m.%d")

    def apply_stamps(self, stamp_list, output_path=None):
        if not self.doc: return None
            
        for data in stamp_list:
            p_idx = data['pNum'] - 1
            if p_idx >= len(self.doc): continue
            
            page = self.doc[p_idx]
            p_rot = page.rotation
            center = fitz.Point(data['x'], data['y'])
            
            S = data['scale']
            # ユーザー指定の回転
            user_rot = data.get('rot', 0)
            # 内部描画用の行列（物理座標系での回転）
            total_rot_internal = (user_rot - p_rot) % 360
            mat = fitz.Matrix(total_rot_internal).prescale(S, S)
            
            # 1. 円と線の描画
            page.draw_circle(center, 30 * S, color=(1, 0, 0), width=1.5)
            line_y = 8
            page.draw_line(center + fitz.Point(-28, -line_y) * mat, center + fitz.Point(28, -line_y) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28,  line_y) * mat, center + fitz.Point(28,  line_y) * mat, color=(1, 0, 0), width=1)

            # 2. テキスト描画設定
            # 見た目上の回転（PDFの回転フラグを加味）
            text_rot = (user_rot + p_rot) % 360
            base_fs = 10
            font_en = fitz.Font("helv")
            font_jp = fitz.Font("china-ss")

            # --- 核心：回転対応のセンター配置関数 ---
            def insert_centered_text(text, font, rel_y, fs_mod=1.0):
                fs = base_fs * fs_mod
                # 文字の幅と高さを取得（フォント固有のメトリクスを使用）
                tw = font.text_length(text, fontsize=fs)
                # ascent (ベースラインから上) と descent (ベースラインから下) から中央を算出
                th = (font.ascent - font.descent) * fs / 1000 
                
                # 【ここが修正のキモ！】
                # 1. まず、未回転状態での「理想の挿入起点」を計算する
                #    x: 中心から幅の半分戻す / y: 指定位置から文字の高さの半分（視覚的補正）下げる
                origin_rel = fitz.Point(-tw / 2, rel_y + (th / 3))
                
                # 2. その相対座標を行列で回転・拡大させる
                # 3. 最後にハンコの中心（center）に足す
                final_origin = center + origin_rel * mat
                
                page.insert_text(final_origin, text, fontsize=fs * S, 
                                 color=(1,0,0), rotate=text_rot, fontname=font.name)

            # 3. 各段の配置（rel_yは各セクションの中心目安）
            insert_centered_text("CHUBU", font_en, -18)
            insert_centered_text(self.today, font_en, 0, fs_mod=0.8)
            insert_centered_text(data.get('name', '名前'), font_jp, 18)

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
