# Project Scenario / 프로젝트 시나리오

|항목|내용|
|---|---|
|프로젝트명| UniMate: 유학생을 위한 한국어 공지사항 과부하 해결 적응형 AI 기반 정보 요약·해야 할 일 추 웹 서비스 |
|프로젝트 키워드| 웹앱, 유학생 지원, AI 챗봇, 정보요약, 스마트 추천 |
|트랙| 산학 |
|프로젝트멤버| Siti Hajar Asyiqin Binti Fazillah / Heimvichit, Nunnalin / Yuzana Win |
|팀지도교수| TBD |
|무엇을 만들고자 하는가| 유학생들이 한국 대학 생활에서 가장 큰 어려움 중 하나인 **한국어 공지사항 과부하 문제**를 해결하기 위해, 적응형 AI 기반의 웹 허브 서비스를 개발하고자 합니다. <br><br> 이 서비스는 학교 홈페이지, PDF, 공지사항 등 다양한 출처의 정보를 수집하여 **AI가 자동으로 요약·정리**하고, 공지의 맥락에 맞춰 **사용자가 실제로 해야 할 일**(예: 서류 준비, 마감 기한 확인, 행정 방문 여부)을 명확히 안내합니다. 이를 통해 유학생들은 불필요한 혼란을 줄이고, 필요한 조치를 놓치지 않도록 지원받을 수 있습니다. <br><br> 또한 학사 일정, 캠퍼스 생활 팁, 문화 관련 안내를 통합 대시보드에서 확인할 수 있으며, 개인화된 기록 관리와 통계 제공을 통해 **자신의 대학 생활 적응 현황을 체계적으로 관리**할 수 있습니다.|
|고객| 이화여대 유학생 (학부, 편입, 대학원) <br><br> [1] 푸릿차야 (19세, 태국인 학부생 유학생) <br> 특징: <br> - 유학 초기로 한국 대학 생활과 문화 적응에 어려움이 있음 <br> - 외로움으로 인해 가끔 우울한 느낌 경험 <br> - 한국어 활용 능력이 제한적임 <br> 고민: <br> - 한국어로 작성된 공지사항과 일정이 체계적으로 정리되어 있지 않아 FOMO(Fear Of Missing Out; 고립 공포) 심리 발생 <br> - 신입생으로서 MT, OT 등 대학 활동 정보 부족으로 친구 사귀기 어려움 <br> - 학교 보험 납부, 등록금 납부 등 필수 대학 관련 정보 파악이 어려움 <br><br> [2] 다니엘라 (27세, 미국인 대학원생 유학생) <br> 특징: <br> - 다양한 여행, 워크샵, 대학원 생활 경험에 관심 있음 <br> - 교육 관련 컨퍼런스, 진로 탐색 정보 수신 희망 <br> - 네트워킹에 관심 있음 <br> 고민: <br> - 대학원 생활에 맞는 스펙 관리 및 정보 취득 방법을 잘 모름 <br> - 대학원 정보와 학부생 정보가 달라 혼란스러움 <br> - 학부생과 달리 참여 가능한 교내 행사, 동아리 활동에 제한이 있음 |
|Pain Point|  - 유학생들이 대학 생활과 관련된 정보를 찾을 때, 자료가 여러 사이트와 커뮤니티에 흩어져 있어 혼란과 스트레스가 심함. <br> -  한국 대학 생활과 문화에 대한 적응 어려움: 수업 방식, 과제 관리, 학사 제도, 교내 활동 등에서 생기는 혼란. <br> - 학생 유형별 필요 차이: 학부, 편입, 대학원 학생마다 관심사와 요구사항이 달라, 일률적인 정보 제공으로는 충분하지 않음. <br> - 기존 정보는 텍스트 중심이 많아, 즉각적인 이해와 활용이 어려움. <br> - 학교 생활과 개인 경험을 체계적으로 정리할 방법이 부족하여, 정보 활용과 기록 관리에 부담을 느낌. <br> - 새로운 유학생에게는 커뮤니티 기반 정보나 추천이 부족하여, 스스로 경험을 찾아야 하는 어려움 존재. |
|사용할 소프트웨어 패키지의 명칭과 핵심기능/용도, 사용시나리오| - React / Next.js: 프론트엔드, 반응형 UI <br> - FastAPI / Node.js / Express / Django: 백엔드 API, 데이터 처리, 사용자 요청 처리 <br> - PostgreSQL / MongoDB: 데이터 관리, 사용자 기록 저장 <br> - BeautifulSoup: 웹사이트 공지사항 및 자료 스크래핑 <br> - OpenAI API: 문서 요약, 자연어 처리 <br> - CLOVA NLP: 한국어 텍스트 분석, 요약, 번역 <br> - KoNLPy, Transformers: 한국어 자연어 처리, 토큰화, 의미 분석, 문서 요약 |
|사용할 소프트웨어 패키지의 명칭과 URL| - React – https://react.dev <br> - Next.js – https://nextjs.org <br> - FastAPI – https://fastapi.tiangolo.com/ko/ <br> - PostgreSQL – https://www.postgresql.org/ <br> - BeautifulSoup – https://www.crummy.com/software/BeautifulSoup/ <br> - OpenAI – https://platform.openai.com/ <br> - CLOVA NLP – https://www.naver.com/clova <br> - KoNLPy – https://konlpy.org/ |
|팀그라운드룰| [SEAquence's Team Ground Rules](https://github.com/HajarFazillah/SEAquence/blob/main/GroundRule.md) |
|최종수정일| 2025-09-26 |
