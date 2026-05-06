import type { IconName } from '../components/Icon';

// API Configuration
export const SPRING_SERVER_URL = 'http://10.0.2.2:8080';
export const AI_SERVER_URL = 'http://10.0.2.2:8000';
export const SPRING_API_BASE_URL = SPRING_SERVER_URL;
export const AI_API_BASE_URL = `${AI_SERVER_URL}/api/v1`;
export const API_BASE_URL = SPRING_API_BASE_URL;

// Colors
export const COLORS = {
  primary: '#6C3BFF',
  secondary: '#1A1A2E',
  background: '#F7F7FB',
  white: '#FFFFFF',
  textPrimary: '#1A1A2E',
  textSecondary: '#6C6C80',
  textMuted: '#B0B0C5',
  border: '#E2E2EC',
  success: '#4CAF50',
  warning: '#F4A261',
  error: '#E53935',
};

// Avatar backgrounds - Extended palette
export const AVATAR_COLORS = {
  // Original
  pink: '#FFB6C1',
  purple: '#C8B4F8',
  blue: '#B4D4F8',
  green: '#B4F8D4',
  yellow: '#F8E8B4',
  
  // Vibrant
  coral: '#FF7F7F',
  lavender: '#E6E6FA',
  mint: '#98FB98',
  peach: '#FFCBA4',
  sky: '#87CEEB',
  
  // Deep
  deepPurple: '#9C27B0',
  deepBlue: '#3F51B5',
  deepTeal: '#009688',
  deepOrange: '#FF5722',
  deepPink: '#E91E63',
  
  // Neutral
  grey: '#9E9E9E',
  blueGrey: '#607D8B',
  brown: '#8D6E63',
  charcoal: '#455A64',
  
  // Pastel
  pastelRose: '#FFD1DC',
  pastelLilac: '#DCD0FF',
  pastelMint: '#AFFFDC',
  pastelLemon: '#FFFACD',
  pastelCoral: '#FFE4E1',
};

// System Avatars from AI Server
export const SYSTEM_AVATARS = [
  {
    id: 'jiwon_junior',
    name_ko: '박지원',
    name_en: 'Jiwon (Junior)',
    role: 'junior',
    difficulty: 'easy',
    description_ko: '당신의 후배. 밝고 친근한 성격.',
    avatarBg: AVATAR_COLORS.pink,
    icon: 'graduationCap' as IconName,
    interests: ['K-POP', '카페', '영화', '게임'],
  },
  {
    id: 'sujin_friend',
    name_ko: '김수진',
    name_en: 'Sujin (Friend)',
    role: 'friend',
    difficulty: 'easy',
    description_ko: '당신의 친한 친구. 유쾌하고 재미있는 성격.',
    avatarBg: AVATAR_COLORS.purple,
    icon: 'users' as IconName,
    interests: ['여행', '음식', 'SNS', '쇼핑'],
  },
  {
    id: 'minsu_senior',
    name_ko: '이민수',
    name_en: 'Minsu (Senior)',
    role: 'senior',
    difficulty: 'medium',
    description_ko: '당신의 선배. 듬직하고 조언을 잘 해주는 성격.',
    avatarBg: AVATAR_COLORS.blue,
    icon: 'briefcase' as IconName,
    interests: ['운동', '독서', '커리어', '자기계발'],
  },
  {
    id: 'professor_kim',
    name_ko: '김교수님',
    name_en: 'Professor Kim',
    role: 'professor',
    difficulty: 'hard',
    description_ko: '대학 교수님. 학문에 열정적이고 엄격하지만 따뜻한 분.',
    avatarBg: AVATAR_COLORS.green,
    icon: 'book' as IconName,
    interests: ['학문', '연구', '교육', '역사'],
  },
  {
    id: 'manager_lee',
    name_ko: '이팀장님',
    name_en: 'Manager Lee',
    role: 'boss',
    difficulty: 'hard',
    description_ko: '회사 팀장님. 카리스마 있고 성과 지향적인 분.',
    avatarBg: AVATAR_COLORS.yellow,
    icon: 'building' as IconName,
    interests: ['비즈니스', '리더십', '골프', '와인'],
  },
];

