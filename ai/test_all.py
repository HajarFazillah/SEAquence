#!/usr/bin/env python3
"""
Talkativ AI - Comprehensive Test Script
Tests all endpoints and features
"""

import asyncio
import httpx
import json
from typing import Optional

BASE_URL = "http://127.0.0.1:8000"

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str, passed: bool, details: str = ""):
    status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
    print(f"  {status} {name}")
    if details and not passed:
        print(f"       {Colors.YELLOW}{details}{Colors.END}")

def print_section(name: str):
    print(f"\n{Colors.BLUE}{'='*50}{Colors.END}")
    print(f"{Colors.BLUE}{name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*50}{Colors.END}")


async def test_health():
    """Test health endpoint"""
    print_section("Health Check")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            data = response.json()
            
            print_test("Server is running", response.status_code == 200)
            print_test("Status is healthy", data.get("status") == "healthy")
            print_test("CLOVA API configured", data.get("services", {}).get("clova_llm", False))
            
            print(f"\n  Services: {json.dumps(data.get('services', {}), indent=2)}")
            
            return data.get("services", {}).get("clova_llm", False)
        except Exception as e:
            print_test("Server connection", False, str(e))
            return False


async def test_core_endpoints():
    """Test core API endpoints"""
    print_section("Core Endpoints")
    
    async with httpx.AsyncClient() as client:
        # Test avatars list
        try:
            response = await client.get(f"{BASE_URL}/api/v1/avatars/")
            print_test("GET /avatars", response.status_code == 200)
            avatars = response.json()
            print(f"       Found {len(avatars)} avatars")
        except Exception as e:
            print_test("GET /avatars", False, str(e))
        
        # Test topics list
        try:
            response = await client.get(f"{BASE_URL}/api/v1/topics/")
            print_test("GET /topics", response.status_code == 200)
        except Exception as e:
            print_test("GET /topics", False, str(e))
        
        # Test politeness analysis
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/analysis/politeness",
                json={
                    "text": "안녕하세요",
                    "target_role": "senior"
                }
            )
            print_test("POST /analysis/politeness", response.status_code == 200)
            data = response.json()
            print(f"       Level: {data.get('level')}, Score: {data.get('score')}")
        except Exception as e:
            print_test("POST /analysis/politeness", False, str(e))


async def test_enhanced_analysis():
    """Test enhanced analysis endpoints"""
    print_section("Enhanced Analysis (Phase 1)")
    
    async with httpx.AsyncClient() as client:
        # Test enhanced politeness
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/analysis/enhanced",
                json={
                    "text": "교수님 질문 있어요",
                    "target_role": "professor",
                    "target_age": 55,
                    "user_age": 22
                }
            )
            print_test("POST /analysis/enhanced", response.status_code == 200)
            data = response.json()
            print(f"       Level: {data.get('level')}, Appropriate: {data.get('is_appropriate')}")
            print(f"       Errors: {data.get('errors', [])[:2]}")
        except Exception as e:
            print_test("POST /analysis/enhanced", False, str(e))
        
        # Test quick check
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/analysis/quick",
                params={"text": "감사합니다", "target_role": "professor"}
            )
            print_test("GET /analysis/quick", response.status_code == 200)
        except Exception as e:
            print_test("GET /analysis/quick", False, str(e))


async def test_ml_analysis():
    """Test ML analysis endpoints"""
    print_section("ML Analysis")
    
    async with httpx.AsyncClient() as client:
        # Test ML status
        try:
            response = await client.get(f"{BASE_URL}/api/v1/ml/status")
            print_test("GET /ml/status", response.status_code == 200)
            data = response.json()
            print(f"       ML Status: {data.get('ml_status', {})}")
        except Exception as e:
            print_test("GET /ml/status", False, str(e))
        
        # Test topic classification
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/ml/topic",
                json={"text": "오늘 수업 너무 어려웠어"}
            )
            print_test("POST /ml/topic", response.status_code == 200)
            data = response.json()
            print(f"       Topic: {data.get('primary_topic_ko')}")
        except Exception as e:
            print_test("POST /ml/topic", False, str(e))
        
        # Test emotion detection
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/ml/emotion",
                params={"text": "와 진짜 기뻐!! ㅎㅎㅎ"}
            )
            print_test("POST /ml/emotion", response.status_code == 200)
            data = response.json()
            print(f"       Emotion: {data.get('primary_emotion')}")
        except Exception as e:
            print_test("POST /ml/emotion", False, str(e))
        
        # Test comprehensive analysis
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/ml/comprehensive",
                json={
                    "text": "교수님 질문 있어요",
                    "target_role": "professor",
                    "avatar_formality": "very_polite"
                }
            )
            print_test("POST /ml/comprehensive", response.status_code == 200)
            data = response.json()
            print(f"       Score: {data.get('overall_score')}, Appropriate: {data.get('is_appropriate')}")
        except Exception as e:
            print_test("POST /ml/comprehensive", False, str(e))


