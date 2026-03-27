import fitz
import datetime

class PdfStamper:
    def __init__(self, input_path):
        # input_pathがある時だけ開き、なければNone（後からセット可能）
        self.doc = fitz.open(input_path) if input_path else None
        self.today = datetime.date.today().strftime("%Y.%m.%d")

    def apply_stamps(self, stamp_list, output_path=None):
        if not self.doc:
            return None
            
        for data in stamp_list:
            p_idx = data['pNum'] - 1
            if p_idx >= len(self.doc): continue
            
            page = self.doc[p_idx]
            p_rot = page.rotation
            center = fitz.Point(data['x'], data['y'])
            
            # 描画行列の作成
            total_rot = (data.get('rot', 0) - p_rot) % 360
            mat = fitz.Matrix(total_rot).prescale(data['scale'], data['scale'])
            
            # 円
            page.draw_circle(center, 30 * data['scale'], color=(1, 0, 0), width=1.5)
            
            # 2本線
            p1_1 = center + fitz.Point(-28, -8) * mat
            p1_2 = center + fitz.Point( 28, -8) * mat
            p2_1 = center + fitz.Point(-28,  5) * mat
            p2_2 = center + fitz.Point( 28,  5) * mat
            page.draw_line(p1_1, p1_2, color=(1, 0, 0), width=1)
            page.draw_line(p2_1, p2_2, color=(1, 0, 0), width=1)

            # テキスト (文字の向きは PDFの回転 + 指定の回転)
            text_rot = (data.get('rot', 0) + p_rot) % 360
            fs = 10 * data['scale']
            page.insert_text(center + fitz.Point(-15, -12) * mat, "CHUBU", fontsize=fs, color=(1,0,0), rotate=text_rot)
            page.insert_text(center + fitz.Point(-20,  2) * mat, self.today, fontsize=fs*0.8, color=(1,0,0), rotate=text_rot)
            page.insert_text(center + fitz.Point(-15, 15) * mat, data.get('name', '名前'), fontsize=fs, color=(1,0,0), rotate=text_rot)

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
