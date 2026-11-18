
from __future__ import annotations

import contextlib
import io
import random
from functools import lru_cache


with contextlib.redirect_stdout(io.StringIO()):
    import poker_equity as core


@lru_cache(maxsize=1)
def _deck():
    return tuple(core.DECK)


def _normalize_cards(cards, expected_min=0, expected_max=None):
    normalized = [core.norm(card) for card in cards]
    if len(normalized) < expected_min:
        raise ValueError(f"카드가 최소 {expected_min}장 필요합니다.")
    if expected_max is not None and len(normalized) > expected_max:
        raise ValueError(f"카드는 최대 {expected_max}장까지 입력할 수 있습니다.")
    if len(set(normalized)) != len(normalized):
        raise ValueError("같은 카드가 중복되었습니다.")
    invalid = [card for card in normalized if card not in core.DECK]
    if invalid:
        raise ValueError(f"올바르지 않은 카드입니다: {', '.join(invalid)}")
    return normalized


def estimate_equity(hole_cards, community_cards=(), opponents=1, trials=1400):
    """고정된 내 카드/공개 커뮤니티 카드를 반영해 승률을 추정한다.

    족보 판정은 poker_equity.best_rank를 그대로 사용하며, 승/무승부 점수
    방식도 원본 my_win_rate와 동일하게 승리 1, 무승부 0.5로 계산한다.
    """
    hole = _normalize_cards(hole_cards, expected_min=2, expected_max=2)
    board = _normalize_cards(community_cards, expected_min=0, expected_max=5)
    if len(set(hole + board)) != len(hole) + len(board):
        raise ValueError("내 카드와 커뮤니티 카드가 중복되었습니다.")
    if not isinstance(opponents, int) or not 1 <= opponents <= 9:
        raise ValueError("상대 플레이어 수는 1~9명이어야 합니다.")
    if len(board) + 2 * opponents > 50:
        raise ValueError("상대 플레이어 수가 너무 많습니다.")
    if not isinstance(trials, int) or trials < 1:
        raise ValueError("시뮬레이션 횟수는 1회 이상이어야 합니다.")

    known = set(hole + board)
    remaining = [card for card in _deck() if card not in known]
    missing_board = 5 - len(board)
    needed = missing_board + 2 * opponents
    score = 0.0

    for _ in range(trials):
        draw = random.sample(remaining, needed)
        full_board = board + draw[:missing_board]
        my_rank = core.best_rank(hole + full_board)
        opponent_cards = draw[missing_board:]
        opponent_ranks = [
            core.best_rank(opponent_cards[i * 2:i * 2 + 2] + full_board)
            for i in range(opponents)
        ]
        best_opponent = max(opponent_ranks)
        if my_rank > best_opponent:
            score += 1.0
        elif my_rank == best_opponent:
            score += 0.5

    return score / trials


def get_hand_features(hole_cards):
    hole = _normalize_cards(hole_cards, expected_min=2, expected_max=2)
    return core.describe_hand(hole)


def get_recommendation(rate, opponents=1):
    return core.advice(rate, num_opponents=opponents)


def evaluate_visible_hand(hole_cards, community_cards=()):
    """현재 공개된 카드로 만들 수 있는 최선의 족보 이름을 반환한다."""
    hole = _normalize_cards(hole_cards, expected_min=2, expected_max=2)
    board = _normalize_cards(community_cards, expected_min=0, expected_max=5)
    if len(set(hole + board)) != len(hole) + len(board):
        raise ValueError("내 카드와 커뮤니티 카드가 중복되었습니다.")
    cards = hole + board
    if len(cards) < 5:
        return "아직 족보를 판정할 카드가 부족합니다."
    return core.HAND_NAMES[core.best_rank(cards)[0]]
