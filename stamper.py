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
            total_rot = (data.get('rot', 0) - p_rot) % 360
            
            # 行列：中心(0,0)を基準に回転・拡大
            mat = fitz.Matrix(total_rot).prescale(S, S)
            
            # 1. 外枠（円）の描画
            page.draw_circle(center, 30 * S, color=(1, 0, 0), width=1.5)
            
            # 2. 段棒（横棒）の描画： ±8 で完全に対称化
            # 中段のスペースを 16pt 確保し、ゆったりとした配置に
            line_y = 8
            page.draw_line(center + fitz.Point(-28, -line_y) * mat, center + fitz.Point(28, -line_y) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28,  line_y) * mat, center + fitz.Point(28,  line_y) * mat, color=(1, 0, 0), width=1)

            # 3. テキスト描画 (視覚的センター調整)
            text_rot = (data.get('rot', 0) + p_rot) % 360
            base_fs = 10
            actual_fs = base_fs * S
            name_str = data.get('name', '名前')

            font_en = fitz.Font("helv")
            font_jp = fitz.Font("china-ss")

            # --- 各段のベースライン計算 ---
            
            # 上段: CHUBU (線が-8なので、その上のエリアの中央へ)
            w1 = font_en.text_length("CHUBU", fontsize=base_fs)
            p1 = center + fitz.Point(-w1 / 2, -13) * mat
            page.insert_text(p1, "CHUBU", fontsize=actual_fs, color=(1,0,0), rotate=text_rot, fontname="helv")
            
            # 中段: 日付 (線が -8 ～ 8 なので、ベースラインを 3 に置くことで視覚的に中央へ)
            fs_date = base_fs * 0.8
            w2 = font_en.text_length(self.today, fontsize=fs_date)
            p2 = center + fitz.Point(-w2 / 2, 3) * mat
            page.insert_text(p2, self.today, fontsize=fs_date * S, color=(1,0,0), rotate=text_rot, fontname="helv")
            
            # 下段: 名前 (線が 8 なので、その下のエリアの中央へ)
            w3 = font_jp.text_length(name_str, fontsize=base_fs)
            p3 = center + fitz.Point(-w3 / 2, 20) * mat
            page.insert_text(p3, name_str, fontsize=actual_fs, color=(1,0,0), rotate=text_rot, fontname="china-ss")

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
