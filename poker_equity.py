import random
import itertools
import re
from collections import Counter

# ---------------- 설정 ----------------
NUM_OPPONENTS = 1     # 상대 인원 (패는 모름 → 랜덤으로 가정)
ITERATIONS = 20000    # 시뮬레이션 횟수
MIN_CONF = 0.25        #YOLO 인식 결과 중 이 신뢰도 미만은 무시

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
SUITS = "shdc"   
DECK = [r + s for r in RANKS for s in SUITS]
VALUE = {r: i + 2 for i, r in enumerate(RANKS)}

HAND_NAMES = [
    "하이카드", "원페어", "투페어", "트리플", "스트레이트",
    "플러시", "풀하우스", "포카드", "스트레이트 플러시", "로열 플러시",
]

# 보드(커뮤니티 카드) 장수 → 게임 진행 단계
STAGE_NAMES = {0: "프리플랍", 3: "플랍", 4: "턴", 5: "리버"}

# "ace of spades" 같은 이름 표기를 변환하기 위한 표
_RANK_WORDS = {
    "ACE": "A", "KING": "K", "QUEEN": "Q", "JACK": "J", "TEN": "10",
    "NINE": "9", "EIGHT": "8", "SEVEN": "7", "SIX": "6",
    "FIVE": "5", "FOUR": "4", "THREE": "3", "TWO": "2",
}
_SUIT_WORDS = {
    "SPADES": "S", "SPADE": "S", "HEARTS": "H", "HEART": "H",
    "DIAMONDS": "D", "DIAMOND": "D", "CLUBS": "C", "CLUB": "C",
}
_CARD_RE = re.compile(
    r"(10|[2-9]|[AKQJT]|" + "|".join(_RANK_WORDS) + r")"
    r"\s*(?:OF)?\s*"
    r"(" + "|".join(_SUIT_WORDS) + r"|[SHDC])"
)

def norm(card):
    """[수정] YOLO가 넘겨준 카드 표기를 덱 표기("As", "10h")와 맞춤.
    앞(숫자/문자)은 대문자, 뒤(무늬)는 소문자로 통일, T는 10으로, "ace of spades" 같은 이름도 변환."""
    text = str(card).strip().upper().replace("_", " ").replace("-", " ")
    m = _CARD_RE.fullmatch(text)
    if not m:
        return text                     # 알 수 없는 표기는 그대로 → 검증 단계에서 걸러짐
    rank, suit = m.group(1), m.group(2)
    rank = "10" if rank == "T" else _RANK_WORDS.get(rank, rank)
    suit = _SUIT_WORDS.get(suit, suit)
    return rank + suit.lower()          

