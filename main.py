import tkinter as tk
from dataclasses import dataclass
from typing import Optional


# ============================================================
# 기본 설정
# ============================================================

GAME_TITLE = "텍스트 파밍 시뮬레이터"

GRID_SIZE = 9
CELL_SIZE = 72

FIELD_MARGIN = 25
PANEL_WIDTH = 500

FIELD_PIXEL_SIZE = GRID_SIZE * CELL_SIZE

DESIRED_WINDOW_WIDTH = (
    FIELD_MARGIN
    + FIELD_PIXEL_SIZE
    + PANEL_WIDTH
)

DESIRED_WINDOW_HEIGHT = 860


# ============================================================
# 작물 데이터
# ============================================================

@dataclass(frozen=True)
class CropData:
    name: str
    symbol: str
    grow_days: int
    water_interval: int


CROPS = {
    "wheat": CropData(
        name="밀",
        symbol="w",
        grow_days=4,
        water_interval=1,
    ),

    "carrot": CropData(
        name="당근",
        symbol="c",
        grow_days=5,
        water_interval=2,
    ),

    "potato": CropData(
        name="감자",
        symbol="o",
        grow_days=6,
        water_interval=3,
    ),
}

CROP_KEYS = list(CROPS.keys())


# ============================================================
# 밭 한 칸
# ============================================================

class Tile:

    def __init__(self):
        self.plowed = False

        self.crop_type: Optional[str] = None

        self.planted_day = 0
        self.age = 0

        self.last_watered_day: Optional[int] = None

    def has_crop(self):
        return self.crop_type is not None

    def crop_data(self):

        if self.crop_type is None:
            return None

        return CROPS[self.crop_type]

    def is_mature(self):

        if not self.has_crop():
            return False

        crop = self.crop_data()

        return self.age >= crop.grow_days

    def needs_water(self, current_day):

        if not self.has_crop():
            return False

        if self.is_mature():
            return False

        crop = self.crop_data()

        if self.last_watered_day is None:
            return True

        return (
            current_day - self.last_watered_day
            >= crop.water_interval
        )

    def watered_today(self, current_day):

        return self.last_watered_day == current_day

    def can_grow_today(self, current_day):

        if not self.has_crop():
            return False

        if self.is_mature():
            return False

        if self.last_watered_day is None:
            return False

        crop = self.crop_data()

        return (
            current_day - self.last_watered_day
            < crop.water_interval
        )


# ============================================================
# 게임
# ============================================================

