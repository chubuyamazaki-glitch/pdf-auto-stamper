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
            # この center が全ての描画の「絶対不動の軸」や！
            center = fitz.Point(data['x'], data['y'])
            
            # スケール（倍率）
            S = data['scale']
            # 回転：(ユーザー指定 - PDF回転)
            total_rot = (data.get('rot', 0) - p_rot) % 360
            
            # 行列：回転させてからスケールさせる（中心は (0,0) として計算）
            mat = fitz.Matrix(total_rot).prescale(S, S)
            
            # --- 1. 円の描画 ---
            # 中心は固定、半径だけをスケール倍する
            page.draw_circle(center, 30 * S, color=(1, 0, 0), width=1.5)
            
            # --- 2. 線の描画 ---
            # 基本の座標（S=1の時の位置）を行列で飛ばす
            page.draw_line(center + fitz.Point(-28, -8) * mat, center + fitz.Point(28, -8) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28,  5) * mat, center + fitz.Point(28,  5) * mat, color=(1, 0, 0), width=1)

            # --- 3. テキストの描画 (中央揃えの再計算) ---
            text_rot = (data.get('rot', 0) + p_rot) % 360
            # 基準となるフォントサイズ
            base_fs = 10
            actual_fs = base_fs * S
            name_str = data.get('name', '名前')

            font_en = fitz.Font("helv")
            font_jp = fitz.Font("china-ss")

            # 【重要】幅の計算は「基準サイズ(10)」で行い、座標を行列で飛ばす！
            # これで二重スケーリングを防ぎ、常に円のセンターを維持する
            
            # 上段: CHUBU (基準 y=-18)
            w1 = font_en.text_length("CHUBU", fontsize=base_fs)
            p1 = center + fitz.Point(-w1 / 2, -18) * mat
            page.insert_text(p1, "CHUBU", fontsize=actual_fs, color=(1,0,0), rotate=text_rot, fontname="helv")
            
            # 中段: 日付 (基準 y=-1.5)
            w2 = font_en.text_length(self.today, fontsize=base_fs * 0.8)
            p2 = center + fitz.Point(-w2 / 2, -1.5) * mat
            page.insert_text(p2, self.today, fontsize=actual_fs * 0.8, color=(1,0,0), rotate=text_rot, fontname="helv")
            
            # 下段: 名前 (基準 y=17)
            w3 = font_jp.text_length(name_str, fontsize=base_fs)
            p3 = center + fitz.Point(-w3 / 2, 17) * mat
            page.insert_text(p3, name_str, fontsize=actual_fs, color=(1,0,0), rotate=text_rot, fontname="china-ss")

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
