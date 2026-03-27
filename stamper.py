import fitz  # PyMuPDF
import datetime
import math

class PdfStamper:
    def __init__(self, input_path):
        self.doc = fitz.open(input_path) if input_path else None
        self.today = datetime.date.today().strftime("%Y.%m.%d")

    def apply_stamps(self, stamp_list, output_path=None):
        for data in stamp_list:
            p_idx = data['pNum'] - 1
            if p_idx >= len(self.doc): continue
            
            page = self.doc[p_idx]
            # 内部の回転を取得 (0, 90, 180, 270)
            p_rot = page.rotation
            
            # 画面上で指定した中心座標 (x, y)
            center = fitz.Point(data['x'], data['y'])
            r = 30 * data['scale']
            
            # ユーザー指定の回転 (rot)
            user_rot = data.get('rot', 0)
            # 合計の回転角（ページの回転を打ち消す方向に回す）
            total_rot = (user_rot - p_rot) % 360
            
            # --- 描画ロジック (ページの回転を考慮した座標変換) ---
            # ページ座標系を、ハンコの中心を軸に total_rot 度回転させる行列を作成
            # これにより、以降の描画は「真っ直ぐなハンコ」を描くつもりで座標を指定できる
            mat = fitz.Matrix(total_rot).prescale(data['scale'], data['scale'])
            
            # 円と線の描画（赤色）
            # 円を描画
            page.draw_circle(center, r, color=(1, 0, 0), width=1.5)
            
            # 中の2本線を描画 (y軸方向にオフセット)
            l1_y = 8
            l2_y = -5
            
            # 回転行列を使って、棒の両端の座標を計算
            p1_1 = center + fitz.Point(-28, -l1_y) * mat
            p1_2 = center + fitz.Point( 28, -l1_y) * mat
            p2_1 = center + fitz.Point(-28, -l2_y) * mat
            p2_2 = center + fitz.Point( 28, -l2_y) * mat
            
            page.draw_line(p1_1, p1_2, color=(1, 0, 0), width=1)
            page.draw_line(p2_1, p2_2, color=(1, 0, 0), width=1)

            # --- テキスト挿入（回転補正） ---
            # テキストの回転角（ユーザーの指定 + PDF自体の回転）
            text_rot = (user_rot + p_rot) % 360
            
            fs = 10 * data['scale']
            
            # 各テキストの位置を配置（回転行列を使って計算）
            # CHUBU
            t1_p = center + fitz.Point(-15, -12) * mat
            page.insert_text(t1_p, "CHUBU", fontsize=fs, color=(1,0,0), rotate=text_rot)
            
            # 日付
            t2_p = center + fitz.Point(-20, 2) * mat
            page.insert_text(t2_p, self.today, fontsize=fs*0.8, color=(1,0,0), rotate=text_rot)
            
            # 名前
            t3_p = center + fitz.Point(-15, 15) * mat
            page.insert_text(t3_p, data.get('name', '名前'), fontsize=fs, color=(1,0,0), rotate=text_rot)

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
            return output_path
        return self.doc
