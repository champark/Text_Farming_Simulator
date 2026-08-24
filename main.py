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

DESIRED_WINDOW_HEIGHT = 900


# ============================================================
# 시간 설정
# ============================================================

DAY_START_MINUTE = 6 * 60
DAY_END_MINUTE = 22 * 60

TIME_MOVE = 5
TIME_PLOW = 20
TIME_PLANT = 10
TIME_WATER = 10
TIME_HARVEST = 15
TIME_SHOP_TRANSACTION = 5


# ============================================================
# 체력 설정
# ============================================================

MAX_STAMINA = 100

STAMINA_MOVE = 1
STAMINA_PLOW = 8
STAMINA_PLANT = 3
STAMINA_WATER = 4
STAMINA_HARVEST = 5


# ============================================================
# 한글 두벌식 키 대응
# ============================================================

HANGUL_KEY_MAP = {
    "ㅂ": "q",
    "ㅈ": "w",
    "ㄷ": "e",

    "ㅁ": "a",
    "ㄴ": "s",
    "ㅇ": "d",

    "ㅋ": "z",
    "ㅠ": "b",
    "ㅜ": "n",
}


def normalize_char(char):

    if not char:
        return ""

    char = char.lower()

    return HANGUL_KEY_MAP.get(
        char,
        char
    )


# ============================================================
# 작물 데이터
# ============================================================

@dataclass(frozen=True)
class CropData:
    name: str
    symbol: str

    grow_days: int
    water_interval: int

    seed_price: int
    sell_price: int


