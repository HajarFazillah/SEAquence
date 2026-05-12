#!/usr/bin/env python3
"""
Identity stability regression checks.

Run:
    python test_identity_stability.py
"""

from app.schemas.avatar import AvatarCreate
from app.services.prompt_builder import build_avatar_system_prompt


def assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing expected prompt text: {needle}")


def main() -> None:
    avatar = AvatarCreate(
        name_ko="민지",
        role="friend",
        description="사용자의 친한 친구입니다.",
    )
    situation = "\n".join([
        "상황 이름: 카페에서 대화",
        "장소/장면: 카페",
        "연습 목표: 약속 시간 정하기",
        "아바타의 장면 속 역할: 친구",
        "금지: 상황의 장소나 활동 때문에 아바타를 직원/점원/면접관/선생님 등 새 역할로 바꾸지 마세요.",
    ])

    prompt = build_avatar_system_prompt(avatar=avatar, situation=situation)

    assert_contains(prompt, "이 상황은 나의 정체성, 직업, 사용자와의 관계를 절대 바꾸지 않습니다.")
    assert_contains(prompt, "카페 상황이어도 내가 친구라면 친구로서 카페에 함께 있는 것이지")
    assert_contains(prompt, "장소에 맞춰 직원, 점원, 면접관, 선생님 같은 새 역할을 임의로 맡지 마세요.")

    print("Identity stability prompt checks passed.")


if __name__ == "__main__":
    main()
