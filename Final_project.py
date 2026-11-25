
import random
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from ultralytics import YOLO

import poker_equity as poker
from poker_equity_web import (
    estimate_equity,
    evaluate_visible_hand,
    get_hand_features,
    get_recommendation,
)


# ==================================================
# 1. 기본 설정
# ==================================================

ROOT = Path(__file__).resolve().parent
ASSET_DIR = ROOT / "assets"

MODEL_PATH = ROOT / "best.pt"

CONFIDENCE = 0.25
IMAGE_SIZE = 1280
IOU = 0.5

DEFAULT_SPLIT_Y = 0.60

DEFAULT_OPPONENTS = 1
DEFAULT_TRIALS = 1400


# ==================================================
# 2. 카드 표시용 상수
# ==================================================

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9",
         "10", "J", "Q", "K", "A"]

SUITS = ["s", "h", "d", "c"]

SUIT_SYMBOL = {
    "s": "♠",
    "h": "♥",
    "d": "♦",
    "c": "♣"
}

SUIT_COLOR = {
    "s": "#20252d",
    "c": "#20252d",
    "h": "#dc3545",
    "d": "#dc3545"
}

DECK = [
    rank + suit
    for rank in RANKS
    for suit in SUITS
]


# ==================================================
# 3. Streamlit 페이지 설정
# ==================================================

