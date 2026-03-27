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
            
            # 内部描画用マトリックス（中心を軸に回転・拡大）
            internal_rot = (user_rot - p_rot) % 360
            mat = fitz.Matrix(internal_rot).prescale(S, S)
            
            # 1. 円(半径30)と区切り線(y=±8)の描画
            page.draw_circle(center, 30 * S, color=(1, 0, 0), width=1.5)
            line_y = 8
            page.draw_line(center + fitz.Point(-28, -line_y) * mat, center + fitz.Point(28, -line_y) * mat, color=(1, 0, 0), width=1)
            page.draw_line(center + fitz.Point(-28,  line_y) * mat, center + fitz.Point(28,  line_y) * mat, color=(1, 0, 0), width=1)

            # 2. テキスト描画（見た目上の回転を加味）
            text_rot = (user_rot + p_rot) % 360
            base_fs = 10
            font_en = fitz.Font("helv")
            font_jp = fitz.Font("china-ss")

            def insert_fixed_text(text, font, target_y, fs_mod=1.0):
                fs = base_fs * fs_mod
                # 文字の幅を取得
                tw = font.text_length(text, fontsize=fs)
                
                # 【ここが修正の核心】
                # 文字の「高さ」を考慮して、ベースラインを垂直方向の中央に補正
                # 一般的なフォントでは ascent の約半分(0.35倍程度)が視覚的な中心
                v_offset = fs * 0.35 
                
                # 0度状態での「中心からの相対座標」を算出
                # x: 半分の幅だけ左へ / y: 各段のセンター位置からベースライン補正分だけ下へ
                rel_origin = fitz.Point(-tw / 2, target_y + v_offset)
                
                # その「点」を行列で回転・拡大させ、ハンコの物理中心に加える
                final_origin = center + rel_origin * mat
                
                page.insert_text(
                    final_origin, 
                    text, 
                    fontsize=fs * S, 
                    color=(1,0,0), 
                    rotate=text_rot, 
                    fontname=font.name
                )

            # 3. 各段の配置（上段、中段、下段）
            # 円の半径30、線が±8なので、各エリアの中央は ±19 付近
            insert_fixed_text("CHUBU", font_en, -19)
            insert_fixed_text(self.today, font_en, 0, fs_mod=0.8)
            insert_fixed_text(data.get('name', '名前'), font_jp, 19)

        if output_path:
            self.doc.save(output_path)
            self.doc.close()
        return self.doc
