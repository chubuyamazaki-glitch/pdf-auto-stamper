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
            
            # 回転とスケールの行列
            total_rot = (data.get('rot', 0) - p_rot) % 360
            mat = fitz.Matrix(total_rot).prescale(data['scale'], data['scale'])
            
            # 1. 円と線の描画
            page.draw_circle(center, 30 * data['scale'], color=(1, 0, 0), width=1.5)
            page.draw_line(center + fitz.Point(-28, -8) * mat, center + fitz.Point(28, -8) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28,  5) * mat, center + fitz.Point(28,  5) * mat, color=(1, 0, 0), width=1)

            # 2. テキスト設定
            text_rot = (data.get('rot', 0) + p_rot) % 360
            fs = 10 * data['scale']
            name_str = data.get('name', '名前')

            # --- フォントの準備 ---
            font_en = fitz.Font("helv")  # 英数字用
            font_jp = fitz.Font("china-ss") # 漢字用

            # 3. 各行のテキスト幅を計算して中央に配置
            # 理論： 中心点から (文字幅 / 2) だけ左にオフセットさせる
            
            # 【上段】CHUBU
            w1 = font_en.text_length("CHUBU", fontsize=fs)
            p1 = center + fitz.Point(-w1 / 2, -12) * mat
            page.insert_text(p1, "CHUBU", fontsize=fs, color=(1,0,0), rotate=text_rot, fontname="helv")
            
            # 【中段】日付
            w2 = font_en.text_length(self.today, fontsize=fs * 0.8)
            p2 = center + fitz.Point(-w2 / 2, 2) * mat
            page.insert_text(p2, self.today, fontsize=fs * 0.8, color=(1,0,0), rotate=text_rot, fontname="helv")
            
            # 【下段】名前
            w3 = font_jp.text_length(name_str, fontsize=fs)
            p3 = center + fitz.Point(-w3 / 2, 15) * mat
            page.insert_text(p3, name_str, fontsize=fs, color=(1,0,0), rotate=text_rot, fontname="china-ss")

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