st.set_page_config(
    page_title="Poker Simulator | 승률 계산기",
    page_icon="♠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ==================================================
# 4. 화면 스타일
# ==================================================

st.markdown("""
<style>
    @import url(
        'https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap'
    );

    html, body, [class*="css"] {
        font-family: 'Noto Sans KR', sans-serif;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1 {
        font-size: 2.05rem !important;
        font-weight: 800 !important;
        color: #202938;
    }

    h2, h3 {
        color: #202938;
        font-weight: 750 !important;
    }

    .subtitle {
        color: #64748b;
        font-size: .88rem;
    }

    .section-title {
        font-size: 1.22rem;
        font-weight: 750;
        color: #202938;
        margin: .2rem 0 .65rem;
    }

    .hint {
        background: #eef5ff;
        border-radius: 9px;
        padding: 13px 15px;
        color: #2862b9;
        font-size: .85rem;
        line-height: 1.6;
    }

    .metric-label {
        color: #64748b;
        font-size: .82rem;
    }

    .metric-value {
        color: #182230;
        font-size: 2.2rem;
        font-weight: 750;
    }

    .advice {
        background: #effaf5;
        color: #08784d;
        border-radius: 9px;
        padding: 13px 15px;
        font-weight: 650;
        font-size: .9rem;
    }

    .grade {
        color: #344054;
        font-size: 1.05rem;
        font-weight: 700;
    }

    .small-muted {
        color: #98a2b3;
        font-size: .75rem;
    }

    .playing-card {
        width: 66px;
        height: 96px;
        border: 1px solid #d7dce2;
        border-radius: 7px;
        background: white;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 7px;
        font-size: 19px;
    }

    .playing-card span {
        font-size: 30px;
        align-self: center;
    }

    .card-back {
        width: 66px;
        height: 96px;
        border-radius: 7px;
        border: 2px solid white;
        outline: 1px solid #ddd;
        background: #d85a62;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 34px;
    }

    hr {
        border-color: #e5e7eb;
    }

    @media (max-width: 800px) {
        .block-container {
            padding: 1rem;
        }

        h1 {
            font-size: 1.5rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# ==================================================
# 5. 카드 이미지 표시 함수
# ==================================================

def card_image_name(card):
    return f"{card}.png"


def render_card(card, width=78):

    path = ASSET_DIR / card_image_name(card)

    if path.exists():

        st.image(str(path), width=width)

    else:

        suit = SUIT_SYMBOL[card[-1]]
        color = SUIT_COLOR[card[-1]]

        st.markdown(
            f'<div class="playing-card" style="color:{color}">'
            f'<b>{card[:-1]}</b><span>{suit}</span></div>',
            unsafe_allow_html=True
        )


def render_back(width=78):

    path = ASSET_DIR / "back.png"

    if path.exists():

        st.image(str(path), width=width)

    else:

        st.markdown(
            '<div class="card-back">♠</div>',
            unsafe_allow_html=True
        )


def card_caption(card):
    return f"{card[:-1]}{SUIT_SYMBOL[card[-1]]}"


# ==================================================
# 6. YOLO 모델 불러오기
# ==================================================

@st.cache_resource
def load_model():

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"YOLO 모델 파일을 찾을 수 없습니다: {MODEL_PATH}"
        )

    model = YOLO(str(MODEL_PATH))

    return model


# ==================================================
# 7. 세로 기준선 그리기
# ==================================================

def draw_split_line(image, split_y):

    height, width = image.shape[:2]

    split_pixel = int(height * split_y)

    # 기준선
    cv2.line(
        image,
        (0, split_pixel),
        (width, split_pixel),
        (0, 0, 255),
        3
    )

    # 영역 이름
    cv2.putText(
        image,
        "BOARD AREA",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 0, 0),
        2
    )

    cv2.putText(
        image,
        "HAND AREA",
        (20, split_pixel + 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 165, 255),
        2
    )

    return image


# ==================================================
# 8. 같은 카드 중복 검출 제거
# ==================================================

def remove_duplicates(cards):

    best_cards = {}

    for card in cards:

        name = card["name"]

        if (
            name not in best_cards
            or card["confidence"] >
            best_cards[name]["confidence"]
        ):

            best_cards[name] = card

    # 왼쪽에서 오른쪽 순서로 정렬
    return sorted(
        best_cards.values(),
        key=lambda card: card["cx"]
    )


# ==================================================
# 9. YOLO 카드 인식 및 세로 좌표 분류
# ==================================================

def detect_cards(model, image, split_y):

    height, width = image.shape[:2]

    results = model.predict(
        source=image,
        imgsz=IMAGE_SIZE,
        conf=CONFIDENCE,
        iou=IOU,
        verbose=False
    )

    hand_cards = []
    board_cards = []

    debug_image = draw_split_line(
        image.copy(),
        split_y
    )

    for result in results:

        for box in result.boxes:

            # 클래스 번호
            class_id = int(box.cls[0].item())

            # 카드 클래스 이름
            raw_name = result.names[class_id]

            # poker_equity.py 표기법으로 변환
            card_name = poker.norm(raw_name)

            # 신뢰도
            confidence = float(box.conf[0].item())

            # 바운딩 박스
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            # 카드 중심 좌표
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            # 세로 비율 좌표
            cy = center_y / height

            # 가로 좌표는 표시 및 정렬용
            cx = center_x / width

            # 카드 정보
            card = {
                "name": card_name,
                "confidence": confidence,
                "cx": cx,
                "cy": cy
            }

            # --------------------------------
            # 세로 좌표만으로 분류
            # --------------------------------

            if cy < split_y:

                board_cards.append(card)
                color = (255, 0, 0)

            else:

                hand_cards.append(card)
                color = (0, 165, 255)

            # 바운딩 박스 표시
            cv2.rectangle(
                debug_image,
                (int(x1), int(y1)),
                (int(x2), int(y2)),
                color,
                2
            )

            # 카드 이름 및 신뢰도 표시
            cv2.putText(
                debug_image,
                f"{card_name} {confidence:.2f}",
                (int(x1), max(int(y1) - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

    # 중복 제거
    hand_cards = remove_duplicates(hand_cards)
    board_cards = remove_duplicates(board_cards)

    hand_names = [
        card["name"] for card in hand_cards
    ]

    board_names = [
        card["name"] for card in board_cards
    ]

    return hand_names, board_names, debug_image


# ==================================================
# 10. 카드 개수 및 중복 검사
# ==================================================

def validate_cards(hand_cards, board_cards):

    if len(hand_cards) != 2:

        raise ValueError(
            f"내 카드가 2장이 아닙니다. "
            f"현재 {len(hand_cards)}장 인식"
        )

    if len(board_cards) not in [0, 3, 4, 5]:

        raise ValueError(
            f"커뮤니티 카드 개수가 올바르지 않습니다. "
            f"현재 {len(board_cards)}장 인식"
        )

    all_cards = hand_cards + board_cards

    if len(set(all_cards)) != len(all_cards):

        raise ValueError(
            "동일한 카드가 중복 인식되었습니다."
        )


# ==================================================
# 11. 세션 상태
# ==================================================

if "hand_cards" not in st.session_state:
    st.session_state.hand_cards = []

if "board_cards" not in st.session_state:
    st.session_state.board_cards = []

if "debug_image" not in st.session_state:
    st.session_state.debug_image = None

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

if "opponents" not in st.session_state:
    st.session_state.opponents = DEFAULT_OPPONENTS


# ==================================================
# 12. 헤더
# ==================================================

st.markdown(
    "# ♠ Poker Simulator (승률 계산기)"
)

st.markdown(
    '<div class="subtitle">'
    'YOLO 카드 인식과 텍사스 홀덤 승률 분석을 결합한 프로그램입니다.'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("---")


# ==================================================
# 13. 화면 구성
# ==================================================

left, right = st.columns(
    [0.9, 1.1],
    gap="large"
)


# ==================================================
# 14. 왼쪽: 사진 업로드 및 YOLO 설정
# ==================================================

with left:

    st.markdown(
        '<div class="section-title">'
        '📷 포커 사진 촬영'
        '</div>',
        unsafe_allow_html=True
    )

    uploaded = st.camera_input(
        "웹캠으로 포커 테이블을 촬영하세요.",
        key="card_camera"
    )

    if uploaded is not None:

        file_bytes = np.frombuffer(
            uploaded.getvalue(),
            np.uint8
        )

        image = cv2.imdecode(
            file_bytes,
            cv2.IMREAD_COLOR
        )

        if image is not None:

            rgb_image = cv2.cvtColor(
                image,
                cv2.COLOR_BGR2RGB
            )

            st.image(
                rgb_image,
                caption="업로드한 포커 사진",
                use_container_width=True
            )

            st.caption(
                f"사진 해상도: {image.shape[1]} × {image.shape[0]}"
            )

            st.markdown("---")

            # 세로 기준선 조절
            st.markdown(
                '<div class="section-title">'
                '📏 카드 분류 기준선'
                '</div>',
                unsafe_allow_html=True
            )

            split_y = st.slider(
                "기준선 위치 (%)",
                min_value=30,
                max_value=85,
                value=int(DEFAULT_SPLIT_Y * 100),
                step=1
            )

            split_y = split_y / 100

            st.info(
                f"현재 기준선: 사진 높이의 {split_y:.0%}\n\n"
                "기준선 위쪽은 커뮤니티 카드, "
                "아래쪽은 내 카드로 분류합니다."
            )

            # YOLO 실행
            if st.button(
                "🔍 YOLO 카드 인식 시작",
                use_container_width=True,
                type="primary"
            ):

                try:

                    with st.spinner(
                        "YOLO가 카드를 인식하고 있습니다..."
                    ):

                        model = load_model()

                        hand, board, debug = detect_cards(
                            model,
                            image,
                            split_y
                        )

                        st.session_state.hand_cards = hand
                        st.session_state.board_cards = board
                        st.session_state.debug_image = debug

                        # 새로운 인식 결과이므로 이전 분석 결과 초기화
                        st.session_state.analysis_result = None

                    st.success("카드 인식이 완료되었습니다.")

                except Exception as e:

                    st.error(f"인식 오류: {e}")

        else:

            st.error("이미지를 읽을 수 없습니다.")

    else:

        st.info("포커 사진을 업로드하면 YOLO 카드 인식을 시작할 수 있습니다.")


# ==================================================
# 15. 오른쪽: 카드 및 승률 분석
# ==================================================

with right:

    st.markdown(
        '<div class="section-title">🎴 인식된 카드</div>',
        unsafe_allow_html=True
    )

    hand = st.session_state.hand_cards
    board = st.session_state.board_cards

    # ----------------------------------------------
    # 내 카드 표시
    # ----------------------------------------------

    st.markdown("**내 카드**")

    if hand:

        cols = st.columns(2)

        for i, card in enumerate(hand):

            with cols[i]:

                render_card(card, 78)
                st.caption(card_caption(card))

    else:

        st.caption("인식된 내 카드가 없습니다.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------------------------------------
    # 커뮤니티 카드 표시
    # ----------------------------------------------

    st.markdown("**커뮤니티 카드**")

    board_cols = st.columns(5)

    for i, col in enumerate(board_cols):

        with col:

            if i < len(board):

                render_card(board[i], 70)
                st.caption(card_caption(board[i]))

            else:

                render_back(70)
                st.caption("미공개")

    st.markdown("---")

    # ----------------------------------------------
    # YOLO 디버깅 이미지
    # ----------------------------------------------

    if st.session_state.debug_image is not None:

        with st.expander("YOLO 인식 및 기준선 확인"):

            debug_rgb = cv2.cvtColor(
                st.session_state.debug_image,
                cv2.COLOR_BGR2RGB
            )

            st.image(
                debug_rgb,
                caption="빨간색: 기준선 / 파란색: 커뮤니티 / 주황색: 내 카드",
                use_container_width=True
            )

    # ----------------------------------------------
    # 상대 플레이어 수
    # ----------------------------------------------

    opponents = st.slider(
        "상대 플레이어 수",
        min_value=1,
        max_value=9,
        value=int(st.session_state.opponents)
    )

    st.session_state.opponents = opponents

    st.caption(
        "상대방의 카드는 남은 카드에서 무작위로 생성합니다."
    )

    # ----------------------------------------------
    # 승률 계산 버튼
    # ----------------------------------------------

    if st.button(
        "📊 포커 승률 계산",
        use_container_width=True,
        type="primary"
    ):

        try:

            validate_cards(hand, board)

            with st.spinner("승률 계산 중..."):

                equity = estimate_equity(
                    hand,
                    board,
                    opponents=opponents,
                    trials=DEFAULT_TRIALS
                )

                current_hand = evaluate_visible_hand(
                    hand,
                    board
                )

                grade, advice_text = get_recommendation(
                    equity,
                    opponents
                )

                hand_features = get_hand_features(hand)

                st.session_state.analysis_result = {
                    "equity": equity,
                    "current_hand": current_hand,
                    "grade": grade,
                    "advice": advice_text,
                    "features": hand_features
                }

        except Exception as e:

            st.session_state.analysis_result = None

            st.error(f"분석할 수 없습니다: {e}")

    # ----------------------------------------------
    # 분석 결과 표시
    # ----------------------------------------------

    result = st.session_state.analysis_result

    if result is not None:

        st.markdown("---")

        st.markdown(
            '<div class="section-title">승리 확률</div>',
            unsafe_allow_html=True
        )

        equity = result["equity"]

        st.markdown(
            '<div class="metric-label">'
            '예상 승률 (무승부는 0.5승 반영)'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="metric-value">{equity:.1%}</div>',
            unsafe_allow_html=True
        )

        st.progress(
            float(max(0.0, min(1.0, equity)))
        )

        st.caption(
            f"{opponents}명 상대 · "
            f"몬테카를로 시뮬레이션 {DEFAULT_TRIALS:,}회"
        )

        # 족보 및 카드 평가
        st.markdown("---")

        st.markdown("**내 카드 평가**")

        st.markdown(
            f'<div class="grade">{result["grade"]}</div>',
            unsafe_allow_html=True
        )

        st.caption(
            f"카드 특징: {result['features']}"
        )

        st.caption(
            f"현재 족보: {result['current_hand']}"
        )

        # 추천 행동
        st.markdown(
            '<div class="section-title">추천 행동</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            f'<div class="advice">👉 {result["advice"]}</div>',
            unsafe_allow_html=True
        )


# ==================================================
# 16. 하단 안내
# ==================================================

st.markdown("---")

st.caption(
    "※ 승률은 YOLO가 인식한 내 카드와 공개된 커뮤니티 카드를 "
    "기반으로 계산합니다. "
    "상대 카드 및 남은 커뮤니티 카드는 무작위로 생성합니다."
)

st.caption(
    "※ 본 프로그램은 확률 기반 의사결정 보조 도구이며, "
    "실제 게임 결과를 보장하지 않습니다."
)
