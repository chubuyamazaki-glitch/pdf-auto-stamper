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
            
            # ハンコ自体の向き：ユーザー指定分 - ページの回転分（これで打ち消し）
            # ですが、描画自体は「物理座標」に対して行うので、
            # 物理座標から見た「見た目上の真っ直ぐ」を計算します。
            total_rot = (data.get('rot', 0) - p_rot) % 360
            mat = fitz.Matrix(total_rot).prescale(data['scale'], data['scale'])
            
            # 円
            page.draw_circle(center, 30 * data['scale'], color=(1, 0, 0), width=1.5)
            
            # 2本線
            page.draw_line(center + fitz.Point(-28, -8) * mat, center + fitz.Point(28, -8) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28,  5) * mat, center + fitz.Point(28,  5) * mat, color=(1, 0, 0), width=1)

            # テキスト（向きは見た目上の真っ直ぐに、ページ回転を足す）
            text_rot = (data.get('rot', 0) + p_rot) % 360
            fs = 10 * data['scale']
            page.insert_text(center + fitz.Point(-15, -12) * mat, "CHUBU", fontsize=fs, color=(1,0,0), rotate=text_rot)
            page.insert_text(center + fitz.Point(-20,  2) * mat, self.today, fontsize=fs*0.8, color=(1,0,0), rotate=text_rot)
            page.insert_text(center + fitz.Point(-15, 15) * mat, data.get('name', '名前'), fontsize=fs, color=(1,0,0), rotate=text_rot)

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
