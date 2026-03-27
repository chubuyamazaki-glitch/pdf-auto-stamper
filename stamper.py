import fitz  # PyMuPDF
import datetime

class PdfStamper:
    def __init__(self, input_path):
        self.doc = fitz.open(input_path)
        self.today = datetime.date.today().strftime("%Y.%m.%d")

    def apply_stamps(self, stamp_list, output_path="result.pdf"):
        for data in stamp_list:
            p_idx = data['pNum'] - 1
            if p_idx >= len(self.doc): continue
            
            page = self.doc[p_idx]
            # PDF内部の回転を取得し、座標をPDFポイントに変換
            center = fitz.Point(data['x'], data['y'])
            r = 30 * data['scale']
            
            # 円と線の描画（赤色）
            page.draw_circle(center, r, color=(1, 0, 0), width=1.5)
            l1 = 8 * data['scale']
            l2 = -5 * data['scale']
            page.draw_line(fitz.Point(center.x - r + 2, center.y - l1), fitz.Point(center.x + r - 2, center.y - l1), color=(1,0,0), width=1)
            page.draw_line(fitz.Point(center.x - r + 2, center.y - l2), fitz.Point(center.x + r - 2, center.y - l2), color=(1,0,0), width=1)

            # 回転補正付きテキスト
            total_rot = data.get('rot', 0)
            fs = 10 * data['scale']
            page.insert_text(fitz.Point(center.x - 15*data['scale'], center.y - 12*data['scale']), "CHUBU", fontsize=fs, color=(1,0,0), rotate=total_rot)
            page.insert_text(fitz.Point(center.x - 18*data['scale'], center.y + 2*data['scale']), self.today, fontsize=fs*0.8, color=(1,0,0), rotate=total_rot)
            page.insert_text(fitz.Point(center.x - 15*data['scale'], center.y + 15*data['scale']), data.get('name', '名前'), fontsize=fs, color=(1,0,0), rotate=total_rot)

        self.doc.save(output_path)
        self.doc.close()
        return output_path