class FarmGame:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title(GAME_TITLE)

        # ----------------------------------------------------
        # 화면 크기에 맞춰 창 크기 결정
        # ----------------------------------------------------

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        self.window_width = min(
            DESIRED_WINDOW_WIDTH,
            screen_width - 60
        )

        self.window_height = min(
            DESIRED_WINDOW_HEIGHT,
            screen_height - 100
        )

        # 너무 작아지는 것은 방지
        self.window_width = max(
            self.window_width,
            1050
        )

        self.window_height = max(
            self.window_height,
            760
        )

        # 화면 중앙 배치
        pos_x = max(
            0,
            (screen_width - self.window_width) // 2
        )

        pos_y = max(
            0,
            (screen_height - self.window_height) // 2
        )

        self.root.geometry(
            f"{self.window_width}x{self.window_height}"
            f"+{pos_x}+{pos_y}"
        )

        # 사용자가 직접 확대 가능
        self.root.resizable(True, True)

        self.root.minsize(
            1050,
            760
        )

        self.root.configure(
            bg="#181818"
        )

        # ----------------------------------------------------
        # 게임 상태
        # ----------------------------------------------------

        self.day = 1

        self.player_x = GRID_SIZE // 2
        self.player_y = GRID_SIZE // 2

        self.selected_action = 0
        self.selected_crop_index = 0

        self.actions = [
            "쟁기질",
            "씨 뿌리기",
            "물주기",
            "수확",
        ]

        self.message = "농장에 도착했다."

        # ----------------------------------------------------
        # 통계
        # ----------------------------------------------------

        self.harvest_count = {
            key: 0
            for key in CROPS
        }

        # ----------------------------------------------------
        # 밭
        # ----------------------------------------------------

        self.field = [
            [
                Tile()
                for _ in range(GRID_SIZE)
            ]
            for _ in range(GRID_SIZE)
        ]

        # ----------------------------------------------------
        # 캔버스
        # ----------------------------------------------------

        self.canvas = tk.Canvas(
            self.root,
            bg="#181818",
            highlightthickness=0,
        )

        self.canvas.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # 키 입력
        # ----------------------------------------------------

        self.root.bind(
            "<KeyPress>",
            self.on_key
        )

        self.root.bind(
            "<Configure>",
            self.on_resize
        )

        self.canvas.focus_set()

        self.draw()

    # ========================================================
    # 실행
    # ========================================================

    def run(self):

        self.root.mainloop()

    # ========================================================
    # 창 크기 변경
    # ========================================================

    def on_resize(self, event):

        if event.widget == self.root:
            self.window_width = event.width
            self.window_height = event.height
            self.draw()

    # ========================================================
    # 입력
    # ========================================================

    def on_key(self, event):

        char = event.char.lower()
        key = event.keysym.lower()

        # ----------------------------------------------------
        # 이동
        # WASD + 방향키
        # ----------------------------------------------------

        if char == "w" or key == "up":
            self.move(0, -1)

        elif char == "s" or key == "down":
            self.move(0, 1)

        elif char == "a" or key == "left":
            self.move(-1, 0)

        elif char == "d" or key == "right":
            self.move(1, 0)

        # ----------------------------------------------------
        # 작업 선택
        # ----------------------------------------------------

        elif char == "1":
            self.selected_action = 0
            self.message = "쟁기질을 선택했다."

        elif char == "2":
            self.selected_action = 1
            self.message = "씨 뿌리기를 선택했다."

        elif char == "3":
            self.selected_action = 2
            self.message = "물주기를 선택했다."

        elif char == "4":
            self.selected_action = 3
            self.message = "수확을 선택했다."

        # ----------------------------------------------------
        # 씨앗 변경
        # ----------------------------------------------------

        elif char == "q":
            self.change_crop(-1)

        elif char == "e":
            self.change_crop(1)

        # ----------------------------------------------------
        # 상호작용
        # ----------------------------------------------------

        elif (
            char == "z"
            or key == "return"
            or key == "space"
        ):
            self.interact()

        # ----------------------------------------------------
        # 다음 날
        # ----------------------------------------------------

        elif char == "n":
            self.next_day()

        # ----------------------------------------------------
        # 종료
        # ----------------------------------------------------

        elif key == "escape":

            self.root.destroy()
            return

        self.draw()

    # ========================================================
    # 이동
    # ========================================================

    def move(self, dx, dy):

        new_x = self.player_x + dx
        new_y = self.player_y + dy

        if (
            0 <= new_x < GRID_SIZE
            and 0 <= new_y < GRID_SIZE
        ):
            self.player_x = new_x
            self.player_y = new_y

    # ========================================================
    # 씨앗 선택
    # ========================================================

    def change_crop(self, direction):

        self.selected_crop_index += direction

        self.selected_crop_index %= len(CROP_KEYS)

        crop_key = CROP_KEYS[
            self.selected_crop_index
        ]

        crop = CROPS[crop_key]

        self.message = (
            f"씨앗 선택: {crop.name}"
        )

    # ========================================================
    # 현재 칸
    # ========================================================

    def current_tile(self):

        return self.field[
            self.player_y
        ][
            self.player_x
        ]

    # ========================================================
    # 상호작용
    # ========================================================

    def interact(self):

        if self.selected_action == 0:
            self.plow()

        elif self.selected_action == 1:
            self.plant()

        elif self.selected_action == 2:
            self.water()

        elif self.selected_action == 3:
            self.harvest()

    # ========================================================
    # 쟁기질
    # ========================================================

    def plow(self):

        tile = self.current_tile()

        if tile.has_crop():

            self.message = (
                "작물이 자라고 있어서 "
                "쟁기질할 수 없다."
            )

            return

        if tile.plowed:

            self.message = (
                "이미 쟁기질된 땅이다."
            )

            return

        tile.plowed = True

        self.message = (
            "땅을 갈았다."
        )

    # ========================================================
    # 씨 뿌리기
    # ========================================================

    def plant(self):

        tile = self.current_tile()

        if tile.has_crop():

            self.message = (
                "이미 작물이 심어져 있다."
            )

            return

        if not tile.plowed:

            self.message = (
                "먼저 땅을 갈아야 한다."
            )

            return

        crop_key = CROP_KEYS[
            self.selected_crop_index
        ]

        crop = CROPS[crop_key]

        tile.crop_type = crop_key
        tile.planted_day = self.day
        tile.age = 0
        tile.last_watered_day = None

        self.message = (
            f"{crop.name} 씨앗을 심었다.\n"
            f"물 주기: {crop.water_interval}일마다"
        )

    # ========================================================
    # 물주기
    # ========================================================

    def water(self):

        tile = self.current_tile()

        if not tile.has_crop():

            self.message = (
                "여기에는 작물이 없다."
            )

            return

        crop = tile.crop_data()

        if tile.is_mature():

            self.message = (
                f"{crop.name}은 이미 다 자랐다."
            )

            return

        if tile.watered_today(self.day):

            self.message = (
                "오늘은 이미 물을 주었다."
            )

            return

        if not tile.needs_water(self.day):

            remaining = (
                crop.water_interval
                - (
                    self.day
                    - tile.last_watered_day
                )
            )

            self.message = (
                f"{crop.name}은 아직 물이 충분하다.\n"
                f"{remaining}일 후 다시 물을 주면 된다."
            )

            return

        tile.last_watered_day = self.day

        self.message = (
            f"{crop.name}에 물을 주었다."
        )

    # ========================================================
    # 수확
    # ========================================================

    def harvest(self):

        tile = self.current_tile()

        if not tile.has_crop():

            self.message = (
                "수확할 작물이 없다."
            )

            return

        crop = tile.crop_data()

        if not tile.is_mature():

            self.message = (
                f"{crop.name}은 아직 자라고 있다.\n"
                f"성장 단계: {tile.age}/{crop.grow_days}"
            )

            return

        crop_key = tile.crop_type

        self.harvest_count[crop_key] += 1

        tile.crop_type = None
        tile.age = 0
        tile.last_watered_day = None
        tile.planted_day = 0

        # 수확 후 갈아놓은 땅은 유지
        tile.plowed = True

        self.message = (
            f"{crop.name}을 수확했다!"
        )

    # ========================================================
    # 다음 날
    # ========================================================

    def next_day(self):

        for row in self.field:

            for tile in row:

                if tile.can_grow_today(self.day):

                    tile.age += 1

                    crop = tile.crop_data()

                    if tile.age > crop.grow_days:
                        tile.age = crop.grow_days

        self.day += 1

        self.message = (
            f"{self.day}일째 아침이 되었다."
        )

    # ========================================================
    # 화면 출력
    # ========================================================

    def draw(self):

        if not self.canvas.winfo_exists():
            return

        self.canvas.delete("all")

        self.draw_field()
        self.draw_panel()

    # ========================================================
    # 밭 출력
    # ========================================================

    def draw_field(self):

        offset_x = FIELD_MARGIN
        offset_y = FIELD_MARGIN

        for y in range(GRID_SIZE):

            for x in range(GRID_SIZE):

                tile = self.field[y][x]

                px = offset_x + x * CELL_SIZE
                py = offset_y + y * CELL_SIZE

                # ------------------------------------------------
                # 배경
                # ------------------------------------------------

                bg = "#3a2b22"

                if tile.plowed:
                    bg = "#62452f"

                if tile.has_crop():
                    bg = "#44552e"

                if tile.watered_today(self.day):
                    bg = "#355667"

                # ------------------------------------------------
                # 칸
                # ------------------------------------------------

                self.canvas.create_rectangle(
                    px,
                    py,
                    px + CELL_SIZE,
                    py + CELL_SIZE,
                    fill=bg,
                    outline="#888888",
                    width=2,
                )

                # ------------------------------------------------
                # 문자
                # ------------------------------------------------

                symbol = "."

                if tile.plowed:
                    symbol = ":"

                if tile.has_crop():

                    crop = tile.crop_data()

                    symbol = crop.symbol

                    if tile.is_mature():
                        symbol = symbol.upper()

                if (
                    x == self.player_x
                    and y == self.player_y
                ):
                    symbol = "P"

                self.canvas.create_text(
                    px + CELL_SIZE // 2,
                    py + CELL_SIZE // 2,
                    text=symbol,
                    fill="#ffffff",
                    font=(
                        "Consolas",
                        31,
                        "bold",
                    ),
                )

    # ========================================================
    # 오른쪽 정보 패널
    # ========================================================

    def draw_panel(self):

        panel_x = (
            FIELD_MARGIN
            + FIELD_PIXEL_SIZE
            + 40
        )

        panel_right = self.window_width - 25

        y = 25

        # ----------------------------------------------------
        # 제목
        # ----------------------------------------------------

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=GAME_TITLE,
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                23,
                "bold",
            ),
        )

        y += 52

        # ----------------------------------------------------
        # 날짜
        # ----------------------------------------------------

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=f"{self.day}일째",
            fill="#f1d58a",
            font=(
                "Malgun Gothic",
                19,
                "bold",
            ),
        )

        y += 42

        # ----------------------------------------------------
        # 현재 작업
        # ----------------------------------------------------

        action = self.actions[
            self.selected_action
        ]

        crop_key = CROP_KEYS[
            self.selected_crop_index
        ]

        crop = CROPS[crop_key]

        info = (
            f"[현재 작업]\n"
            f"{self.selected_action + 1}. {action}\n\n"
            f"[선택 씨앗]\n"
            f"{crop.name}\n"
            f"성장: {crop.grow_days}일\n"
            f"물: {crop.water_interval}일마다"
        )

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=info,
            fill="#dddddd",
            font=(
                "Malgun Gothic",
                14,
            ),
        )

        y += 160

        # ----------------------------------------------------
        # 현재 칸
        # ----------------------------------------------------

        tile = self.current_tile()

        tile_text = self.get_tile_info(tile)

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=tile_text,
            fill="#a9d6ff",
            font=(
                "Malgun Gothic",
                13,
            ),
        )

        y += 112

        # ----------------------------------------------------
        # 메시지
        # ----------------------------------------------------

        self.canvas.create_rectangle(
            panel_x - 8,
            y - 8,
            panel_right,
            y + 76,
            fill="#252525",
            outline="#666666",
            width=2,
        )

        self.canvas.create_text(
            panel_x + 5,
            y + 5,
            anchor="nw",
            text=self.message,
            width=max(
                250,
                panel_right - panel_x - 20
            ),
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                12,
            ),
        )

        y += 98

        # ----------------------------------------------------
        # 수확량
        # ----------------------------------------------------

        harvest_text = (
            "[수확량]\n"
            f"밀   {self.harvest_count['wheat']}\n"
            f"당근 {self.harvest_count['carrot']}\n"
            f"감자 {self.harvest_count['potato']}"
        )

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=harvest_text,
            fill="#d3d3d3",
            font=(
                "Malgun Gothic",
                12,
            ),
        )

        y += 100

        # ----------------------------------------------------
        # 조작법
        # ----------------------------------------------------

        controls = (
            "[조작]\n"
            "WASD / 방향키      이동\n"
            "1                  쟁기질\n"
            "2                  씨 뿌리기\n"
            "3                  물주기\n"
            "4                  수확\n"
            "Q / E              씨앗 선택\n"
            "Z / SPACE / ENTER  실행\n"
            "N                  다음 날\n"
            "ESC                종료"
        )

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=controls,
            fill="#bbbbbb",
            font=(
                "Malgun Gothic",
                11,
            ),
        )

    # ========================================================
    # 현재 타일 상세정보
    # ========================================================

    def get_tile_info(self, tile):

        result = "[현재 칸]\n"

        if not tile.plowed:

            result += "상태: 평범한 땅"

            return result

        if not tile.has_crop():

            result += "상태: 갈아놓은 땅"

            return result

        crop = tile.crop_data()

        result += (
            f"작물: {crop.name}\n"
            f"성장: {tile.age}/{crop.grow_days}\n"
        )

        if tile.is_mature():

            result += "상태: 수확 가능"

            return result

        if tile.watered_today(self.day):

            result += "수분: 오늘 물 줌"

        elif tile.needs_water(self.day):

            result += "수분: 물 필요!"

        else:

            remaining = (
                crop.water_interval
                - (
                    self.day
                    - tile.last_watered_day
                )
            )

            result += (
                f"수분: 충분 ({remaining}일)"
            )

        return result


# ============================================================
# 시작
# ============================================================

if __name__ == "__main__":

    game = FarmGame()
    game.run()