async def test_revision(clova_available: bool):
    """Test revision endpoints"""
    print_section("Revision & Sample Reply")
    
    if not clova_available:
        print(f"  {Colors.YELLOW}⚠ CLOVA API not configured - using fallback{Colors.END}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test revision
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/revision/revise",
                json={
                    "sentence": "교수님 질문 있어요",
                    "target_role": "professor",
                    "target_formality": "very_polite"
                }
            )
            print_test("POST /revision/revise", response.status_code == 200)
            data = response.json()
            print(f"       Original: {data.get('original')}")
            print(f"       Revised: {data.get('revised')}")
            print(f"       Has Error: {data.get('has_error')}")
        except Exception as e:
            print_test("POST /revision/revise", False, str(e))
        
        # Test sample replies
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/revision/sample-replies",
                json={
                    "situation": "I want to ask my professor about the assignment deadline",
                    "target_role": "professor",
                    "target_formality": "very_polite"
                }
            )
            print_test("POST /revision/sample-replies", response.status_code == 200)
            data = response.json()
            samples = data.get("samples", [])
            print(f"       Got {len(samples)} sample replies")
            for s in samples[:2]:
                print(f"       • {s.get('korean', s)}")
        except Exception as e:
            print_test("POST /revision/sample-replies", False, str(e))
        
        # Test formality examples
        try:
            response = await client.get(f"{BASE_URL}/api/v1/revision/formality-examples/polite")
            print_test("GET /revision/formality-examples", response.status_code == 200)
        except Exception as e:
            print_test("GET /revision/formality-examples", False, str(e))


async def test_progress():
    """Test user progress endpoints"""
    print_section("User Progress (Phase 2)")
    
    async with httpx.AsyncClient() as client:
        user_id = "test_user_123"
        
        # Create user profile
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/progress/profile",
                json={
                    "user_id": user_id,
                    "korean_level": "intermediate",
                    "native_language": "en",
                    "interests": ["kpop", "drama"]
                }
            )
            print_test("POST /progress/profile", response.status_code == 200)
        except Exception as e:
            print_test("POST /progress/profile", False, str(e))
        
        # Get user profile
        try:
            response = await client.get(f"{BASE_URL}/api/v1/progress/profile/{user_id}")
            print_test("GET /progress/profile/{id}", response.status_code == 200)
        except Exception as e:
            print_test("GET /progress/profile/{id}", False, str(e))
        
        # Get skills
        try:
            response = await client.get(f"{BASE_URL}/api/v1/progress/skills/{user_id}")
            print_test("GET /progress/skills/{id}", response.status_code == 200)
        except Exception as e:
            print_test("GET /progress/skills/{id}", False, str(e))
        
        # Get recommendations
        try:
            response = await client.get(f"{BASE_URL}/api/v1/progress/recommendations/{user_id}")
            print_test("GET /progress/recommendations/{id}", response.status_code == 200)
            data = response.json()
            rec = data.get("recommendations", {})
            if rec:
                print(f"       Recommended Avatar: {rec.get('avatar', {}).get('avatar_id')}")
                print(f"       Recommended Topic: {rec.get('topic', {}).get('topic_id')}")
        except Exception as e:
            print_test("GET /progress/recommendations/{id}", False, str(e))