def rank5(cards):
    """카드 5장의 족보를 (족보번호, 키커...) 튜플로 반환. 튜플이 클수록 강한 패."""
    vals = sorted((VALUE[c[:-1]] for c in cards), reverse=True)
    is_flush = len({c[-1] for c in cards}) == 1

    # 스트레이트 판정 (A-2-3-4-5 도 인정)
    straight_high = 0
    uniq = sorted(set(vals), reverse=True)
    if len(uniq) == 5:
        if uniq[0] - uniq[4] == 4:
            straight_high = uniq[0]
        elif uniq == [14, 5, 4, 3, 2]:
            straight_high = 5

    # 같은 숫자 묶음: (개수, 숫자) 큰 순서
    groups = sorted(Counter(vals).items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
    counts = [cnt for _, cnt in groups]
    ordered = [v for v, _ in groups]

    if is_flush and straight_high == 14:
        return (9,)                      # 로열 플러시
    if is_flush and straight_high:
        return (8, straight_high)        # 스트레이트 플러시
    if counts == [4, 1]:
        return (7, *ordered)             # 포카드
    if counts == [3, 2]:
        return (6, *ordered)             # 풀하우스
    if is_flush:
        return (5, *vals)                # 플러시
    if straight_high:
        return (4, straight_high)        # 스트레이트
    if counts == [3, 1, 1]:
        return (3, *ordered)             # 트리플
    if counts == [2, 2, 1]:
        return (2, *ordered)             # 투페어
    if counts == [2, 1, 1, 1]:
        return (1, *ordered)             # 원페어
    return (0, *vals)                    # 하이카드


def best_rank(cards):
    """5장 이상이면 그중 가장 강한 5장 조합의 족보를 반환 (5장이면 그대로)."""
    return max(rank5(combo) for combo in itertools.combinations(cards, 5))


# ---------------- 승률 계산 ----------------
# board 인자 추가. 커뮤니티 카드 0/3/4/5장을 받아서 남은 카드만 랜덤으로 뽑음
def my_win_rate(my_cards, board=(), iterations=ITERATIONS, num_opponents=NUM_OPPONENTS):
    """내 카드 2장 + 지금까지 공개된 커뮤니티 카드(0/3/4/5장)를 알고,
    남은 커뮤니티 카드와 상대 패를 랜덤으로 뽑아 승률을 추정.
    (보드가 5장이면 남은 건 상대 패뿐이므로 리버 승률이 됨)"""
    my_cards, board = list(my_cards), list(board)
    known = set(my_cards) | set(board)               
    rest = [c for c in DECK if c not in known]
    need_board = 5 - len(board)                      

    score = 0.0
    for _ in range(iterations):
        #기존: 항상 3장 고정 → 이제 (남은 보드 장수 + 상대 패)만큼 뽑음
        draw = random.sample(rest, need_board + 2 * num_opponents)
        full_board = board + draw[:need_board]       
        opp_cards = draw[need_board:]                

        mine = best_rank(my_cards + full_board)
        best_opp = max(
            best_rank(opp_cards[2 * i: 2 * i + 2] + full_board)   
            for i in range(num_opponents)
        )
        if mine > best_opp:
            score += 1          # 승리
        elif mine == best_opp:
            score += 0.5        # 무승부는 절반으로 계산
    return score / iterations


# [수정] board 인자 추가
def describe_hand(my_cards, board=()):
    """내 카드의 특징을 한 줄로 설명. 보드가 3장 이상이면 현재 만들어진 족보도 표시."""
    r1, s1 = my_cards[0][:-1], my_cards[0][-1]
    r2, s2 = my_cards[1][:-1], my_cards[1][-1]
    v1, v2 = VALUE[r1], VALUE[r2]
    tags = []
    if v1 == v2:
        tags.append("포켓 페어")
    if s1 == s2:
        tags.append("같은 무늬(플러시 가능성)")
    if v1 != v2 and abs(v1 - v2) <= 2:
        tags.append("숫자가 이어짐(스트레이트 가능성)")
    if max(v1, v2) >= 11:
        tags.append("높은 카드 포함")
    text = ", ".join(tags) if tags else "특별한 조합 없음"

    #보드가 3장 이상이면 지금 만들어진 족보 표시
    if len(board) >= 3:
        made = HAND_NAMES[best_rank(list(my_cards) + list(board))[0]]
        text += f" / 현재 족보: {made}"
    return text


def advice(rate, num_opponents=NUM_OPPONENTS):
    """승률을 '공평한 몫(1/전체 인원)'과 비교해서 카드 평가와 행동 추천을 반환."""
    fair = 1 / (num_opponents + 1)
    ratio = rate / fair

    if ratio >= 1.4:
        return "매우 좋은 카드", "적극적으로 베팅/레이즈하세요."
    if ratio >= 1.1:
        return "좋은 카드", "계속 게임하세요 (콜 또는 가벼운 베팅)."
    if ratio >= 0.9:
        return "보통 카드", "신중하게 계속하세요. 큰 베팅이 들어오면 포기도 고려하세요."
    if ratio >= 0.7:
        return "약한 카드", "되도록 포기하세요. 공짜로 볼 수 있을 때만 계속하세요."
    return "매우 약한 카드", "포기(폴드)를 추천합니다."


# ---------------- 분석 진입 함수 ----------------
# board_cards, num_opponents, iterations, verbose 인자 추가
def analyze(my_cards, board_cards=(), num_opponents=NUM_OPPONENTS,
            iterations=ITERATIONS, verbose=True):
    """내 카드 2장(예: ["As", "Kh"])과 커뮤니티 카드(0/3/4/5장)를 받아 평가.
    결과는 출력하고 dict로도 반환 (웹 화면 등에서 바로 쓸 수 있게)."""
    my_cards = [norm(c) for c in my_cards]
    board = [norm(c) for c in board_cards]         

    # YOLO 인식 오류 방어
    if len(my_cards) != 2:
        raise ValueError(f"내 카드는 2장이어야 합니다: {my_cards}")
    #보드는 0/3/4/5장만 허용
    if len(board) not in STAGE_NAMES:
        raise ValueError(f"커뮤니티 카드는 0/3/4/5장이어야 합니다: {board}")
    #내 카드 + 보드 전체에서 표기/중복 검사
    all_cards = my_cards + board
    if any(c not in DECK for c in all_cards):
        raise ValueError(f"알 수 없는 카드 표기가 있습니다: {all_cards}")
    if len(set(all_cards)) != len(all_cards):
        dup = [c for c, n in Counter(all_cards).items() if n > 1]
        raise ValueError(f"같은 카드가 두 번 인식됐습니다: {dup}")

    stage = STAGE_NAMES[len(board)]              
    rate = my_win_rate(my_cards, board, iterations, num_opponents)   
    grade, action = advice(rate, num_opponents)                      

    if verbose:
        print(f"진행 단계: {stage}")                                  
        print("내 카드:", my_cards)
        print("커뮤니티 카드:", board if board else "없음")           
        print("카드 특징:", describe_hand(my_cards, board))         
        print(f"내 승률: {rate:.1%}")
        print("카드 평가:", grade)
        print("추천 행동:", action)

    # 웹 화면 등에서 쓸 수 있게 결과를 dict로 반환
    return {"stage": stage, "my_cards": my_cards, "board": board,
            "win_rate": rate, "grade": grade, "action": action}


# ---------------- YOLO 연동 ----------------
def cards_from_yolo(results, expected=None, min_conf=MIN_CONF):
    """ultralytics의 predict() 결과에서 카드 목록을 뽑아 덱 표기("As", "10h")로 반환.

    - 카드 한 장에는 모서리 숫자가 2개라 같은 카드가 두 번 탐지되기 쉬움
      → 이름이 같은 탐지는 신뢰도가 가장 높은 하나만 남김
    - min_conf 미만은 버림
    - expected를 주면 신뢰도 높은 순으로 그 장수만 남김 (예: 내 카드 expected=2)
    """
    r = results[0] if isinstance(results, (list, tuple)) else results
    names = r.names
    best = {}
    for cls, conf in zip(r.boxes.cls.tolist(), r.boxes.conf.tolist()):
        if conf < min_conf:
            continue
        card = norm(names[int(cls)])
        if conf > best.get(card, 0):
            best[card] = conf

    cards = sorted(best, key=lambda c: -best[c])
    return cards[:expected] if expected else cards


def analyze_yolo(hand_results, board_results=None, num_opponents=NUM_OPPONENTS,
                 iterations=ITERATIONS, min_conf=MIN_CONF):

    my_cards = cards_from_yolo(hand_results, expected=2, min_conf=min_conf)
    board = cards_from_yolo(board_results, min_conf=min_conf) if board_results is not None else []
    return analyze(my_cards, board, num_opponents, iterations)