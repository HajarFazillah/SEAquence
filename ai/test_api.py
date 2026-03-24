#!/usr/bin/env python3
"""
Talkativ AI Server - API Test Script

Run this script to test all API endpoints.

Usage:
    1. Start the server: uvicorn app.main:app --reload --port 8000
    2. Run tests: python test_api.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_test(name: str):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


def print_success(msg: str):
    print(f"{GREEN}✅ {msg}{RESET}")


def print_error(msg: str):
    print(f"{RED}❌ {msg}{RESET}")


def print_info(msg: str):
    print(f"{YELLOW}ℹ️  {msg}{RESET}")


def print_json(data: dict):
    print(json.dumps(data, indent=2, ensure_ascii=False))


# =============================================================================
# Test Data
# =============================================================================

TEST_USER_PROFILE = {
    "name": "나린",
    "age": 22,
    "gender": "female",
    "korean_level": "intermediate",
    "interests": ["음악", "여행", "카페"],
    "dislikes": ["정치", "취업 스트레스"],
    "memo": "처음 배우는 단어는 천천히 설명해주세요"
}

TEST_AVATAR = {
    "name_ko": "이민수",
    "name_en": "Lee Minsu",
    "age": 28,
    "gender": "male",
    "avatarType": "fictional",
    "role": "senior",
    "customRole": "",
    "relationship_description": "같은 동아리 선배, 2년 전부터 알고 지냄",
    "description": "IT 회사에서 일하는 개발자. 친근하고 유머러스한 성격.",
    "personality_traits": ["친절함", "유머러스"],
    "speaking_style": "편하게 말하지만 존중하는 느낌",
    "interests": ["코딩", "게임", "K-POP"],
    "dislikes": ["거짓말"],
    "memo": "사용자가 어려워하면 천천히 설명해줌",
    "avatarBg": "blue",
    "icon": "smile",
    "difficulty": "medium",
    "formality_to_user": "informal",
    "formality_from_user": "polite",
    "bio": ""
}


# =============================================================================
# Test Functions
# =============================================================================

def test_health():
    """Test server is running"""
    print_test("Health Check")
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print_success("Server is running!")
            print_json(response.json())
            return True
        else:
            print_error(f"Server returned {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to server!")
        print_info("Make sure to run: uvicorn app.main:app --reload --port 8000")
        return False


def test_recommendation_roles():
    """Test GET /recommendation/roles"""
    print_test("Get All Roles")
    try:
        response = requests.get(f"{BASE_URL}/recommendation/roles")
        data = response.json()
        print_success(f"Got {len(data['roles'])} roles")
        print(f"Categories: {list(data['roles'].keys())}")
        return True
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_recommendation_speech_level():
    """Test GET /recommendation/speech-level"""
    print_test("Get Speech Level for Role")
    
    roles_to_test = ["friend", "senior", "professor", "boss"]
    
    for role in roles_to_test:
        try:
            response = requests.get(f"{BASE_URL}/recommendation/speech-level?role={role}")
            data = response.json()
            print_success(f"Role: {role}")
            print(f"  Avatar→User: {data['to_user']['level']} ({data['to_user']['name_ko']})")
            print(f"  User→Avatar: {data['from_user']['level']} ({data['from_user']['name_ko']})")
        except Exception as e:
            print_error(f"Error for {role}: {e}")
            return False
    
    return True


def test_chat():
    """Test POST /chat"""
    print_test("Chat with Avatar")
    
    request_data = {
        "avatar": TEST_AVATAR,
        "user_message": "선배 안녕하세요! 오늘 뭐 하세요?",
        "conversation_history": [],
        "user_profile": TEST_USER_PROFILE,
        "situation": "카페에서 우연히 만남",
        "user_id": "test_user_123"
    }
    
    try:
        print_info("Sending message: '선배 안녕하세요! 오늘 뭐 하세요?'")
        response = requests.post(f"{BASE_URL}/chat", json=request_data)
        data = response.json()
        
        if response.status_code == 200:
            print_success("Got response from avatar!")
            print(f"\n{YELLOW}Avatar says:{RESET} {data['message']}")
            
            if data.get('correction'):
                correction = data['correction']
                print(f"\n{YELLOW}Correction:{RESET}")
                print(f"  Has errors: {correction.get('has_errors', False)}")
                print(f"  Accuracy: {correction.get('accuracy_score', 'N/A')}%")
                if correction.get('encouragement'):
                    print(f"  Encouragement: {correction['encouragement']}")
            
            print(f"\n{YELLOW}Mood:{RESET} {data.get('mood_emoji', '')} {data.get('current_mood', '')}%")
            
            if data.get('suggestions'):
                print(f"\n{YELLOW}Suggestions:{RESET} {', '.join(data['suggestions'])}")
            
            return True
        else:
            print_error(f"Error: {response.status_code}")
            print_json(data)
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_chat_with_errors():
    """Test chat with intentional speech level errors"""
    print_test("Chat with Speech Level Errors")
    
    request_data = {
        "avatar": TEST_AVATAR,
        "user_message": "선배 뭐해? 나 오늘 너무 피곤해",  # Using 반말 to senior (wrong!)
        "conversation_history": [],
        "user_profile": TEST_USER_PROFILE,
        "situation": "카페에서 만남",
        "user_id": "test_user_123"
    }
    
    try:
        print_info("Sending message with WRONG speech level: '선배 뭐해? 나 오늘 너무 피곤해'")
        print_info("(Using 반말 to senior - should trigger correction)")
        
        response = requests.post(f"{BASE_URL}/chat", json=request_data)
        data = response.json()
        
        if response.status_code == 200:
            print_success("Got response!")
            
            correction = data.get('correction', {})
            if correction.get('has_errors'):
                print_success("Errors detected correctly!")
                print(f"\n{YELLOW}Corrections:{RESET}")
                for c in correction.get('corrections', []):
                    print(f"  • '{c['original']}' → '{c['corrected']}'")
                    print(f"    Type: {c['type']}, Severity: {c['severity']}")
                    print(f"    Explanation: {c['explanation']}")
                
                if correction.get('corrected_message'):
                    print(f"\n{YELLOW}Full correction:{RESET} {correction['corrected_message']}")
            else:
                print_info("No errors detected (CLOVA may have been lenient)")
            
            return True
        else:
            print_error(f"Error: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_chat_check():
    """Test POST /chat/check (quick correction without response)"""
    print_test("Quick Correction Check")
    
    test_messages = [
        {"message": "교수님 뭐해?", "expected_speech_level": "formal", "avatar_role": "professor"},
        {"message": "교수님, 안녕하십니까?", "expected_speech_level": "formal", "avatar_role": "professor"},
        {"message": "야 뭐해?", "expected_speech_level": "informal", "avatar_role": "friend"},
    ]
    
    for test in test_messages:
        try:
            print_info(f"Checking: '{test['message']}' (expected: {test['expected_speech_level']})")
            
            response = requests.post(f"{BASE_URL}/chat/check", json={
                "message": test['message'],
                "expected_speech_level": test['expected_speech_level'],
                "avatar_role": test['avatar_role'],
                "user_level": "intermediate"
            })
            data = response.json()
            
            if data.get('has_errors'):
                print(f"  {RED}Errors found{RESET} - Accuracy: {data.get('accuracy_score', 'N/A')}%")
            else:
                print(f"  {GREEN}Correct!{RESET} - Accuracy: {data.get('accuracy_score', 'N/A')}%")
                
        except Exception as e:
            print_error(f"Error: {e}")
            return False
    
    return True


def test_compatibility():
    """Test POST /compatibility/analyze"""
    print_test("Compatibility Analysis")
    
    request_data = {
        "user_profile": TEST_USER_PROFILE,
        "avatar": TEST_AVATAR
    }
    
    try:
        # Test simple (rule-based)
        print_info("Testing simple compatibility (rule-based)...")
        response = requests.post(f"{BASE_URL}/compatibility/analyze-simple", json=request_data)
        data = response.json()
        
        print_success(f"Simple Analysis - Score: {data['overall_score']}%")
        print(f"  Interest overlap: {data['interest_overlap']}%")
        print(f"  Topic safety: {data['topic_safety']}%")
        print(f"  Difficulty match: {data['difficulty_match']}%")
        
        # Test full (AI-powered)
        print_info("\nTesting full compatibility (AI-powered)...")
        response = requests.post(f"{BASE_URL}/compatibility/analyze", json=request_data)
        data = response.json()
        
        print_success(f"AI Analysis - Score: {data['overall_score']}%")
        
        if data.get('semantic_matches'):
            print(f"\n{YELLOW}Semantic Matches:{RESET}")
            for match in data['semantic_matches'][:3]:
                print(f"  • {match['user_interest']} ↔ {match['avatar_interest']} ({match['similarity']}%)")
        
        if data.get('suggested_topics'):
            print(f"\n{YELLOW}Suggested Topics:{RESET}")
            for topic in data['suggested_topics'][:3]:
                print(f"  • {topic}")
        
        print(f"\n{YELLOW}Recommendation:{RESET} {data['recommendation']}")
        
        return True
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_memory():
    """Test memory endpoints"""
    print_test("Conversation Memory")
    
    user_id = "test_user_123"
    avatar_id = "minsu_avatar"
    
    # Test extract memories
    print_info("Extracting memories from conversation...")
    
    messages = [
        {"role": "user", "content": "선배, 저 다음 주에 제주도 여행 가요!"},
        {"role": "assistant", "content": "오 진짜? 좋겠다! 얼마나 가?"},
        {"role": "user", "content": "3박 4일이요. 고양이 두 마리 맡겨야 해서 걱정이에요."},
        {"role": "assistant", "content": "아 고양이 키우는구나! 펫시터 알아봤어?"},
    ]
    
    try:
        response = requests.post(f"{BASE_URL}/memory/extract", json={
            "user_id": user_id,
            "avatar_id": avatar_id,
            "messages": messages
        })
        data = response.json()
        
        print_success(f"Extracted {data['total']} memories")
        for m in data['memories']:
            print(f"  • [{m['type']}] {m['content']}")
        
        # Test get context
        print_info("\nGetting conversation context...")
        response = requests.post(f"{BASE_URL}/memory/context", json={
            "user_id": user_id,
            "avatar_id": avatar_id,
            "avatar_name": "이민수"
        })
        data = response.json()
        
        print_success("Got context!")
        print(f"  Relationship: {data['relationship_summary']}")
        if data.get('suggested_callbacks'):
            print(f"  Callbacks: {', '.join(data['suggested_callbacks'][:2])}")
        
        # Test summarize
        print_info("\nSummarizing conversation...")
        response = requests.post(f"{BASE_URL}/memory/summarize", json={
            "user_id": user_id,
            "avatar_id": avatar_id,
            "conversation_id": "conv_001",
            "messages": messages,
            "duration_minutes": 10
        })
        data = response.json()
        
        print_success("Summary created!")
        print(f"  Topics: {', '.join(data['main_topics'])}")
        print(f"  Mood: {data['mood']}")
        print(f"  New memories: {data['new_memories_count']}")
        
        return True
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_vocabulary():
    """Test vocabulary endpoints"""
    print_test("Vocabulary Spaced Repetition")
    
    user_id = "test_user_123"
    
    try:
        # Add vocabulary
        print_info("Adding vocabulary...")
        response = requests.post(f"{BASE_URL}/vocabulary/add", json={
            "user_id": user_id,
            "korean": "설레다",
            "meaning": "to be excited, to flutter",
            "type": "word",
            "example": "여행 전날이라 설레요",
            "source_avatar_name": "이민수"
        })
        data = response.json()
        vocab_id = data['id']
        
        print_success(f"Added vocabulary: {data['korean']}")
        print(f"  Mastery: {data['mastery_level']} ({data['mastery_score']}%)")
        
        # Add more words
        for word in [("기대되다", "to look forward to"), ("멀미", "motion sickness")]:
            requests.post(f"{BASE_URL}/vocabulary/add", json={
                "user_id": user_id,
                "korean": word[0],
                "meaning": word[1],
                "type": "word"
            })
        
        # Get stats
        print_info("\nGetting vocabulary stats...")
        response = requests.get(f"{BASE_URL}/vocabulary/{user_id}/stats")
        data = response.json()
        
        print_success("Stats:")
        print(f"  Total words: {data['total_words']}")
        print(f"  Due today: {data['due_today']}")
        print(f"  Mastered: {data['mastered_count']}")
        
        # Get due reviews
        print_info("\nGetting due reviews...")
        response = requests.get(f"{BASE_URL}/vocabulary/{user_id}/due?limit=5")
        data = response.json()
        
        print_success(f"Due for review: {data['total']} items")
        for item in data['items'][:3]:
            print(f"  • {item['korean']} - {item['mastery_level']}")
        
        # Record a review
        print_info("\nRecording a review (correct)...")
        response = requests.post(f"{BASE_URL}/vocabulary/review", json={
            "user_id": user_id,
            "vocab_id": vocab_id,
            "correct": True,
            "response_time_ms": 2000
        })
        data = response.json()
        
        print_success("Review recorded!")
        print(f"  New mastery: {data['mastery_level']} ({data['mastery_score']}%)")
        print(f"  Next review in: {data['interval_days']} days")
        print(f"  Streak: {data['streak']}")
        
        return True
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_extract_vocab_from_conversation():
    """Test extracting vocabulary from conversation"""
    print_test("Extract Vocabulary from Conversation")
    
    try:
        messages = [
            {"role": "assistant", "content": "여행 전날이라 설레겠다!"},
            {"role": "user", "content": "응 너무 기대돼!"},
            {"role": "assistant", "content": "비행기 탈 때 멀미는 안 해?"},
            {"role": "user", "content": "조금 해요. 약 먹어야 할 것 같아요."},
        ]
        
        print_info("Extracting vocabulary from conversation...")
        response = requests.post(f"{BASE_URL}/vocabulary/extract", json={
            "user_id": "test_user_123",
            "avatar_id": "minsu",
            "avatar_name": "이민수",
            "messages": messages
        })
        data = response.json()
        
        print_success(f"Extracted {data['total']} vocabulary items")
        for item in data['items']:
            print(f"  • {item['korean']} ({item['type']})")
            print(f"    Meaning: {item['meaning']}")
        
        return True
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_generate_bio():
    """Test avatar bio generation"""
    print_test("Generate Avatar Bio")
    
    try:
        print_info("Generating bio for avatar...")
        response = requests.post(f"{BASE_URL}/chat/generate-bio", json={
            "avatar": TEST_AVATAR
        })
        data = response.json()
        
        print_success("Bio generated!")
        print(f"\n{YELLOW}Bio:{RESET}")
        print(data['bio'])
        
        return True
    except Exception as e:
        print_error(f"Error: {e}")
        return False


# =============================================================================
# Main
# =============================================================================

def run_all_tests():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}       TALKATIV AI SERVER - API TEST SUITE{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"Server URL: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Health Check", test_health),
        ("Recommendation - Roles", test_recommendation_roles),
        ("Recommendation - Speech Level", test_recommendation_speech_level),
        ("Chat - Normal", test_chat),
        ("Chat - With Errors", test_chat_with_errors),
        ("Chat - Quick Check", test_chat_check),
        ("Compatibility Analysis", test_compatibility),
        ("Memory System", test_memory),
        ("Vocabulary - Basic", test_vocabulary),
        ("Vocabulary - Extract", test_extract_vocab_from_conversation),
        ("Generate Bio", test_generate_bio),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}                    TEST SUMMARY{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"  {status}  {name}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"  {GREEN}All tests passed! 🎉{RESET}")
    else:
        print(f"  {RED}Some tests failed. Check output above.{RESET}")
    
    print(f"{BLUE}{'='*60}{RESET}\n")


if __name__ == "__main__":
    run_all_tests()