async def test_avatars():
    """Test avatar management endpoints"""
    print_section("Avatar Management")
    
    async with httpx.AsyncClient() as client:
        user_id = "test_user_123"
        
        # Create custom avatar
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/avatars/create",
                json={
                    "user_id": user_id,
                    "name": "Test Avatar",
                    "name_ko": "테스트 아바타",
                    "role": "friend",
                    "age": 25,
                    "personality": "friendly and helpful",
                    "formality": "polite"
                }
            )
            print_test("POST /avatars/create", response.status_code == 200)
            data = response.json()
            avatar_id = data.get("avatar_id")
            print(f"       Created: {avatar_id}")
        except Exception as e:
            print_test("POST /avatars/create", False, str(e))
        
        # List user avatars
        try:
            response = await client.get(f"{BASE_URL}/api/v1/avatars/user/{user_id}")
            print_test("GET /avatars/user/{id}", response.status_code == 200)
            data = response.json()
            print(f"       User has {len(data.get('custom_avatars', []))} custom avatars")
        except Exception as e:
            print_test("GET /avatars/user/{id}", False, str(e))


async def test_integrated_chat(clova_available: bool):
    """Test integrated chat endpoints"""
    print_section("Integrated Chat")
    
    if not clova_available:
        print(f"  {Colors.YELLOW}⚠ CLOVA API not configured - limited testing{Colors.END}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Start session
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/integrated/start",
                json={
                    "user_id": "test_user_123",
                    "avatar_id": "professor_kim",
                    "topic": "professor_meeting"
                }
            )
            print_test("POST /integrated/start", response.status_code == 200)
            data = response.json()
            session_id = data.get("session_id")
            print(f"       Session: {session_id}")
            print(f"       Avatar: {data.get('avatar_name')}")
        except Exception as e:
            print_test("POST /integrated/start", False, str(e))
            return
        
        if not session_id:
            return
        
        # Send message
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/integrated/message",
                json={
                    "session_id": session_id,
                    "message": "교수님 질문 있어요",
                    "include_revision": True,
                    "include_samples": True
                }
            )
            print_test("POST /integrated/message", response.status_code == 200)
            data = response.json()
            
            analysis = data.get("user_message", {}).get("analysis", {})
            print(f"       Score: {analysis.get('score')}, Appropriate: {analysis.get('is_appropriate')}")
            
            if data.get("revision"):
                print(f"       Revision: {data['revision'].get('revised')}")
            
            if data.get("avatar_response"):
                resp = data["avatar_response"].get("content", "")[:50]
                print(f"       Avatar: {resp}...")
        except Exception as e:
            print_test("POST /integrated/message", False, str(e))
        
        # End session
        try:
            response = await client.post(f"{BASE_URL}/api/v1/integrated/end/{session_id}")
            print_test("POST /integrated/end", response.status_code == 200)
        except Exception as e:
            print_test("POST /integrated/end", False, str(e))


async def test_prompt_preview():
    """Test prompt preview endpoints"""
    print_section("System Prompt Preview")
    
    async with httpx.AsyncClient() as client:
        # Preview prompt
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/prompts/preview",
                json={
                    "avatar_id": "professor_kim",
                    "topic": "professor_meeting",
                    "user_context": {
                        "korean_level": "intermediate",
                        "weak_skills": ["formal_speech"],
                        "common_errors": ["ending_mismatch"],
                        "sessions_completed": 10,
                        "average_score": 68
                    }
                }
            )
            print_test("POST /prompts/preview", response.status_code == 200)
            data = response.json()
            prompt = data.get("system_prompt", "")
            print(f"       Prompt length: {len(prompt)} chars")
            print(f"       Contains user context: {'학습자 정보' in prompt}")
        except Exception as e:
            print_test("POST /prompts/preview", False, str(e))
        
        # Get teaching modes
        try:
            response = await client.get(f"{BASE_URL}/api/v1/prompts/teaching-modes")
            print_test("GET /prompts/teaching-modes", response.status_code == 200)
        except Exception as e:
            print_test("GET /prompts/teaching-modes", False, str(e))


async def main():
    """Run all tests"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}       TALKATIV AI - COMPREHENSIVE TEST SUITE{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")
    
    # Health check first
    clova_available = await test_health()
    
    # Core endpoints
    await test_core_endpoints()
    
    # Enhanced analysis
    await test_enhanced_analysis()
    
    # ML analysis
    await test_ml_analysis()
    
    # User progress
    await test_progress()
    
    # Avatar management
    await test_avatars()
    
    # Prompt preview
    await test_prompt_preview()
    
    # Revision (uses CLOVA)
    await test_revision(clova_available)
    
    # Integrated chat (uses CLOVA)
    await test_integrated_chat(clova_available)
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}Testing complete!{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")


if __name__ == "__main__":
    asyncio.run(main())
