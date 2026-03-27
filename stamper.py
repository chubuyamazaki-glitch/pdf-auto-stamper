import fitz
import datetime
import math

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
            p_rot = page.rotation # PDFが元々持っている回転
            center = fitz.Point(data['x'], data['y']) # ハンコの中心
            
            S = data['scale']
            user_rot = data.get('rot', 0) # 0, 90, 180, 270
            
            # 1. 内部の描画行列 (物理座標系)
            # PDFの描画は「物理的な紙面」に対して行うため、表示上の回転を差し引く
            internal_rot = (user_rot - p_rot) % 360
            mat = fitz.Matrix(internal_rot).prescale(S, S)
            
            # 円(R=30)と区切り線(Y=±8)の描画
            # PDF座標系は Y軸が上向きなので、+8が上、-8が下
            page.draw_circle(center, 30 * S, color=(1, 0, 0), width=1.5)
            page.draw_line(center + fitz.Point(-28, 8) * mat, center + fitz.Point(28, 8) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28, -8) * mat, center + fitz.Point(28, -8) * mat, color=(1, 0, 0), width=1)

            # 2. テキスト描画設定
            # 見た目上の回転（PDFの回転フラグを加味）
            text_rot = (user_rot + p_rot) % 360
            base_fs = 10
            f_en = fitz.Font("helv")
            f_jp = fitz.Font("china-ss")

            def insert_centered_text(text, font_obj, alias, dy_offset, fs_mod=1.0):
                fs = base_fs * fs_mod
                # 文字の幅と視覚的な高さを取得
                tw = font_obj.text_length(text, fontsize=fs)
                th = fs * 0.7 
                
                # --- 【核心】回転角度ごとの起点(rx, ry)の算出 ---
                # insert_textは「左下(baseline)」を起点に、指定角度回転させる仕様。
                # 文字の中心をターゲットに重ねるための「0度状態での相対起点」を計算する。
                if user_rot == 0:
                    rx, ry = -tw/2, -th/2
                elif user_rot == 90:
                    rx, ry = th/2, -tw/2
                elif user_rot == 180:
                    rx, ry = tw/2, th/2
                elif user_rot == 270:
                    rx, ry = -th/2, tw/2
                else:
                    # 任意角の場合の一般式
                    rad = math.radians(user_rot)
                    rx = -(tw/2)*math.cos(rad) + (th/2)*math.sin(rad)
                    ry = -(tw/2)*math.sin(rad) - (th/2)*math.cos(rad)

                # 物理座標への最終的な挿入ポイント
                # 0度状態の「dy_offset」と「回転補正(rx, ry)」を合算し、行列で一気に回す
                final_origin = center + fitz.Point(rx, dy_offset + ry) * mat
                
                page.insert_text(
                    final_origin, text, 
                    fontsize=fs * S, color=(1,0,0), 
                    rotate=text_rot, fontname=alias
                )

            # 3. 三段の配置 (PDF座標系に合わせて上がプラス)
            insert_centered_text("CHUBU", f_en, "helv", 18)
            insert_centered_text(self.today, f_en, "helv", 0, fs_mod=0.8)
            insert_centered_text(data.get('name', '名前'), f_jp, "china-ss", -18)

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
