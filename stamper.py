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
            
            # 回転計算
            total_rot = (data.get('rot', 0) - p_rot) % 360
            mat = fitz.Matrix(total_rot).prescale(data['scale'], data['scale'])
            
            # 円と線の描画
            page.draw_circle(center, 30 * data['scale'], color=(1, 0, 0), width=1.5)
            page.draw_line(center + fitz.Point(-28, -8) * mat, center + fitz.Point(28, -8) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28,  5) * mat, center + fitz.Point(28,  5) * mat, color=(1, 0, 0), width=1)

            # --- テキスト描画 (日本語対応) ---
            text_rot = (data.get('rot', 0) + p_rot) % 360
            fs = 10 * data['scale']
            
            # 【重要】fontname="jpn" を指定することで日本語（漢字）に対応させる
            # これでStreamlit Cloud上のLinux環境でも日本語が表示されるようになります
            
            # 上段: 組織名
            page.insert_text(center + fitz.Point(-15, -12) * mat, "CHUBU", 
                             fontsize=fs, color=(1,0,0), rotate=text_rot, fontname="helv")
            
            # 中段: 日付
            page.insert_text(center + fitz.Point(-20,  2) * mat, self.today, 
                             fontsize=fs*0.8, color=(1,0,0), rotate=text_rot, fontname="helv")
            
            # 下段: 名前（ここが漢字なので、フォント指定が必須！）
            page.insert_text(center + fitz.Point(-15, 15) * mat, data.get('name', '名前'), 
                             fontsize=fs, color=(1,0,0), rotate=text_rot, fontname="china-ss") 

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
