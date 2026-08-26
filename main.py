import tkinter as tk
from dataclasses import dataclass
from typing import Optional


# ============================================================
# 기본 설정
# ============================================================

GAME_TITLE = "텍스트 파밍 시뮬레이터"

GRID_SIZE = 9
CELL_SIZE = 72

# 9x9 밭 아래 중앙에 별도 집 칸을 둔다.
# 밭 자체의 81칸은 그대로 유지된다.
HOUSE_POS = (
    GRID_SIZE // 2,
    GRID_SIZE,
)

# 9x9 밭 아래 오른쪽에 별도 상점 칸을 둔다.
SHOP_POS = (
    GRID_SIZE - 1,
    GRID_SIZE,
)

FIELD_MARGIN = 25
PANEL_WIDTH = 500

FIELD_PIXEL_SIZE = GRID_SIZE * CELL_SIZE

DESIRED_WINDOW_WIDTH = (
    FIELD_MARGIN
    + FIELD_PIXEL_SIZE
    + PANEL_WIDTH
)

DESIRED_WINDOW_HEIGHT = 1000


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

STAMINA_MOVE = 0
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
# 시나리오 데이터
# ============================================================

SCENARIOS = [
    {
        "id": "first_winter",
        "title": "첫 번째 겨울",
        "subtitle": "다가오는 겨울을 준비하라",
        "description": (
            "30일 동안 농사를 지어 겨울을 준비한다.\n"
            "겨울이 오기 전에 충분한 식량을 비축해야 한다."
        ),
        "goal": "목표: 30일 안에 식량 100 비축",
    },
]


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
            screen_height - 50
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
        # 화면 상태
        # ====================================================

        self.screen_mode = "main"
        self.current_scenario_id = None
        self.scenario_selected_index = 0

        # 마우스 클릭 판정용 영역
        self.click_regions = {}

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
        # 최근 기록
        # ====================================================

        self.activity_log = []

        self.add_log(
            "농장에 도착"
        )

        self.message = (
            "농장에 도착했다.\n"
            "집은 H, 상점은 밭 아래 오른쪽 S에 있다."
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

        self.root.bind(
            "<Button-1>",
            self.on_click
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
            "이동은 가능하다. 집으로 돌아가 "
            "N키를 눌러 잠을 자자."
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
    # 최근 기록
    # ========================================================

    def add_log(
        self,
        text
    ):

        entry = (
            f"{self.format_time()}  "
            f"{text}"
        )

        self.activity_log.append(
            entry
        )

        # 내부적으로는 최근 100개까지 보관
        if len(self.activity_log) > 100:
            self.activity_log = (
                self.activity_log[-100:]
            )

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
        # 메인 화면
        # ====================================================

        if self.screen_mode == "main":

            if (
                key == "return"
                or key == "space"
                or char == "z"
            ):

                self.screen_mode = (
                    "scenario_select"
                )

                self.draw()

                return

            if key == "escape":

                self.root.destroy()

                return

            return

        # ====================================================
        # 시나리오 선택
        # ====================================================

        if self.screen_mode == "scenario_select":

            if (
                key == "up"
                or char == "w"
            ):

                self.scenario_selected_index -= 1
                self.scenario_selected_index %= len(
                    SCENARIOS
                )

            elif (
                key == "down"
                or char == "s"
            ):

                self.scenario_selected_index += 1
                self.scenario_selected_index %= len(
                    SCENARIOS
                )

            elif (
                key == "return"
                or key == "space"
                or char == "z"
            ):

                scenario = SCENARIOS[
                    self.scenario_selected_index
                ]

                self.start_scenario(
                    scenario["id"]
                )

                return

            elif key == "escape":

                self.screen_mode = "main"

            self.draw()

            return

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

            if (
                (self.player_x, self.player_y)
                == SHOP_POS
            ):

                self.open_shop()

            else:

                self.message = (
                    "상점은 직접 찾아가야 한다.\n"
                    "밭 아래 오른쪽의 S 표시로 가자."
                )

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

        inside_field = (
            0 <= new_x < GRID_SIZE
            and
            0 <= new_y < GRID_SIZE
        )

        at_house = (
            (new_x, new_y)
            == HOUSE_POS
        )

        at_shop = (
            (new_x, new_y)
            == SHOP_POS
        )

        if not (
            inside_field
            or at_house
            or at_shop
        ):

            self.message = (
                "그쪽으로는 갈 수 없다."
            )

            return

        # 이동은 체력을 소모하지 않는다.
        # 작업 종료 시각 이후에도 집으로 돌아갈 수 있도록
        # 이동 자체는 시간 제한으로 막지 않는다.
        # 시간은 기존처럼 5분 흐른다.

        self.player_x = new_x
        self.player_y = new_y

        self.spend_time(
            TIME_MOVE
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

        if (
            (self.player_x, self.player_y)
            == HOUSE_POS
            or
            (self.player_x, self.player_y)
            == SHOP_POS
        ):

            return None

        return self.field[
            self.player_y
        ][
            self.player_x
        ]

    # ========================================================
    # 상호작용
    # ========================================================

    def interact(self):

        if (
            (self.player_x, self.player_y)
            == HOUSE_POS
        ):

            self.sleep()

            return

        if (
            (self.player_x, self.player_y)
            == SHOP_POS
        ):

            self.open_shop()

            return

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

        self.add_log(
            "밭 쟁기질"
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

        self.add_log(
            f"{crop.name} 씨앗 파종"
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

        self.add_log(
            f"{crop.name}에 물을 줌"
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

        self.add_log(
            f"{crop.name} 수확 +1"
        )

    # ========================================================
    # 잠자기
    # ========================================================

    def sleep(self):

        if (
            (self.player_x, self.player_y)
            != HOUSE_POS
        ):

            self.message = (
                "잠은 집에서만 잘 수 있다.\n"
                "밭 아래쪽의 H 표시로 돌아가자."
            )

            return

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

        self.add_log(
            f"{self.day}일째 아침"
        )

        self.add_log(
            "체력 완전 회복"
        )

        if grown_count > 0:

            self.add_log(
                f"작물 {grown_count}칸 성장"
            )

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

        if (
            (self.player_x, self.player_y)
            != SHOP_POS
        ):

            self.message = (
                "상점은 직접 찾아가야 한다.\n"
                "밭 아래 오른쪽의 S 표시로 가자."
            )

            return

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

        self.add_log(
            "상점에서 나옴"
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

        self.add_log(
            f"{crop.name} 씨앗 구입 -{price}G"
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

        self.add_log(
            f"{crop.name} 판매 +{price}G"
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

        self.click_regions = {}

        if self.screen_mode == "main":

            self.draw_main_menu()

            return

        if self.screen_mode == "scenario_select":

            self.draw_scenario_select()

            return

        self.draw_top_hud()
        self.draw_field()
        self.draw_right_panel()
        self.draw_action_bar()
        self.draw_work_card()
        self.draw_message_bar()

        if self.shop_open:

            self.draw_shop()

    # ========================================================
    # 밭
    # ========================================================

    def draw_field(self):

        offset_x = FIELD_MARGIN
        offset_y = 90

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

        # ----------------------------------------------------
        # 집
        # 9x9 밭 아래 중앙에 별도 한 칸으로 표시한다.
        # ----------------------------------------------------

        house_x, house_y = HOUSE_POS

        px = (
            offset_x
            + house_x * CELL_SIZE
        )

        py = (
            offset_y
            + house_y * CELL_SIZE
        )

        self.canvas.create_rectangle(
            px,
            py,
            px + CELL_SIZE,
            py + CELL_SIZE,
            fill="#4c3a32",
            outline="#8a8a8a",
            width=3,
        )

        house_symbol = "H"

        if (
            self.player_x == house_x
            and
            self.player_y == house_y
        ):

            house_symbol = "P"

        self.canvas.create_text(
            px + CELL_SIZE // 2,
            py + CELL_SIZE // 2 - 7,
            text=house_symbol,
            fill="#ffffff",
            font=(
                "Consolas",
                30,
                "bold",
            ),
        )

        self.canvas.create_text(
            px + CELL_SIZE // 2,
            py + CELL_SIZE - 10,
            text="집",
            fill="#f1d58a",
            font=(
                "Malgun Gothic",
                9,
                "bold",
            ),
        )

        # ----------------------------------------------------
        # 상점
        # 9x9 밭 아래 오른쪽에 별도 한 칸으로 표시한다.
        # ----------------------------------------------------

        shop_x, shop_y = SHOP_POS

        shop_px = (
            offset_x
            + shop_x * CELL_SIZE
        )

        shop_py = (
            offset_y
            + shop_y * CELL_SIZE
        )

        self.canvas.create_rectangle(
            shop_px,
            shop_py,
            shop_px + CELL_SIZE,
            shop_py + CELL_SIZE,
            fill="#3a4550",
            outline="#8a8a8a",
            width=3,
        )

        shop_symbol = "S"

        if (
            self.player_x == shop_x
            and
            self.player_y == shop_y
        ):

            shop_symbol = "P"

        self.canvas.create_text(
            shop_px + CELL_SIZE // 2,
            shop_py + CELL_SIZE // 2 - 7,
            text=shop_symbol,
            fill="#ffffff",
            font=(
                "Consolas",
                30,
                "bold",
            ),
        )

        self.canvas.create_text(
            shop_px + CELL_SIZE // 2,
            shop_py + CELL_SIZE - 10,
            text="상점",
            fill="#b9d8f0",
            font=(
                "Malgun Gothic",
                9,
                "bold",
            ),
        )

        # ----------------------------------------------------
        # 플레이어 위치 강조 테두리
        #
        # 모든 타일과 집을 그린 뒤 마지막에 덧그려
        # 인접 칸에 테두리가 가려지지 않게 한다.
        # ----------------------------------------------------

        player_px = (
            offset_x
            + self.player_x * CELL_SIZE
        )

        player_py = (
            offset_y
            + self.player_y * CELL_SIZE
        )

        inset = 3

        self.canvas.create_rectangle(
            player_px + inset,
            player_py + inset,
            player_px + CELL_SIZE - inset,
            player_py + CELL_SIZE - inset,
            outline="#f1d58a",
            width=4,
        )

    # ========================================================
    # 메인 화면
    # ========================================================

    def draw_main_menu(self):

        center_x = (
            self.window_width // 2
        )

        self.canvas.create_text(
            center_x,
            190,
            text=GAME_TITLE,
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                34,
                "bold",
            ),
        )

        self.canvas.create_text(
            center_x,
            245,
            text="농사 생존 시뮬레이션",
            fill="#c9b77d",
            font=(
                "Malgun Gothic",
                14,
            ),
        )

        button_left = (
            center_x - 180
        )

        button_right = (
            center_x + 180
        )

        button_top = 390
        button_bottom = 460

        self.canvas.create_rectangle(
            button_left,
            button_top,
            button_right,
            button_bottom,
            fill="#313129",
            outline="#d8c48c",
            width=3,
        )

        self.canvas.create_text(
            center_x,
            (
                button_top
                + button_bottom
            ) // 2,
            text="게임 시작",
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                18,
                "bold",
            ),
        )

        self.click_regions[
            "main_start"
        ] = (
            button_left,
            button_top,
            button_right,
            button_bottom,
        )

        self.canvas.create_text(
            center_x,
            515,
            text="ENTER / SPACE / Z",
            fill="#888888",
            font=(
                "Consolas",
                11,
            ),
        )

        self.canvas.create_text(
            center_x,
            self.window_height - 75,
            text="ESC  종료",
            fill="#777777",
            font=(
                "Malgun Gothic",
                10,
            ),
        )

    # ========================================================
    # 시나리오 선택 화면
    # ========================================================

    def draw_scenario_select(self):

        center_x = (
            self.window_width // 2
        )

        self.canvas.create_text(
            center_x,
            85,
            text="시나리오 선택",
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                27,
                "bold",
            ),
        )

        self.canvas.create_text(
            center_x,
            125,
            text=(
                "각 시나리오는 서로 다른 환경과 "
                "생존 목표를 가진다."
            ),
            fill="#aaaaaa",
            font=(
                "Malgun Gothic",
                11,
            ),
        )

        card_width = min(
            760,
            self.window_width - 140
        )

        card_left = (
            center_x
            - card_width // 2
        )

        card_right = (
            center_x
            + card_width // 2
        )

        card_top = 220
        card_bottom = 550

        scenario = SCENARIOS[
            self.scenario_selected_index
        ]

        self.canvas.create_rectangle(
            card_left,
            card_top,
            card_right,
            card_bottom,
            fill="#222222",
            outline="#d8c48c",
            width=3,
        )

        # 왼쪽의 간단한 겨울 풍경 표식
        icon_x = (
            card_left + 120
        )

        icon_y = (
            card_top + 130
        )

        self.canvas.create_oval(
            icon_x - 48,
            icon_y - 48,
            icon_x + 48,
            icon_y + 48,
            fill="#26313a",
            outline="#8fa7ba",
            width=3,
        )

        self.canvas.create_text(
            icon_x,
            icon_y - 3,
            text="❄",
            fill="#dcecf7",
            font=(
                "Malgun Gothic",
                46,
                "bold",
            ),
        )

        text_x = (
            card_left + 235
        )

        self.canvas.create_text(
            text_x,
            card_top + 55,
            anchor="nw",
            text=scenario["title"],
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                23,
                "bold",
            ),
        )

        self.canvas.create_text(
            text_x,
            card_top + 100,
            anchor="nw",
            text=scenario["subtitle"],
            fill="#d8c48c",
            font=(
                "Malgun Gothic",
                13,
                "bold",
            ),
        )

        self.canvas.create_text(
            text_x,
            card_top + 145,
            anchor="nw",
            text=scenario["description"],
            width=max(
                300,
                card_right
                - text_x
                - 35
            ),
            fill="#cccccc",
            font=(
                "Malgun Gothic",
                11,
            ),
        )

        self.canvas.create_text(
            text_x,
            card_top + 235,
            anchor="nw",
            text=scenario["goal"],
            fill="#a9d6ff",
            font=(
                "Malgun Gothic",
                11,
                "bold",
            ),
        )

        self.click_regions[
            "scenario_first_winter"
        ] = (
            card_left,
            card_top,
            card_right,
            card_bottom,
        )

        start_left = (
            center_x - 150
        )

        start_right = (
            center_x + 150
        )

        start_top = 620
        start_bottom = 680

        self.canvas.create_rectangle(
            start_left,
            start_top,
            start_right,
            start_bottom,
            fill="#313129",
            outline="#d8c48c",
            width=3,
        )

        self.canvas.create_text(
            center_x,
            (
                start_top
                + start_bottom
            ) // 2,
            text="시나리오 시작",
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                15,
                "bold",
            ),
        )

        self.click_regions[
            "scenario_start"
        ] = (
            start_left,
            start_top,
            start_right,
            start_bottom,
        )

        self.canvas.create_text(
            center_x,
            730,
            text=(
                "ENTER / SPACE / Z : 시작    "
                "ESC : 메인 화면"
            ),
            fill="#888888",
            font=(
                "Malgun Gothic",
                10,
            ),
        )

        self.canvas.create_text(
            center_x,
            self.window_height - 75,
            text="현재 선택 가능한 시나리오: 1개",
            fill="#666666",
            font=(
                "Malgun Gothic",
                9,
            ),
        )

    # ========================================================
    # 시나리오 시작
    # ========================================================

    def start_scenario(
        self,
        scenario_id
    ):

        self.current_scenario_id = (
            scenario_id
        )

        self.screen_mode = "game"

        # 현재는 첫 번째 겨울 하나만 존재한다.
        # 새 시나리오를 추가할 때 여기에서
        # 시나리오별 초기 조건을 분기할 수 있다.

        self.day = 1
        self.current_time = (
            DAY_START_MINUTE
        )

        self.stamina = (
            self.max_stamina
        )

        self.player_x = (
            GRID_SIZE // 2
        )

        self.player_y = (
            GRID_SIZE // 2
        )

        self.selected_action = 0
        self.selected_crop_index = 0

        self.money = 500

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

        self.shop_open = False
        self.shop_mode = "buy"
        self.shop_selected_index = 0

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

        self.activity_log = []

        self.add_log(
            "첫 번째 겨울 시작"
        )

        self.message = (
            "《첫 번째 겨울》이 시작되었다.\\n"
            "다가오는 겨울에 대비해 농사를 준비하자.\\n"
            "집은 H, 상점은 밭 아래 오른쪽 S에 있다."
        )

        self.draw()

    # ========================================================
    # 마우스 입력
    # ========================================================

    def on_click(
        self,
        event
    ):

        x = event.x
        y = event.y

        if self.screen_mode == "main":

            region = self.click_regions.get(
                "main_start"
            )

            if (
                region is not None
                and
                self.point_in_region(
                    x,
                    y,
                    region
                )
            ):

                self.screen_mode = (
                    "scenario_select"
                )

                self.draw()

            return

        if self.screen_mode == "scenario_select":

            card = self.click_regions.get(
                "scenario_first_winter"
            )

            start = self.click_regions.get(
                "scenario_start"
            )

            if (
                card is not None
                and
                self.point_in_region(
                    x,
                    y,
                    card
                )
            ):

                self.scenario_selected_index = 0
                self.draw()

                return

            if (
                start is not None
                and
                self.point_in_region(
                    x,
                    y,
                    start
                )
            ):

                scenario = SCENARIOS[
                    self.scenario_selected_index
                ]

                self.start_scenario(
                    scenario["id"]
                )

    @staticmethod
    def point_in_region(
        x,
        y,
        region
    ):

        left, top, right, bottom = (
            region
        )

        return (
            left <= x <= right
            and
            top <= y <= bottom
        )

    # ========================================================
    # 상단 HUD
    # ========================================================

    def draw_top_hud(self):

        left = FIELD_MARGIN
        right = self.window_width - 25
        top = 18
        bottom = 68

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="#222222",
            outline="#666666",
            width=2,
        )

        self.canvas.create_text(
            left + 18,
            top + 13,
            anchor="nw",
            text=(
                f"{self.day}일째   "
                f"{self.format_time()}"
            ),
            fill="#f1d58a",
            font=(
                "Malgun Gothic",
                14,
                "bold",
            ),
        )

        self.canvas.create_text(
            right - 18,
            top + 13,
            anchor="ne",
            text=f"{self.money:,} G",
            fill="#f1d58a",
            font=(
                "Malgun Gothic",
                14,
                "bold",
            ),
        )

        stamina_text_x = (
            left + 245
        )

        self.canvas.create_text(
            stamina_text_x,
            top + 13,
            anchor="nw",
            text=(
                f"체력 {self.stamina}/{self.max_stamina}"
            ),
            fill="#dddddd",
            font=(
                "Malgun Gothic",
                11,
                "bold",
            ),
        )

        bar_x = (
            stamina_text_x + 125
        )

        bar_y = (
            top + 15
        )

        bar_width = 220
        bar_height = 18

        self.canvas.create_rectangle(
            bar_x,
            bar_y,
            bar_x + bar_width,
            bar_y + bar_height,
            fill="#333333",
            outline="#777777",
        )

        stamina_ratio = (
            self.stamina
            / self.max_stamina
        )

        if stamina_ratio > 0.6:
            stamina_color = "#5eaf66"

        elif stamina_ratio > 0.3:
            stamina_color = "#d4ad4d"

        else:
            stamina_color = "#c95a5a"

        self.canvas.create_rectangle(
            bar_x,
            bar_y,
            bar_x + (
                bar_width
                * stamina_ratio
            ),
            bar_y + bar_height,
            fill=stamina_color,
            outline="",
        )

    # ========================================================
    # 오른쪽 패널
    # ========================================================

    def draw_right_panel(self):

        panel_x = (
            FIELD_MARGIN
            + FIELD_PIXEL_SIZE
            + 35
        )

        panel_right = (
            self.window_width
            - 25
        )

        top = 90
        bottom = min(
            self.window_height - 220,
            735
        )

        # ----------------------------------------------------
        # 현재 칸
        # ----------------------------------------------------

        current_bottom = (
            top + 225
        )

        self.canvas.create_rectangle(
            panel_x,
            top,
            panel_right,
            current_bottom,
            fill="#202020",
            outline="#666666",
            width=2,
        )

        self.canvas.create_text(
            panel_x + 14,
            top + 12,
            anchor="nw",
            text="[현재 칸]",
            fill="#a9d6ff",
            font=(
                "Malgun Gothic",
                12,
                "bold",
            ),
        )

        tile = (
            self.current_tile()
        )

        tile_text = (
            self.get_tile_info(
                tile
            )
        )

        # "[현재 칸]" 제목은 별도 출력하므로 제거
        if tile_text.startswith(
            "[현재 칸]\\n"
        ):
            tile_text = (
                tile_text[len("[현재 칸]\\n"):]
            )

        self.canvas.create_text(
            panel_x + 14,
            top + 50,
            anchor="nw",
            text=tile_text,
            width=max(
                220,
                panel_right
                - panel_x
                - 28
            ),
            fill="#dddddd",
            font=(
                "Malgun Gothic",
                11,
            ),
        )

        # ----------------------------------------------------
        # 최근 기록
        # ----------------------------------------------------

        log_top = (
            current_bottom + 15
        )

        self.canvas.create_rectangle(
            panel_x,
            log_top,
            panel_right,
            bottom,
            fill="#181818",
            outline="#666666",
            width=2,
        )

        self.canvas.create_text(
            panel_x + 14,
            log_top + 12,
            anchor="nw",
            text="[최근 기록]",
            fill="#d8e6c3",
            font=(
                "Malgun Gothic",
                12,
                "bold",
            ),
        )

        recent = (
            self.activity_log[-8:]
        )

        log_text = (
            "\n".join(
                reversed(
                    recent
                )
            )
        )

        self.canvas.create_text(
            panel_x + 14,
            log_top + 48,
            anchor="nw",
            text=log_text,
            width=max(
                220,
                panel_right
                - panel_x
                - 28
            ),
            fill="#bbbbbb",
            font=(
                "Malgun Gothic",
                9,
            ),
        )

    # ========================================================
    # 작업 선택 바
    # ========================================================

    def draw_action_bar(self):

        left = FIELD_MARGIN
        right = (
            FIELD_MARGIN
            + FIELD_PIXEL_SIZE
        )

        top = 825
        bottom = 895

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="#202020",
            outline="#666666",
            width=2,
        )

        section_width = (
            (right - left)
            / 4
        )

        for index, action in enumerate(
            self.actions
        ):

            x1 = (
                left
                + index * section_width
            )

            x2 = (
                x1
                + section_width
            )

            selected = (
                index
                == self.selected_action
            )

            if selected:
                fill = "#4a4a36"
                outline = "#d8c48c"
                text_color = "#ffffff"

            else:
                fill = "#2a2a2a"
                outline = "#555555"
                text_color = "#bbbbbb"

            self.canvas.create_rectangle(
                x1 + 4,
                top + 7,
                x2 - 4,
                bottom - 7,
                fill=fill,
                outline=outline,
                width=2,
            )

            self.canvas.create_text(
                (
                    x1 + x2
                ) / 2,
                (
                    top + bottom
                ) / 2,
                text=(
                    f"{index + 1} {action}"
                ),
                fill=text_color,
                font=(
                    "Malgun Gothic",
                    10,
                    "bold",
                ),
            )

    # ========================================================
    # 현재 작업 카드
    # ========================================================

    def draw_work_card(self):

        left = (
            FIELD_MARGIN
            + FIELD_PIXEL_SIZE
            + 35
        )

        right = (
            self.window_width
            - 25
        )

        top = 825
        bottom = 895

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="#202020",
            outline="#666666",
            width=2,
        )

        action = (
            self.actions[
                self.selected_action
            ]
        )

        # ----------------------------------------------------
        # 아이콘 영역
        # ----------------------------------------------------

        icon_center_x = (
            left + 48
        )

        icon_center_y = (
            top + 35
        )

        if self.selected_action == 0:

            self.draw_plow_icon(
                icon_center_x,
                icon_center_y,
            )

            title = "쟁기질"

            detail = (
                f"{TIME_PLOW}분 / "
                f"체력 {STAMINA_PLOW}"
            )

        elif self.selected_action == 1:

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

            self.draw_crop_icon(
                icon_center_x,
                icon_center_y,
                crop_key,
            )

            title = (
                f"씨 뿌리기 · {crop.name} × {seed_count}"
            )

            detail = (
                f"Q / E 씨앗 변경    "
                f"{TIME_PLANT}분 / "
                f"체력 {STAMINA_PLANT}"
            )

        elif self.selected_action == 2:

            self.draw_watering_icon(
                icon_center_x,
                icon_center_y,
            )

            title = "물주기"

            detail = (
                f"{TIME_WATER}분 / "
                f"체력 {STAMINA_WATER}"
            )

        else:

            self.draw_harvest_icon(
                icon_center_x,
                icon_center_y,
            )

            title = "수확"

            detail = (
                f"{TIME_HARVEST}분 / "
                f"체력 {STAMINA_HARVEST}"
            )

        # ----------------------------------------------------
        # 텍스트 영역
        # ----------------------------------------------------

        text_x = (
            left + 92
        )

        self.canvas.create_text(
            text_x,
            top + 16,
            anchor="nw",
            text=title,
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                12,
                "bold",
            ),
        )

        self.canvas.create_text(
            text_x,
            top + 44,
            anchor="nw",
            text=detail,
            fill="#d3c9a3",
            font=(
                "Malgun Gothic",
                9,
            ),
        )

    # ========================================================
    # 작업 카드 아이콘
    # ========================================================

    def draw_plow_icon(
        self,
        cx,
        cy
    ):

        # 손잡이
        self.canvas.create_line(
            cx - 15,
            cy - 18,
            cx + 8,
            cy + 10,
            fill="#c89b6b",
            width=5,
        )

        # 쟁기 몸체
        self.canvas.create_line(
            cx + 7,
            cy + 8,
            cx + 18,
            cy + 16,
            fill="#9ca3aa",
            width=5,
        )

        # 날
        self.canvas.create_polygon(
            cx + 12,
            cy + 12,
            cx + 23,
            cy + 14,
            cx + 17,
            cy + 23,
            cx + 4,
            cy + 15,
            fill="#c9ced3",
            outline="#eeeeee",
        )

        # 손잡이 끝
        self.canvas.create_line(
            cx - 18,
            cy - 21,
            cx - 8,
            cy - 23,
            fill="#d4ad7d",
            width=4,
        )

    def draw_watering_icon(
        self,
        cx,
        cy
    ):

        # 물뿌리개 몸체
        self.canvas.create_rectangle(
            cx - 16,
            cy - 8,
            cx + 10,
            cy + 15,
            fill="#657f8f",
            outline="#b8ced8",
            width=2,
        )

        # 손잡이
        self.canvas.create_arc(
            cx - 10,
            cy - 21,
            cx + 12,
            cy + 2,
            start=10,
            extent=160,
            style="arc",
            outline="#b8ced8",
            width=3,
        )

        # 주둥이
        self.canvas.create_polygon(
            cx + 10,
            cy - 3,
            cx + 27,
            cy - 12,
            cx + 29,
            cy - 7,
            cx + 12,
            cy + 3,
            fill="#657f8f",
            outline="#b8ced8",
        )

        # 물방울
        for dx, dy in (
            (27, 2),
            (22, 8),
            (30, 10),
        ):
            self.canvas.create_oval(
                cx + dx - 2,
                cy + dy - 3,
                cx + dx + 2,
                cy + dy + 3,
                fill="#73b7dd",
                outline="",
            )

    def draw_harvest_icon(
        self,
        cx,
        cy
    ):

        # 낫 손잡이
        self.canvas.create_line(
            cx - 13,
            cy + 20,
            cx + 4,
            cy - 3,
            fill="#b68150",
            width=5,
        )

        # 낫 날
        self.canvas.create_arc(
            cx - 2,
            cy - 24,
            cx + 28,
            cy + 8,
            start=80,
            extent=185,
            style="arc",
            outline="#d7dde2",
            width=5,
        )

        self.canvas.create_line(
            cx + 4,
            cy - 3,
            cx + 11,
            cy - 10,
            fill="#d7dde2",
            width=4,
        )

    def draw_crop_icon(
        self,
        cx,
        cy,
        crop_key
    ):

        if crop_key == "wheat":

            # 줄기
            self.canvas.create_line(
                cx,
                cy + 20,
                cx,
                cy - 20,
                fill="#c9a64a",
                width=3,
            )

            # 이삭
            for offset_y in (
                -14,
                -8,
                -2,
                4,
            ):
                self.canvas.create_oval(
                    cx - 10,
                    cy + offset_y - 4,
                    cx - 1,
                    cy + offset_y + 3,
                    fill="#d9b85b",
                    outline="",
                )

                self.canvas.create_oval(
                    cx + 1,
                    cy + offset_y - 4,
                    cx + 10,
                    cy + offset_y + 3,
                    fill="#d9b85b",
                    outline="",
                )

        elif crop_key == "carrot":

            # 잎
            for dx in (
                -8,
                0,
                8,
            ):
                self.canvas.create_line(
                    cx,
                    cy - 7,
                    cx + dx,
                    cy - 22,
                    fill="#6fa35f",
                    width=4,
                )

            # 뿌리
            self.canvas.create_polygon(
                cx - 11,
                cy - 8,
                cx + 11,
                cy - 8,
                cx + 4,
                cy + 20,
                cx,
                cy + 25,
                cx - 4,
                cy + 20,
                fill="#d97b35",
                outline="#f0a15c",
            )

            # 당근 결
            self.canvas.create_line(
                cx - 6,
                cy + 2,
                cx + 3,
                cy + 1,
                fill="#aa5826",
                width=2,
            )

            self.canvas.create_line(
                cx - 3,
                cy + 10,
                cx + 5,
                cy + 9,
                fill="#aa5826",
                width=2,
            )

        else:

            # 감자
            potato_specs = (
                (-10, -3, 10, 15),
                (3, -10, 21, 8),
                (-20, -12, -3, 5),
            )

            for x1, y1, x2, y2 in potato_specs:

                self.canvas.create_oval(
                    cx + x1,
                    cy + y1,
                    cx + x2,
                    cy + y2,
                    fill="#9a7047",
                    outline="#c89b6b",
                    width=2,
                )

            # 감자 눈
            for dx, dy in (
                (-4, 3),
                (11, -2),
                (-11, -5),
            ):
                self.canvas.create_oval(
                    cx + dx - 1,
                    cy + dy - 1,
                    cx + dx + 1,
                    cy + dy + 1,
                    fill="#60452f",
                    outline="",
                )

    # ========================================================
    # 하단 메시지 바
    # ========================================================

    def draw_message_bar(self):

        left = FIELD_MARGIN
        right = (
            self.window_width
            - 25
        )

        top = 908
        bottom = (
            self.window_height
            - 18
        )

        if bottom <= top:
            return

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill="#252525",
            outline="#666666",
            width=2,
        )

        self.canvas.create_text(
            left + 14,
            top + 10,
            anchor="nw",
            text=self.message,
            width=max(
                300,
                right - left - 28
            ),
            fill="#ffffff",
            font=(
                "Malgun Gothic",
                10,
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

        if tile is None:

            if (
                (self.player_x, self.player_y)
                == HOUSE_POS
            ):

                result += (
                    "장소: 집\n"
                    "N / Z / SPACE / ENTER : 잠자기"
                )

            elif (
                (self.player_x, self.player_y)
                == SHOP_POS
            ):

                result += (
                    "장소: 상점\n"
                    "B / Z / SPACE / ENTER : 거래"
                )

            return result

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