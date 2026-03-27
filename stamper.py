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
            p_rot = page.rotation
            center = fitz.Point(data['x'], data['y'])
            
            S = data['scale']
            user_rot = data.get('rot', 0)
            
            # 内部描画用マトリックス
            # PDFはY軸が上向きなので、それに合わせた回転・拡大を行う
            internal_rot = (user_rot - p_rot) % 360
            mat = fitz.Matrix(internal_rot).prescale(S, S)
            
            # 1. 円(半径30)と区切り線(y=±8)の描画
            # PDF座標系(Y上向き)なので +8が上線、-8が下線
            page.draw_circle(center, 30 * S, color=(1, 0, 0), width=1.5)
            page.draw_line(center + fitz.Point(-28, 8) * mat, center + fitz.Point(28, 8) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28, -8) * mat, center + fitz.Point(28, -8) * mat, color=(1, 0, 0), width=1)

            # 2. テキスト設定
            text_rot = (user_rot + p_rot) % 360
            base_fs = 10
            f_en = fitz.Font("helv")
            f_jp = fitz.Font("china-ss")

            # --- 核心：回転を考慮した中心座標の算出 ---
            def insert_centered_text(text, font_obj, alias, dy, fs_mod=1.0):
                fs = base_fs * fs_mod
                # 文字の幅と視覚的な高さ（中央補正用）
                tw = font_obj.text_length(text, fontsize=fs)
                th = fs * 0.7  # フォントの高さの約70%を実質的な高さとする
                
                # 回転角度（ラジアン）
                rad = math.radians(text_rot)
                cos_a = math.cos(rad)
                sin_a = math.sin(rad)

                # ターゲットとなる「その段の中心点」
                # PDF座標系(Y上向き)に合わせて dy を計算
                target_p = center + fitz.Point(0, dy) * mat
                
                # 【ここが修正のキモ！】
                # rotate=text_rot を指定した insert_text は「左下(baseline)」を軸に回る。
                # その「左下」がどこにあれば、回転後に文字のセンターが target_p に来るかを算出する。
                # PDFのY軸(上向き)を考慮した幾何学補正
                ox = -(tw / 2) * cos_a + (th / 2) * sin_a
                oy = -(tw / 2) * sin_a - (th / 2) * cos_a
                
                final_origin = target_p + fitz.Point(ox, oy)
                
                page.insert_text(
                    final_origin, text, 
                    fontsize=fs * S, color=(1,0,0), 
                    rotate=text_rot, fontname=alias
                )

            # 3. 各段の配置（PDF座標系: 上はプラス、下はマイナス）
            insert_centered_text("CHUBU", f_en, "helv", 19)
            insert_centered_text(self.today, f_en, "helv", 0, fs_mod=0.8)
            insert_centered_text(data.get('name', '名前'), f_jp, "china-ss", -19)

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
