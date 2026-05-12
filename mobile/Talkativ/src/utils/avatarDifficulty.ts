export type AvatarDifficulty = 'easy' | 'medium' | 'hard';
export type SpeechLevelCode = 'formal' | 'polite' | 'informal';

type DifficultyMeta = {
  difficulty: AvatarDifficulty;
  label: string;
  description: string;
};

const EASY_ROLES = new Set([
  'friend',
  'close_friend',
  'classmate',
  'classmate_formal',
  'roommate',
  'club_member',
  'younger_sibling',
  'cousin',
]);

const HARD_ROLES = new Set([
  'parent',
  'grandparent',
  'professor',
  'teacher',
  'team_leader',
  'boss',
  'ceo',
  'client',
  'doctor',
]);

const HARD_ROLE_KEYWORDS = [
  '교수',
  '선생',
  '부장',
  '상사',
  '팀장',
  '대표',
  '사장',
  '고객',
  '클라이언트',
  '의사',
  '면접관',
  '임원',
  '원장',
  '회장',
  '부모',
  '아버지',
  '어머니',
  '할머니',
  '할아버지',
];

const EASY_ROLE_KEYWORDS = [
  '친구',
  '절친',
  '동기',
  '룸메',
  '룸메이트',
  '동아리',
  '동생',
  '사촌',
];

const MEDIUM_ROLE_KEYWORDS = [
  '선배',
  '후배',
  '동료',
  '팀원',
  '튜터',
  '이웃',
  '직원',
  '점원',
  '기사',
  '배달',
  '처음 만난',
  '낯선',
];

const includesAnyKeyword = (value: string, keywords: string[]) =>
  keywords.some((keyword) => value.includes(keyword));

const normalizeSpeechLevel = (level?: string | null): SpeechLevelCode | null => {
  if (level === 'formal' || level === 'polite' || level === 'informal') {
    return level;
  }
  return null;
};

export const deriveAvatarDifficulty = ({
  role,
  customRole,
  formalityFromUser,
}: {
  role?: string | null;
  customRole?: string | null;
  formalityFromUser?: string | null;
}): AvatarDifficulty => {
  const normalizedRole = (role || '').trim().toLowerCase();
  const normalizedCustomRole = (customRole || '').trim();
  const normalizedSpeech = normalizeSpeechLevel(formalityFromUser);

  if (HARD_ROLES.has(normalizedRole)) {
    return 'hard';
  }
  if (EASY_ROLES.has(normalizedRole)) {
    return 'easy';
  }

  if (normalizedCustomRole) {
    if (includesAnyKeyword(normalizedCustomRole, HARD_ROLE_KEYWORDS)) {
      return 'hard';
    }
    if (includesAnyKeyword(normalizedCustomRole, EASY_ROLE_KEYWORDS)) {
      return 'easy';
    }
    if (includesAnyKeyword(normalizedCustomRole, MEDIUM_ROLE_KEYWORDS)) {
      return 'medium';
    }
  }

  if (normalizedSpeech === 'formal') {
    return 'hard';
  }
  if (normalizedSpeech === 'informal') {
    return 'easy';
  }
  return 'medium';
};

export const getAvatarDifficultyMeta = (
  difficulty: AvatarDifficulty
): DifficultyMeta => {
  switch (difficulty) {
    case 'easy':
      return {
        difficulty,
        label: '쉬움',
        description: '친한 관계라 편하게 시작하기 좋아요.',
      };
    case 'hard':
      return {
        difficulty,
        label: '어려움',
        description: '격식과 존댓말이 더 중요한 관계예요.',
      };
    case 'medium':
    default:
      return {
        difficulty,
        label: '보통',
        description: '예의는 필요하지만 지나치게 딱딱하진 않아요.',
      };
  }
};
