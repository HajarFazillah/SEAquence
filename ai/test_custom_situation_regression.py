#!/usr/bin/env python3
"""
Custom situation regression checks for realtime correction.

Run:
    python test_custom_situation_regression.py

Notes:
- Requires the same environment the AI server uses.
- Uses the internal ChatService realtime analyzer.
- CLOVA-backed, so network/API access should be available.
"""

import asyncio
from dataclasses import dataclass
from typing import List

from app.schemas.avatar import SpeechLevel
from app.services.chat_service import ChatService


@dataclass
class RegressionCase:
    name: str
    user_message: str
    expected_level: SpeechLevel
    avatar_role: str
    situation: str
    expected_substrings: List[str]
    expected_correction_types: List[str]


CASES = [
    RegressionCase(
        name="service_order_request",
        user_message="라태 두개 포장해줘",
        expected_level=SpeechLevel.POLITE,
        avatar_role="카페 직원",
        situation="사용자가 직접 만든 상황: 처음 가 본 디저트 카페에서 직원에게 테이크아웃을 부탁하는 상황",
        expected_substrings=["라떼", "두 개", "포장해 주세요"],
        expected_correction_types=["spelling", "honorific"],
    ),
    RegressionCase(
        name="professor_greeting_first_meeting",
        user_message="교수님 안녕",
        expected_level=SpeechLevel.POLITE,
        avatar_role="교수",
        situation="사용자가 직접 만든 상황: 교수님 연구실에 처음 방문해서 인사하는 상황",
        expected_substrings=["안녕하세요"],
        expected_correction_types=["honorific"],
    ),
    RegressionCase(
        name="library_desk_question",
        user_message="저 책 반납 어디에 해",
        expected_level=SpeechLevel.POLITE,
        avatar_role="도서관 안내 직원",
        situation="사용자가 직접 만든 상황: 도서관 안내 데스크에서 처음 만난 직원에게 반납 위치를 묻는 상황",
        expected_substrings=["반납", "어디"] ,
        expected_correction_types=["speech_level"],
    ),
    RegressionCase(
        name="senior_request",
        user_message="선배 이거 좀 봐줘",
        expected_level=SpeechLevel.POLITE,
        avatar_role="동아리 선배",
        situation="사용자가 직접 만든 상황: 처음 같이 프로젝트를 하는 동아리 선배에게 자료를 확인해 달라고 부탁하는 상황",
        expected_substrings=["봐 주세요"],
        expected_correction_types=["honorific"],
    ),
]


async def main() -> None:
    service = ChatService()
    failures = []

    for case in CASES:
        result = await service._analyze_realtime(
            user_message=case.user_message,
            expected_speech_level=case.expected_level,
            avatar_role=case.avatar_role,
            user_level="intermediate",
            situation=case.situation,
            conversation_history=[],
        )

        corrected = result.corrected_message or ""
        correction_types = [correction.type.value for correction in result.corrections]

        missing_substrings = [item for item in case.expected_substrings if item not in corrected and all(item not in c.corrected for c in result.corrections)]
        missing_types = [item for item in case.expected_correction_types if item not in correction_types]

        passed = not missing_substrings and not missing_types
        print(f"\n[{ 'PASS' if passed else 'FAIL' }] {case.name}")
        print(f"  message:   {case.user_message}")
        print(f"  situation: {case.situation}")
        print(f"  corrected: {corrected}")
        print(f"  types:     {correction_types}")

        if not passed:
            failures.append((case.name, missing_substrings, missing_types))
            if missing_substrings:
                print(f"  missing substrings: {missing_substrings}")
            if missing_types:
                print(f"  missing types: {missing_types}")

    if failures:
        print("\nRegression failures found:")
        for name, substrings, types in failures:
            print(f"- {name}: substrings={substrings}, types={types}")
        raise SystemExit(1)

    print("\nAll custom situation regression checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