CROPS = {
    "wheat": CropData(
        name="밀",
        symbol="w",
        grow_days=4,
        water_interval=1,
        seed_price=10,
        sell_price=18,
    ),

    "carrot": CropData(
        name="당근",
        symbol="c",
        grow_days=5,
        water_interval=2,
        seed_price=20,
        sell_price=40,
    ),

    "potato": CropData(
        name="감자",
        symbol="o",
        grow_days=6,
        water_interval=3,
        seed_price=30,
        sell_price=65,
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

        return (
            self.age
            >= crop.grow_days
        )

    def needs_water(
        self,
        current_day
    ):

        if not self.has_crop():
            return False

        if self.is_mature():
            return False

        crop = self.crop_data()

        if self.last_watered_day is None:
            return True

        return (
            current_day
            - self.last_watered_day
            >= crop.water_interval
        )

    def watered_today(
        self,
        current_day
    ):

        return (
            self.last_watered_day
            == current_day
        )

    def can_grow_today(
        self,
        current_day
    ):

        if not self.has_crop():
            return False

        if self.is_mature():
            return False

        if self.last_watered_day is None:
            return False

        crop = self.crop_data()

        return (
            current_day
            - self.last_watered_day
            < crop.water_interval
        )


# ============================================================
# 게임
# ============================================================

class FarmGame:

    def __init__(self):

        self.root = tk.Tk()

        self.root.title(
            GAME_TITLE
        )

        # ====================================================
        # 창 크기
        # ====================================================

        screen_width = (
            self.root.winfo_screenwidth()
        )

        screen_height = (
            self.root.winfo_screenheight()
        )

        available_width = max(
            900,
            screen_width - 60
        )

        available_height = max(
            700,
            screen_height - 100
        )

        self.window_width = min(
            DESIRED_WINDOW_WIDTH,
            available_width
        )

        self.window_height = min(
            DESIRED_WINDOW_HEIGHT,
            available_height
        )

        pos_x = max(
            0,
            (
                screen_width
                - self.window_width
            ) // 2
        )

        pos_y = max(
            0,
            (
                screen_height
                - self.window_height
            ) // 2
        )

        self.root.geometry(
            f"{self.window_width}"
            f"x{self.window_height}"
            f"+{pos_x}+{pos_y}"
        )

        self.root.resizable(
            True,
            True
        )

        self.root.configure(
            bg="#181818"
        )

        # ====================================================
        # 날짜 / 시간
        # ====================================================

        self.day = 1

        self.current_time = (
            DAY_START_MINUTE
        )

        # ====================================================
        # 체력
        # ====================================================

        self.max_stamina = MAX_STAMINA
        self.stamina = MAX_STAMINA

        # ====================================================
        # 플레이어
        # ====================================================

        self.player_x = (
            GRID_SIZE // 2
        )

        self.player_y = (
            GRID_SIZE // 2
        )

        # ====================================================
        # 작업 선택
        # ====================================================

        self.selected_action = 0
        self.selected_crop_index = 0

        self.actions = [
            "쟁기질",
            "씨 뿌리기",
            "물주기",
            "수확",
        ]

        self.message = (
            "농장에 도착했다."
        )

        # ====================================================
        # 돈
        # ====================================================

        self.money = 500

        # ====================================================
        # 인벤토리
        # ====================================================

        self.inventory = {

            "seeds": {
                "wheat": 5,
                "carrot": 5,
                "potato": 5,
            },

            "crops": {
                "wheat": 0,
                "carrot": 0,
                "potato": 0,
            },
        }

        # ====================================================
        # 상점
        # ====================================================

        self.shop_open = False
        self.shop_mode = "buy"

        self.shop_selected_index = 0

        self.shop_message = (
            "구매하거나 판매할 "
            "품목을 선택하세요."
        )

        # ====================================================
        # 밭
        # ====================================================

        self.field = [
            [
                Tile()
                for _ in range(
                    GRID_SIZE
                )
            ]
            for _ in range(
                GRID_SIZE
            )
        ]

        # ====================================================
        # 캔버스
        # ====================================================

        self.canvas = tk.Canvas(
            self.root,
            bg="#181818",
            highlightthickness=0,
        )

        self.canvas.pack(
            fill="both",
            expand=True
        )

        # ====================================================
        # 입력
        # ====================================================

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
    # 시간
    # ========================================================

    def format_time(
        self,
        minute_value=None
    ):

        if minute_value is None:
            minute_value = (
                self.current_time
            )

        hour = (
            minute_value // 60
        )

        minute = (
            minute_value % 60
        )

        return (
            f"{hour:02d}:{minute:02d}"
        )

    def can_spend_time(
        self,
        minutes
    ):

        return (
            self.current_time
            + minutes
            <= DAY_END_MINUTE
        )

    def spend_time(
        self,
        minutes
    ):

        self.current_time += minutes

    def time_block_message(
        self,
        required_minutes
    ):

        self.message = (
            "오늘은 시간이 너무 늦었다.\n"
            f"현재 {self.format_time()} / "
            f"필요 시간 {required_minutes}분\n"
            "N키를 눌러 잠자리에 들 수 있다."
        )

    # ========================================================
    # 체력
    # ========================================================

    def can_spend_stamina(
        self,
        amount
    ):

        return (
            self.stamina
            >= amount
        )

    def spend_stamina(
        self,
        amount
    ):

        self.stamina -= amount

        if self.stamina < 0:
            self.stamina = 0

    def stamina_block_message(
        self,
        required_stamina
    ):

        self.message = (
            "체력이 부족하다.\n"
            f"현재 체력 "
            f"{self.stamina}/{self.max_stamina} / "
            f"필요 체력 {required_stamina}\n"
            "N키를 눌러 잠을 자면 체력이 회복된다."
        )

    # ========================================================
    # 행동 가능 여부
    # ========================================================

    def can_perform_action(
        self,
        time_cost,
        stamina_cost
    ):

        if not self.can_spend_time(
            time_cost
        ):

            self.time_block_message(
                time_cost
            )

            return False

        if not self.can_spend_stamina(
            stamina_cost
        ):

            self.stamina_block_message(
                stamina_cost
            )

            return False

        return True

    # ========================================================
    # 창 크기 변경
    # ========================================================

    def on_resize(
        self,
        event
    ):

        if event.widget == self.root:

            self.window_width = (
                event.width
            )

            self.window_height = (
                event.height
            )

            self.draw()

    # ========================================================
    # 입력
    # ========================================================

    def on_key(
        self,
        event
    ):

        char = normalize_char(
            event.char
        )

        key = (
            event.keysym.lower()
        )

        # ====================================================
        # 상점
        # ====================================================

        if self.shop_open:

            self.handle_shop_input(
                char,
                key
            )

            self.draw()

            return

        # ====================================================
        # 이동
        # ====================================================

        if (
            char == "w"
            or key == "up"
        ):

            self.move(
                0,
                -1
            )

        elif (
            char == "s"
            or key == "down"
        ):

            self.move(
                0,
                1
            )

        elif (
            char == "a"
            or key == "left"
        ):

            self.move(
                -1,
                0
            )

        elif (
            char == "d"
            or key == "right"
        ):

            self.move(
                1,
                0
            )

        # ====================================================
        # 작업 선택
        # ====================================================

        elif char == "1":

            self.selected_action = 0

            self.message = (
                "쟁기질을 선택했다."
            )

        elif char == "2":

            self.selected_action = 1

            crop_key = CROP_KEYS[
                self.selected_crop_index
            ]

            crop = CROPS[
                crop_key
            ]

            seed_count = (
                self.inventory[
                    "seeds"
                ][crop_key]
            )

            self.message = (
                "씨 뿌리기를 선택했다.\n"
                f"{crop.name} 씨앗: "
                f"{seed_count}개"
            )

        elif char == "3":

            self.selected_action = 2

            self.message = (
                "물주기를 선택했다."
            )

        elif char == "4":

            self.selected_action = 3

            self.message = (
                "수확을 선택했다."
            )

        # ====================================================
        # 씨앗 변경
        # ====================================================

        elif char == "q":

            self.change_crop(-1)

        elif char == "e":

            self.change_crop(1)

        # ====================================================
        # 상호작용
        # ====================================================

        elif (
            char == "z"
            or key == "return"
            or key == "space"
        ):

            self.interact()

        # ====================================================
        # 잠자기
        # ====================================================

        elif char == "n":

            self.sleep()

        # ====================================================
        # 상점
        # ====================================================

        elif char == "b":

            self.open_shop()

        # ====================================================
        # 종료
        # ====================================================

        elif key == "escape":

            self.root.destroy()

            return

        self.draw()

    # ========================================================
    # 이동
    # ========================================================

    def move(
        self,
        dx,
        dy
    ):

        new_x = (
            self.player_x
            + dx
        )

        new_y = (
            self.player_y
            + dy
        )

        if not (
            0 <= new_x < GRID_SIZE
            and
            0 <= new_y < GRID_SIZE
        ):

            self.message = (
                "밭 밖으로 나갈 수 없다."
            )

            return

        if not self.can_perform_action(
            TIME_MOVE,
            STAMINA_MOVE
        ):

            return

        self.player_x = new_x
        self.player_y = new_y

        self.spend_time(
            TIME_MOVE
        )

        self.spend_stamina(
            STAMINA_MOVE
        )

    # ========================================================
    # 씨앗 선택
    # ========================================================

    def change_crop(
        self,
        direction
    ):

        self.selected_crop_index += (
            direction
        )

        self.selected_crop_index %= (
            len(CROP_KEYS)
        )

        crop_key = CROP_KEYS[
            self.selected_crop_index
        ]

        crop = CROPS[
            crop_key
        ]

        seed_count = (
            self.inventory[
                "seeds"
            ][crop_key]
        )

        self.message = (
            f"씨앗 선택: {crop.name}\n"
            f"보유 씨앗: {seed_count}개"
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

        tile = (
            self.current_tile()
        )

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

        if not self.can_perform_action(
            TIME_PLOW,
            STAMINA_PLOW
        ):

            return

        tile.plowed = True

        self.spend_time(
            TIME_PLOW
        )

        self.spend_stamina(
            STAMINA_PLOW
        )

        self.message = (
            "땅을 갈았다.\n"
            f"시간 -{TIME_PLOW}분 / "
            f"체력 -{STAMINA_PLOW}"
        )

    # ========================================================
    # 씨 뿌리기
    # ========================================================

    def plant(self):

        tile = (
            self.current_tile()
        )

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

        crop = CROPS[
            crop_key
        ]

        seed_count = (
            self.inventory[
                "seeds"
            ][crop_key]
        )

        if seed_count <= 0:

            self.message = (
                f"{crop.name} 씨앗이 없다!\n"
                "B / ㅠ 키로 상점을 열 수 있다."
            )

            return

        if not self.can_perform_action(
            TIME_PLANT,
            STAMINA_PLANT
        ):

            return

        self.inventory[
            "seeds"
        ][crop_key] -= 1

        tile.crop_type = (
            crop_key
        )

        tile.planted_day = (
            self.day
        )

        tile.age = 0

        tile.last_watered_day = (
            None
        )

        self.spend_time(
            TIME_PLANT
        )

        self.spend_stamina(
            STAMINA_PLANT
        )

        remaining = (
            self.inventory[
                "seeds"
            ][crop_key]
        )

        self.message = (
            f"{crop.name} 씨앗을 심었다.\n"
            f"시간 -{TIME_PLANT}분 / "
            f"체력 -{STAMINA_PLANT} / "
            f"씨앗 {remaining}개"
        )

    # ========================================================
    # 물주기
    # ========================================================

    def water(self):

        tile = (
            self.current_tile()
        )

        if not tile.has_crop():

            self.message = (
                "여기에는 작물이 없다."
            )

            return

        crop = (
            tile.crop_data()
        )

        if tile.is_mature():

            self.message = (
                f"{crop.name}은 "
                "이미 다 자랐다."
            )

            return

        if tile.watered_today(
            self.day
        ):

            self.message = (
                "오늘은 이미 물을 주었다."
            )

            return

        if not tile.needs_water(
            self.day
        ):

            remaining = (
                crop.water_interval
                - (
                    self.day
                    - tile.last_watered_day
                )
            )

            self.message = (
                f"{crop.name}은 아직 "
                "물이 충분하다.\n"
                f"{remaining}일 후 물 필요"
            )

            return

        if not self.can_perform_action(
            TIME_WATER,
            STAMINA_WATER
        ):

            return

        tile.last_watered_day = (
            self.day
        )

        self.spend_time(
            TIME_WATER
        )

        self.spend_stamina(
            STAMINA_WATER
        )

        self.message = (
            f"{crop.name}에 물을 주었다.\n"
            f"시간 -{TIME_WATER}분 / "
            f"체력 -{STAMINA_WATER}"
        )

    # ========================================================
    # 수확
    # ========================================================

    def harvest(self):

        tile = (
            self.current_tile()
        )

        if not tile.has_crop():

            self.message = (
                "수확할 작물이 없다."
            )

            return

        crop = (
            tile.crop_data()
        )

        if not tile.is_mature():

            self.message = (
                f"{crop.name}은 아직 "
                "자라고 있다.\n"
                f"성장 단계: "
                f"{tile.age}/{crop.grow_days}"
            )

            return

        if not self.can_perform_action(
            TIME_HARVEST,
            STAMINA_HARVEST
        ):

            return

        crop_key = (
            tile.crop_type
        )

        harvest_amount = 1

        self.inventory[
            "crops"
        ][crop_key] += (
            harvest_amount
        )

        total_amount = (
            self.inventory[
                "crops"
            ][crop_key]
        )

        tile.crop_type = None
        tile.age = 0
        tile.last_watered_day = None
        tile.planted_day = 0

        tile.plowed = True

        self.spend_time(
            TIME_HARVEST
        )

        self.spend_stamina(
            STAMINA_HARVEST
        )

        self.message = (
            f"{crop.name}을 수확했다!\n"
            f"{crop.name} +1 / "
            f"시간 -{TIME_HARVEST}분 / "
            f"체력 -{STAMINA_HARVEST}\n"
            f"현재 보유량: {total_amount}"
        )

    # ========================================================
    # 잠자기
    # ========================================================

    def sleep(self):

        grown_count = 0

        # ----------------------------------------------------
        # 오늘 성장 처리
        # ----------------------------------------------------

        for row in self.field:

            for tile in row:

                if tile.can_grow_today(
                    self.day
                ):

                    tile.age += 1

                    grown_count += 1

                    crop = (
                        tile.crop_data()
                    )

                    if (
                        tile.age
                        > crop.grow_days
                    ):

                        tile.age = (
                            crop.grow_days
                        )

        # ----------------------------------------------------
        # 다음 날
        # ----------------------------------------------------

        self.day += 1

        self.current_time = (
            DAY_START_MINUTE
        )

        # 체력 완전 회복
        self.stamina = (
            self.max_stamina
        )

        if grown_count > 0:

            self.message = (
                f"{self.day}일째 아침이다.\n"
                f"작물 {grown_count}칸이 성장했다.\n"
                "체력이 완전히 회복되었다."
            )

        else:

            self.message = (
                f"{self.day}일째 아침이다.\n"
                "체력이 완전히 회복되었다."
            )

    # ========================================================
    # 상점
    # ========================================================

    def open_shop(self):

        self.shop_open = True
        self.shop_mode = "buy"
        self.shop_selected_index = 0

        self.shop_message = (
            "어서 오세요! "
            "무엇을 도와드릴까요?"
        )

    def close_shop(self):

        self.shop_open = False

        self.message = (
            "상점을 나왔다."
        )

    # ========================================================
    # 상점 입력
    # ========================================================

    def handle_shop_input(
        self,
        char,
        key
    ):

        if (
            char == "b"
            or key == "escape"
        ):

            self.close_shop()

            return

        if (
            char == "a"
            or key == "left"
        ):

            self.shop_mode = "buy"

            self.shop_message = (
                "씨앗 구매 메뉴."
            )

            return

        if (
            char == "d"
            or key == "right"
        ):

            self.shop_mode = "sell"

            self.shop_message = (
                "농산물 판매 메뉴."
            )

            return

        if (
            char == "w"
            or key == "up"
        ):

            self.shop_selected_index -= 1

            self.shop_selected_index %= (
                len(CROP_KEYS)
            )

            return

        if (
            char == "s"
            or key == "down"
        ):

            self.shop_selected_index += 1

            self.shop_selected_index %= (
                len(CROP_KEYS)
            )

            return

        if (
            char == "z"
            or key == "return"
            or key == "space"
        ):

            if self.shop_mode == "buy":

                self.buy_selected_seed()

            else:

                self.sell_selected_crop()

    # ========================================================
    # 씨앗 구매
    # ========================================================

    def buy_selected_seed(self):

        crop_key = CROP_KEYS[
            self.shop_selected_index
        ]

        crop = CROPS[
            crop_key
        ]

        price = (
            crop.seed_price
        )

        if self.money < price:

            self.shop_message = (
                "돈이 부족하다!\n"
                f"{crop.name} 씨앗: "
                f"{price} G"
            )

            return

        if not self.can_spend_time(
            TIME_SHOP_TRANSACTION
        ):

            self.shop_message = (
                "오늘은 거래하기에 "
                "너무 늦었다.\n"
                f"현재 {self.format_time()}"
            )

            return

        self.money -= price

        self.inventory[
            "seeds"
        ][crop_key] += 1

        self.spend_time(
            TIME_SHOP_TRANSACTION
        )

        count = (
            self.inventory[
                "seeds"
            ][crop_key]
        )

        self.shop_message = (
            f"{crop.name} 씨앗 구입 "
            f"-{price} G\n"
            f"보유 {count}개 / "
            f"{TIME_SHOP_TRANSACTION}분 경과"
        )

    # ========================================================
    # 농산물 판매
    # ========================================================

    def sell_selected_crop(self):

        crop_key = CROP_KEYS[
            self.shop_selected_index
        ]

        crop = CROPS[
            crop_key
        ]

        amount = (
            self.inventory[
                "crops"
            ][crop_key]
        )

        if amount <= 0:

            self.shop_message = (
                f"판매할 {crop.name}이 없다."
            )

            return

        if not self.can_spend_time(
            TIME_SHOP_TRANSACTION
        ):

            self.shop_message = (
                "오늘은 거래하기에 "
                "너무 늦었다.\n"
                f"현재 {self.format_time()}"
            )

            return

        price = (
            crop.sell_price
        )

        self.inventory[
            "crops"
        ][crop_key] -= 1

        self.money += price

        self.spend_time(
            TIME_SHOP_TRANSACTION
        )

        remaining = (
            self.inventory[
                "crops"
            ][crop_key]
        )

        self.shop_message = (
            f"{crop.name} 판매 "
            f"+{price} G\n"
            f"남은 수량 {remaining}개 / "
            f"{TIME_SHOP_TRANSACTION}분 경과"
        )

    # ========================================================
    # 전체 화면
    # ========================================================

    def draw(self):

        if not (
            self.canvas.winfo_exists()
        ):
            return

        self.canvas.delete(
            "all"
        )

        self.draw_field()
        self.draw_panel()

        if self.shop_open:

            self.draw_shop()

    # ========================================================
    # 밭
    # ========================================================

    def draw_field(self):

        offset_x = FIELD_MARGIN
        offset_y = FIELD_MARGIN

        for y in range(
            GRID_SIZE
        ):

            for x in range(
                GRID_SIZE
            ):

                tile = (
                    self.field[y][x]
                )

                px = (
                    offset_x
                    + x * CELL_SIZE
                )

                py = (
                    offset_y
                    + y * CELL_SIZE
                )

                bg = "#3a2b22"

                if tile.plowed:
                    bg = "#62452f"

                if tile.has_crop():
                    bg = "#44552e"

                if tile.watered_today(
                    self.day
                ):
                    bg = "#355667"

                self.canvas.create_rectangle(
                    px,
                    py,
                    px + CELL_SIZE,
                    py + CELL_SIZE,
                    fill=bg,
                    outline="#888888",
                    width=2,
                )

                symbol = "."

                if tile.plowed:
                    symbol = ":"

                if tile.has_crop():

                    crop = (
                        tile.crop_data()
                    )

                    symbol = (
                        crop.symbol
                    )

                    if tile.is_mature():
                        symbol = (
                            symbol.upper()
                        )

                if (
                    x == self.player_x
                    and
                    y == self.player_y
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
    # 오른쪽 패널
    # ========================================================

    def draw_panel(self):

        panel_x = (
            FIELD_MARGIN
            + FIELD_PIXEL_SIZE
            + 40
        )

        panel_right = (
            self.window_width
            - 25
        )

        panel_width = max(
            250,
            panel_right - panel_x
        )

        y = 18

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
                21,
                "bold",
            ),
        )

        y += 46

        # ----------------------------------------------------
        # 날짜 / 시간 / 돈
        # ----------------------------------------------------

        time_color = "#f1d58a"

        if self.current_time >= 20 * 60:
            time_color = "#ffad8a"

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=(
                f"{self.day}일째    "
                f"{self.format_time()}    "
                f"{self.money:,} G"
            ),
            fill=time_color,
            font=(
                "Malgun Gothic",
                15,
                "bold",
            ),
        )

        y += 38

        # ----------------------------------------------------
        # 체력
        # ----------------------------------------------------

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=(
                f"체력 "
                f"{self.stamina}/{self.max_stamina}"
            ),
            fill="#dddddd",
            font=(
                "Malgun Gothic",
                11,
                "bold",
            ),
        )

        y += 24

        bar_width = min(
            330,
            panel_width - 20
        )

        bar_height = 18

        self.canvas.create_rectangle(
            panel_x,
            y,
            panel_x + bar_width,
            y + bar_height,
            fill="#333333",
            outline="#777777",
        )

        stamina_ratio = (
            self.stamina
            / self.max_stamina
        )

        current_bar_width = (
            bar_width
            * stamina_ratio
        )

        if stamina_ratio > 0.6:

            stamina_color = "#5eaf66"

        elif stamina_ratio > 0.3:

            stamina_color = "#d4ad4d"

        else:

            stamina_color = "#c95a5a"

        self.canvas.create_rectangle(
            panel_x,
            y,
            panel_x + current_bar_width,
            y + bar_height,
            fill=stamina_color,
            outline="",
        )

        y += 32

        # ----------------------------------------------------
        # 현재 작업
        # ----------------------------------------------------

        action = (
            self.actions[
                self.selected_action
            ]
        )

        crop_key = CROP_KEYS[
            self.selected_crop_index
        ]

        crop = CROPS[
            crop_key
        ]

        seed_count = (
            self.inventory[
                "seeds"
            ][crop_key]
        )

        info = (
            "[현재 작업]\n"
            f"{self.selected_action + 1}. "
            f"{action}\n"
            f"선택 씨앗: "
            f"{crop.name} × {seed_count}\n"
            f"성장 {crop.grow_days}일 / "
            f"물 {crop.water_interval}일마다"
        )

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=info,
            fill="#dddddd",
            font=(
                "Malgun Gothic",
                11,
            ),
        )

        y += 92

        # ----------------------------------------------------
        # 인벤토리
        # ----------------------------------------------------

        inventory_text = (
            "[인벤토리]\n"
            "씨앗                 농산물\n"
            f"밀   {self.inventory['seeds']['wheat']:>3}"
            f"          밀   "
            f"{self.inventory['crops']['wheat']:>3}\n"

            f"당근 {self.inventory['seeds']['carrot']:>3}"
            f"          당근 "
            f"{self.inventory['crops']['carrot']:>3}\n"

            f"감자 {self.inventory['seeds']['potato']:>3}"
            f"          감자 "
            f"{self.inventory['crops']['potato']:>3}"
        )

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=inventory_text,
            fill="#d8e6c3",
            font=(
                "Malgun Gothic",
                10,
            ),
        )

        y += 92

        # ----------------------------------------------------
        # 현재 칸
        # ----------------------------------------------------

        tile = (
            self.current_tile()
        )

        tile_text = (
            self.get_tile_info(
                tile
            )
        )

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=tile_text,
            fill="#a9d6ff",
            font=(
                "Malgun Gothic",
                10,
            ),
        )

        y += 84

        # ----------------------------------------------------
        # 메시지
        # ----------------------------------------------------

        self.canvas.create_rectangle(
            panel_x - 8,
            y - 7,
            panel_right,
            y + 77,
            fill="#252525",
            outline="#666666",
            width=2,
        )

        self.canvas.create_text(
            panel_x + 5,
            y + 4,
            anchor="nw",
            text=self.message,
            width=max(
                240,
                panel_right
                - panel_x
                - 20
            ),
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                10,
            ),
        )

        y += 94

        # ----------------------------------------------------
        # 행동 비용
        # ----------------------------------------------------

        cost_info = (
            "[행동 비용]\n"
            f"이동      {TIME_MOVE}분 / 체력 {STAMINA_MOVE}\n"
            f"쟁기질   {TIME_PLOW}분 / 체력 {STAMINA_PLOW}\n"
            f"파종      {TIME_PLANT}분 / 체력 {STAMINA_PLANT}\n"
            f"물주기   {TIME_WATER}분 / 체력 {STAMINA_WATER}\n"
            f"수확      {TIME_HARVEST}분 / 체력 {STAMINA_HARVEST}\n"
            f"거래      {TIME_SHOP_TRANSACTION}분 / 체력 0"
        )

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=cost_info,
            fill="#d3c9a3",
            font=(
                "Malgun Gothic",
                9,
            ),
        )

        y += 116

        # ----------------------------------------------------
        # 조작법
        # ----------------------------------------------------

        controls = (
            "[조작]\n"
            "WASD / 방향키     이동\n"
            "1 쟁기질    2 씨 뿌리기\n"
            "3 물주기    4 수확\n"
            "Q / E              씨앗 선택\n"
            "Z / SPACE / ENTER  실행\n"
            "B                  상점\n"
            "N                  잠자기\n"
            "ESC                종료\n"
            "※ 한글 입력 상태 대응"
        )

        self.canvas.create_text(
            panel_x,
            y,
            anchor="nw",
            text=controls,
            fill="#bbbbbb",
            font=(
                "Malgun Gothic",
                9,
            ),
        )

    # ========================================================
    # 상점 화면
    # ========================================================

    def draw_shop(self):

        shop_width = min(
            700,
            self.window_width - 100
        )

        shop_height = min(
            600,
            self.window_height - 100
        )

        left = (
            self.window_width
            - shop_width
        ) // 2

        top = (
            self.window_height
            - shop_height
        ) // 2

        right = (
            left
            + shop_width
        )

        bottom = (
            top
            + shop_height
        )

        self.canvas.create_rectangle(
            0,
            0,
            self.window_width,
            self.window_height,
            fill="#080808",
            stipple="gray50",
            outline="",
        )

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="#202020",
            outline="#d8c48c",
            width=3,
        )

        center_x = (
            left + right
        ) // 2

        y = (
            top + 25
        )

        self.canvas.create_text(
            center_x,
            y,
            text="상점",
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                26,
                "bold",
            ),
        )

        y += 48

        self.canvas.create_text(
            center_x,
            y,
            text=(
                f"{self.format_time()}    "
                f"보유금 {self.money:,} G"
            ),
            fill="#f1d58a",
            font=(
                "Malgun Gothic",
                15,
                "bold",
            ),
        )

        y += 46

        buy_color = (
            "#ffffff"
            if self.shop_mode == "buy"
            else "#777777"
        )

        sell_color = (
            "#ffffff"
            if self.shop_mode == "sell"
            else "#777777"
        )

        self.canvas.create_text(
            center_x - 120,
            y,
            text="[ 구매 ]",
            fill=buy_color,
            font=(
                "Malgun Gothic",
                15,
                "bold",
            ),
        )

        self.canvas.create_text(
            center_x + 120,
            y,
            text="[ 판매 ]",
            fill=sell_color,
            font=(
                "Malgun Gothic",
                15,
                "bold",
            ),
        )

        y += 55

        for (
            index,
            crop_key
        ) in enumerate(
            CROP_KEYS
        ):

            crop = CROPS[
                crop_key
            ]

            selected = (
                index
                == self.shop_selected_index
            )

            if selected:

                prefix = "▶ "
                color = "#ffffff"

            else:

                prefix = "   "
                color = "#aaaaaa"

            if self.shop_mode == "buy":

                price = (
                    crop.seed_price
                )

                owned = (
                    self.inventory[
                        "seeds"
                    ][crop_key]
                )

                line = (
                    f"{prefix}"
                    f"{crop.name} 씨앗"
                    f"     {price:>3} G"
                    f"     보유 {owned}"
                )

            else:

                price = (
                    crop.sell_price
                )

                owned = (
                    self.inventory[
                        "crops"
                    ][crop_key]
                )

                line = (
                    f"{prefix}"
                    f"{crop.name}"
                    f"          {price:>3} G"
                    f"     보유 {owned}"
                )

            self.canvas.create_text(
                left + 90,
                y,
                anchor="w",
                text=line,
                fill=color,
                font=(
                    "Malgun Gothic",
                    15,
                    (
                        "bold"
                        if selected
                        else "normal"
                    ),
                ),
            )

            y += 55

        message_top = (
            bottom - 150
        )

        self.canvas.create_rectangle(
            left + 40,
            message_top,
            right - 40,
            message_top + 65,
            fill="#151515",
            outline="#555555",
        )

        self.canvas.create_text(
            center_x,
            message_top + 32,
            text=self.shop_message,
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                11,
            ),
            width=shop_width - 120,
        )

        self.canvas.create_text(
            center_x,
            bottom - 45,
            text=(
                "← → / A D : 구매·판매    "
                "↑ ↓ / W S : 품목    "
                "Z / SPACE / ENTER : 거래    "
                "B / ESC : 나가기"
            ),
            fill="#bdbdbd",
            font=(
                "Malgun Gothic",
                10,
            ),
        )

    # ========================================================
    # 현재 타일 정보
    # ========================================================

    def get_tile_info(
        self,
        tile
    ):

        result = (
            "[현재 칸]\n"
        )

        if not tile.plowed:

            result += (
                "상태: 평범한 땅"
            )

            return result

        if not tile.has_crop():

            result += (
                "상태: 갈아놓은 땅"
            )

            return result

        crop = (
            tile.crop_data()
        )

        result += (
            f"작물: {crop.name}\n"
            f"성장: "
            f"{tile.age}/{crop.grow_days}\n"
        )

        if tile.is_mature():

            result += (
                "상태: 수확 가능"
            )

            return result

        if tile.watered_today(
            self.day
        ):

            result += (
                "수분: 오늘 물 줌"
            )

        elif tile.needs_water(
            self.day
        ):

            result += (
                "수분: 물 필요!"
            )

        else:

            remaining = (
                crop.water_interval
                - (
                    self.day
                    - tile.last_watered_day
                )
            )

            result += (
                f"수분: 충분 "
                f"({remaining}일)"
            )

        return result


# ============================================================
# 시작
# ============================================================

if __name__ == "__main__":

    game = FarmGame()
    game.run()