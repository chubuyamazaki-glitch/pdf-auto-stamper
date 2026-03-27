import fitz  # PyMuPDF
import datetime

class PdfStamper:
    def __init__(self, input_path):
        self.doc = fitz.open(input_path)
        self.today = datetime.date.today().strftime("%Y.%m.%d")

    def apply_stamps(self, stamp_list, output_path=None):
        for data in stamp_list:
            p_idx = data['pNum'] - 1
            if p_idx >= len(self.doc): continue
            
            page = self.doc[p_idx]
            # 内部の回転(0, 90, 180, 270)を取得
            p_rot = page.rotation
            
            center = fitz.Point(data['x'], data['y'])
            r = 30 * data['scale']
            
            # --- 描画ロジック ---
            # 1. 外枠（円）
            page.draw_circle(center, r, color=(1, 0, 0), width=1.5)
            
            # 2. 中の線
            # ページの回転角に合わせて線の向きも変える必要があるが、
            # fitzのdraw_lineはページ座標系に従うので、相対位置を計算
            l1 = 8 * data['scale']
            l2 = -5 * data['scale']
            page.draw_line(fitz.Point(center.x - r + 2, center.y - l1), fitz.Point(center.x + r - 2, center.y - l1), color=(1,0,0), width=1)
            page.draw_line(fitz.Point(center.x - r + 2, center.y - l2), fitz.Point(center.x + r - 2, center.y - l2), color=(1,0,0), width=1)

            # 3. テキスト (ユーザー指定の回転 + PDF自体の回転)
            # 90度回転してるA3横なら、+90度してやることで見た目上の「上」を向く
            total_rot = (data.get('rot', 0) + p_rot) % 360
            fs = 10 * data['scale']
            
            # insert_textは、指定座標が「回転後の座標」として扱われるため補正が重要
            page.insert_text(fitz.Point(center.x - 15*data['scale'], center.y - 12*data['scale']), "CHUBU", fontsize=fs, color=(1,0,0), rotate=total_rot)
            page.insert_text(fitz.Point(center.x - 18*data['scale'], center.y + 2*data['scale']), self.today, fontsize=fs*0.8, color=(1,0,0), rotate=total_rot)
            page.insert_text(fitz.Point(center.x - 15*data['scale'], center.y + 15*data['scale']), data.get('name', '名前'), fontsize=fs, color=(1,0,0), rotate=total_rot)

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
            return output_path
        return self.doc
