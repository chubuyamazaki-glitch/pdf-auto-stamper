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
            
            S = data['scale']
            user_rot = data.get('rot', 0)
            
            # 内部描画用行列（中心を軸に回転・拡大）
            internal_rot = (user_rot - p_rot) % 360
            mat = fitz.Matrix(internal_rot).prescale(S, S)
            
            # 1. 円(半径30)と区切り線(y=±8)の描画
            page.draw_circle(center, 30 * S, color=(1, 0, 0), width=1.5)
            line_y = 8
            page.draw_line(center + fitz.Point(-28, -line_y) * mat, center + fitz.Point(28, -line_y) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28,  line_y) * mat, center + fitz.Point(28,  line_y) * mat, color=(1, 0, 0), width=1)

            # 2. テキスト設定
            text_rot = (user_rot + p_rot) % 360
            base_fs = 10
            
            # フォントオブジェクト（幅計算用）
            f_en = fitz.Font("helv")
            f_jp = fitz.Font("china-ss")

            # --- 垂直センター補正付き挿入関数 ---
            def insert_fixed_text(text, font_obj, alias_name, target_y, fs_mod=1.0):
                fs = base_fs * fs_mod
                # 文字幅を取得
                tw = font_obj.text_length(text, fontsize=fs)
                
                # ベースライン補正（文字の高さの約35%分、下にずらすと視覚的に中央に来る）
                v_offset = fs * 0.35 
                
                # 未回転状態での「中心からの相対座標」
                rel_origin = fitz.Point(-tw / 2, target_y + v_offset)
                
                # 物理座標への変換
                final_origin = center + rel_origin * mat
                
                # 実際の描画。fontnameにはエイリアス名を直接渡す（これでエラー回避！）
                page.insert_text(
                    final_origin, 
                    text, 
                    fontsize=fs * S, 
                    color=(1,0,0), 
                    rotate=text_rot, 
                    fontname=alias_name
                )

            # 3. 各段の配置（上段、中段、下段）
            insert_fixed_text("CHUBU", f_en, "helv", -19)
            insert_fixed_text(self.today, f_en, "helv", 0, fs_mod=0.8)
            insert_fixed_text(data.get('name', '名前'), f_jp, "china-ss", 19)

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