// Situations from AI Server
export const SITUATIONS: Array<{
  id: string;
  name_ko: string;
  name_en: string;
  description_ko: string;
  icon: IconName;
  category: string;
}> = [
  {
    id: 'cafe_chat',
    name_ko: '카페에서 수다',
    name_en: 'Cafe Chat',
    description_ko: '친구와 카페에서 일상적인 대화를 나눕니다.',
    icon: 'coffee',
    category: 'casual',
  },
  {
    id: 'campus_meetup',
    name_ko: '캠퍼스에서 만남',
    name_en: 'Campus Meetup',
    description_ko: '학교에서 선후배를 만나 인사합니다.',
    icon: 'graduationCap',
    category: 'casual',
  },
  {
    id: 'cafe_order',
    name_ko: '카페 주문',
    name_en: 'Cafe Order',
    description_ko: '카페에서 음료를 주문합니다.',
    icon: 'coffee',
    category: 'service',
  },
  {
    id: 'restaurant_order',
    name_ko: '식당 주문',
    name_en: 'Restaurant Order',
    description_ko: '식당에서 음식을 주문합니다.',
    icon: 'utensils',
    category: 'service',
  },
  {
    id: 'shopping',
    name_ko: '쇼핑',
    name_en: 'Shopping',
    description_ko: '가게에서 물건을 구매합니다.',
    icon: 'shoppingBag',
    category: 'service',
  },
  {
    id: 'professor_office',
    name_ko: '교수님 연구실 방문',
    name_en: 'Professor Office Visit',
    description_ko: '교수님 연구실을 방문하여 상담합니다.',
    icon: 'graduationCap',
    category: 'formal',
  },
  {
    id: 'group_project',
    name_ko: '그룹 프로젝트',
    name_en: 'Group Project',
    description_ko: '팀원들과 프로젝트에 대해 논의합니다.',
    icon: 'users',
    category: 'work',
  },
  {
    id: 'job_interview',
    name_ko: '취업 면접',
    name_en: 'Job Interview',
    description_ko: '면접관과 취업 면접을 진행합니다.',
    icon: 'briefcase',
    category: 'formal',
  },
  {
    id: 'office_meeting',
    name_ko: '회사 회의',
    name_en: 'Office Meeting',
    description_ko: '팀장님과 업무 회의를 합니다.',
    icon: 'building',
    category: 'work',
  },
  {
    id: 'first_meeting',
    name_ko: '처음 만남',
    name_en: 'First Meeting',
    description_ko: '처음 만나는 사람과 인사를 나눕니다.',
    icon: 'handshake',
    category: 'casual',
  },
  {
    id: 'party',
    name_ko: '파티/모임',
    name_en: 'Party',
    description_ko: '친구들과 파티나 모임에 참석합니다.',
    icon: 'party',
    category: 'casual',
  },
];

// Speech Level Info
export const SPEECH_LEVELS = {
  formal: {
    name_ko: '합쇼체',
    name_en: 'Formal',
    description: '가장 격식있는 말투입니다.',
    endings: ['-습니다', '-습니까', '-십시오'],
    color: '#6C3BFF',
  },
  polite: {
    name_ko: '해요체',
    name_en: 'Polite',
    description: '공손하지만 부드러운 말투입니다.',
    endings: ['-어요', '-아요', '-해요'],
    color: '#4CAF50',
  },
  informal: {
    name_ko: '반말',
    name_en: 'Informal',
    description: '친한 사이에서 쓰는 편한 말투입니다.',
    endings: ['-어', '-아', '-야', '-해'],
    color: '#F4A261',
  },
};

// Situation categories with icons
export const SITUATION_CATEGORIES = [
  { id: 'all', label: '전체', icon: 'fileText' as IconName },
  { id: 'casual', label: '일상', icon: 'coffee' as IconName },
  { id: 'service', label: '서비스', icon: 'shoppingBag' as IconName },
  { id: 'formal', label: '격식', icon: 'graduationCap' as IconName },
  { id: 'work', label: '업무', icon: 'briefcase' as IconName },
];
