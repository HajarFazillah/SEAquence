import React, { useEffect, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet,
  ScrollView, TouchableOpacity, Alert, ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import { 
  Coffee, Briefcase, GraduationCap, ShoppingBag,
  UtensilsCrossed, Users, Building2, Handshake, PartyPopper,
  MapPin, Sparkles, Check,
} from 'lucide-react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Header, Card, Button, InputField, Tag } from '../components';
import type { IconName } from '../components/Icon';
import { AI_SERVER_URL } from '../constants';
import { getMyProfile, UserProfile } from '../services/apiUser';

const CUSTOM_SITUATIONS_KEY = 'custom_situations';
const AI_SERVER = AI_SERVER_URL;

const SITUATION_ICONS = [
  { id: 'coffee', icon: Coffee, label: '카페' },
  { id: 'utensils', icon: UtensilsCrossed, label: '식당' },
  { id: 'shoppingBag', icon: ShoppingBag, label: '쇼핑' },
  { id: 'graduationCap', icon: GraduationCap, label: '학교' },
  { id: 'briefcase', icon: Briefcase, label: '회사' },
  { id: 'building', icon: Building2, label: '사무실' },
  { id: 'users', icon: Users, label: '모임' },
  { id: 'handshake', icon: Handshake, label: '미팅' },
  { id: 'party', icon: PartyPopper, label: '파티' },
  { id: 'mapPin', icon: MapPin, label: '장소' },
];

const CATEGORIES = [
  { id: 'casual', label: '일상' },
  { id: 'service', label: '서비스' },
  { id: 'formal', label: '격식' },
  { id: 'work', label: '업무' },
];

const CONTEXT_SUGGESTIONS = [
  '처음 만나는 상황',
  '도움을 요청하는 상황',
  '주문하는 상황',
  '질문하는 상황',
  '인사하는 상황',
  '약속을 잡는 상황',
  '감사를 표현하는 상황',
  '사과하는 상황',
];

const normalizeTopic = (value: string) => value.trim().toLowerCase();
const toStringArray = (value: unknown): string[] => (
  Array.isArray(value) ? value.map(String).filter((item) => item.trim().length > 0) : []
);

type CreationMode = 'manual' | 'ai';

type RecommendedSituation = {
  id: string;
  name_ko: string;
  name_en: string;
  description_ko: string;
  icon: string;
  category: string;
  contexts: string[];
};

const getAvatarText = (avatar: any) => {
  const values = [
    avatar?.relationship,
    avatar?.role,
    avatar?.name_ko,
    avatar?.name,
    avatar?.description_ko,
    avatar?.description,
  ];
  return values.filter(Boolean).join(' ').toLowerCase();
};

const findTopicOverlap = (left: string[], right: string[]) => {
  const normalizedRight = right.map(normalizeTopic);
  return left.find((topic) => {
    const normalizedTopic = normalizeTopic(topic);
    return normalizedRight.some((candidate) => (
      normalizedTopic.includes(candidate) || candidate.includes(normalizedTopic)
    ));
  });
};

const personalizeRecommendations = (
  situations: RecommendedSituation[],
  avatar: any,
  userProfile: UserProfile | null,
): RecommendedSituation[] => {
  const userLikes = toStringArray(userProfile?.interests);
  const userDislikes = toStringArray(userProfile?.dislikes);
  const avatarLikes = toStringArray(avatar?.interests);
  const avatarDislikes = toStringArray(avatar?.dislikes);
  const sharedLike = findTopicOverlap(userLikes, avatarLikes);
  const sharedDislike = findTopicOverlap(userDislikes, avatarDislikes);
  const userLikeAvatarDislikes = findTopicOverlap(userLikes, avatarDislikes);
  const avatarLikeUserDislikes = findTopicOverlap(avatarLikes, userDislikes);
  const avoidTopic = sharedDislike || userLikeAvatarDislikes || avatarLikeUserDislikes;
  const focusTopic = sharedLike || avatarLikes[0] || userLikes[0];

  return situations.map((situation, index) => {
    if (index === 0 && focusTopic) {
      return {
        ...situation,
        id: `${situation.id}_personalized`,
        description_ko: `${situation.description_ko} 공통 관심사나 자연스러운 화제로 "${focusTopic}" 이야기를 활용합니다.`,
        contexts: Array.from(new Set([...situation.contexts, '질문하는 상황'])),
      };
    }

    if (avoidTopic) {
      return {
        ...situation,
        id: `${situation.id}_avoid`,
        description_ko: `${situation.description_ko} 서로 불편할 수 있는 "${avoidTopic}" 이야기는 피하면서 대화를 이어갑니다.`,
        contexts: Array.from(new Set([...situation.contexts, '질문하는 상황'])),
      };
    }

    return situation;
  });
};

const buildRecommendedSituations = (avatar: any): RecommendedSituation[] => {
  const avatarText = getAvatarText(avatar);

  if (avatarText.includes('professor') || avatarText.includes('교수')) {
    return [
      {
        id: 'professor_feedback',
        name_ko: '과제 피드백 요청하기',
        name_en: 'Asking for Assignment Feedback',
        description_ko: '과제 방향이 맞는지 교수님께 정중하게 확인하고 조언을 구합니다.',
        icon: 'graduationCap',
        category: 'formal',
        contexts: ['도움을 요청하는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'professor_office_hours',
        name_ko: '면담 시간 조율하기',
        name_en: 'Scheduling Office Hours',
        description_ko: '수업 내용이나 진로 상담을 위해 교수님께 가능한 시간을 여쭤봅니다.',
        icon: 'building',
        category: 'formal',
        contexts: ['약속을 잡는 상황', '질문하는 상황', '인사하는 상황'],
      },
      {
        id: 'professor_extension',
        name_ko: '제출 기한 문의하기',
        name_en: 'Asking About a Deadline',
        description_ko: '과제 제출 일정이나 지연 가능성을 교수님께 조심스럽게 문의합니다.',
        icon: 'graduationCap',
        category: 'formal',
        contexts: ['질문하는 상황', '사과하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'professor_research',
        name_ko: '연구 주제 상담하기',
        name_en: 'Discussing a Research Topic',
        description_ko: '관심 있는 연구 주제에 대해 교수님께 의견과 방향을 여쭤봅니다.',
        icon: 'building',
        category: 'formal',
        contexts: ['질문하는 상황', '도움을 요청하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'professor_class_question',
        name_ko: '수업 내용 질문하기',
        name_en: 'Asking About Class Content',
        description_ko: '이해하지 못한 수업 내용을 교수님께 정중하게 다시 설명해 달라고 요청합니다.',
        icon: 'graduationCap',
        category: 'formal',
        contexts: ['질문하는 상황', '도움을 요청하는 상황', '인사하는 상황'],
      },
    ];
  }

  if (avatarText.includes('senior') || avatarText.includes('선배')) {
    return [
      {
        id: 'senior_advice',
        name_ko: '선배에게 조언 구하기',
        name_en: 'Asking a Senior for Advice',
        description_ko: '학교생활이나 동아리 활동에 대해 선배에게 자연스럽게 조언을 구합니다.',
        icon: 'users',
        category: 'casual',
        contexts: ['도움을 요청하는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'senior_project',
        name_ko: '팀 프로젝트 역할 묻기',
        name_en: 'Asking About a Project Role',
        description_ko: '팀 프로젝트에서 맡을 역할과 진행 방식을 선배에게 확인합니다.',
        icon: 'handshake',
        category: 'work',
        contexts: ['질문하는 상황', '도움을 요청하는 상황', '약속을 잡는 상황'],
      },
      {
        id: 'senior_career',
        name_ko: '진로 경험 물어보기',
        name_en: 'Asking About Career Experience',
        description_ko: '선배의 경험을 바탕으로 진로 선택이나 준비 방법을 물어봅니다.',
        icon: 'briefcase',
        category: 'casual',
        contexts: ['질문하는 상황', '도움을 요청하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'senior_club',
        name_ko: '동아리 활동 조언받기',
        name_en: 'Getting Club Advice',
        description_ko: '동아리나 학교 활동에서 어떻게 행동하면 좋을지 선배에게 조언을 구합니다.',
        icon: 'users',
        category: 'casual',
        contexts: ['도움을 요청하는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'senior_meeting',
        name_ko: '스터디 약속 잡기',
        name_en: 'Planning a Study Meeting',
        description_ko: '선배와 함께 공부하거나 자료를 확인할 시간을 자연스럽게 정합니다.',
        icon: 'coffee',
        category: 'casual',
        contexts: ['약속을 잡는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
    ];
  }

  if (avatarText.includes('boss') || avatarText.includes('manager') || avatarText.includes('상사') || avatarText.includes('팀장')) {
    return [
      {
        id: 'boss_progress',
        name_ko: '업무 진행 상황 보고하기',
        name_en: 'Reporting Work Progress',
        description_ko: '상사에게 현재 진행 상황과 막힌 부분을 간결하고 공손하게 보고합니다.',
        icon: 'briefcase',
        category: 'work',
        contexts: ['질문하는 상황', '도움을 요청하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'boss_deadline',
        name_ko: '마감 일정 조율하기',
        name_en: 'Discussing a Deadline',
        description_ko: '업무 마감 일정이나 우선순위를 상사와 조심스럽게 조율합니다.',
        icon: 'building',
        category: 'work',
        contexts: ['약속을 잡는 상황', '질문하는 상황', '사과하는 상황'],
      },
      {
        id: 'boss_feedback',
        name_ko: '업무 피드백 요청하기',
        name_en: 'Requesting Work Feedback',
        description_ko: '완성한 업무나 초안에 대해 상사에게 개선점을 정중하게 요청합니다.',
        icon: 'briefcase',
        category: 'work',
        contexts: ['도움을 요청하는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'boss_problem',
        name_ko: '문제 상황 공유하기',
        name_en: 'Sharing a Work Issue',
        description_ko: '업무 중 생긴 문제를 숨기지 않고 상사에게 차분하게 설명합니다.',
        icon: 'building',
        category: 'work',
        contexts: ['질문하는 상황', '도움을 요청하는 상황', '사과하는 상황'],
      },
      {
        id: 'boss_meeting',
        name_ko: '회의 의견 말하기',
        name_en: 'Giving an Opinion in a Meeting',
        description_ko: '회의에서 상사에게 자신의 의견을 조심스럽지만 분명하게 전달합니다.',
        icon: 'handshake',
        category: 'work',
        contexts: ['질문하는 상황', '감사를 표현하는 상황', '인사하는 상황'],
      },
    ];
  }

  if (avatarText.includes('customer') || avatarText.includes('고객') || avatarText.includes('손님')) {
    return [
      {
        id: 'customer_request',
        name_ko: '고객 요청 응대하기',
        name_en: 'Responding to a Customer Request',
        description_ko: '고객의 요청을 확인하고 가능한 해결 방법을 친절하게 안내합니다.',
        icon: 'shoppingBag',
        category: 'service',
        contexts: ['도움을 요청하는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'customer_problem',
        name_ko: '불편 사항 사과하기',
        name_en: 'Apologizing for an Issue',
        description_ko: '고객이 불편을 말했을 때 사과하고 다음 조치를 설명합니다.',
        icon: 'handshake',
        category: 'service',
        contexts: ['사과하는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'customer_recommendation',
        name_ko: '상품 추천하기',
        name_en: 'Recommending an Option',
        description_ko: '고객의 취향과 필요를 물어본 뒤 적절한 선택지를 추천합니다.',
        icon: 'shoppingBag',
        category: 'service',
        contexts: ['질문하는 상황', '도움을 요청하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'customer_order',
        name_ko: '주문 확인하기',
        name_en: 'Confirming an Order',
        description_ko: '고객의 주문 내용을 다시 확인하고 필요한 정보를 친절하게 묻습니다.',
        icon: 'utensils',
        category: 'service',
        contexts: ['주문하는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'customer_delay',
        name_ko: '대기 시간 안내하기',
        name_en: 'Explaining a Delay',
        description_ko: '고객에게 대기나 지연 상황을 공손하게 설명하고 양해를 구합니다.',
        icon: 'mapPin',
        category: 'service',
        contexts: ['사과하는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
    ];
  }

  if (avatarText.includes('interviewer') || avatarText.includes('면접')) {
    return [
      {
        id: 'interviewer_intro',
        name_ko: '면접 자기소개하기',
        name_en: 'Introducing Yourself in an Interview',
        description_ko: '면접관에게 경험과 강점을 격식 있게 소개하고 후속 질문에 답합니다.',
        icon: 'briefcase',
        category: 'formal',
        contexts: ['처음 만나는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'interviewer_question',
        name_ko: '면접 질문 되묻기',
        name_en: 'Clarifying an Interview Question',
        description_ko: '질문을 정확히 이해하지 못했을 때 정중하게 확인하고 답변합니다.',
        icon: 'handshake',
        category: 'formal',
        contexts: ['질문하는 상황', '사과하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'interviewer_strength',
        name_ko: '강점 설명하기',
        name_en: 'Explaining Your Strengths',
        description_ko: '면접관에게 자신의 강점과 경험을 구체적인 예시로 설명합니다.',
        icon: 'briefcase',
        category: 'formal',
        contexts: ['질문하는 상황', '감사를 표현하는 상황', '처음 만나는 상황'],
      },
      {
        id: 'interviewer_weakness',
        name_ko: '약점 질문 답하기',
        name_en: 'Answering a Weakness Question',
        description_ko: '약점이나 부족한 점을 묻는 질문에 솔직하지만 균형 있게 답합니다.',
        icon: 'handshake',
        category: 'formal',
        contexts: ['질문하는 상황', '사과하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'interviewer_closing',
        name_ko: '면접 마무리 인사하기',
        name_en: 'Closing an Interview',
        description_ko: '면접 마지막에 감사 인사를 전하고 후속 절차를 정중하게 확인합니다.',
        icon: 'users',
        category: 'formal',
        contexts: ['감사를 표현하는 상황', '질문하는 상황', '인사하는 상황'],
      },
    ];
  }

  if (avatarText.includes('friend') || avatarText.includes('친구')) {
    return [
      {
        id: 'friend_plan',
        name_ko: '카페 약속 잡기',
        name_en: 'Making Cafe Plans',
        description_ko: '친구와 편하게 시간과 장소를 정하고 취향을 물어봅니다.',
        icon: 'coffee',
        category: 'casual',
        contexts: ['약속을 잡는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'friend_help',
        name_ko: '친구에게 부탁하기',
        name_en: 'Asking a Friend for a Favor',
        description_ko: '친구에게 작은 도움을 부탁하고 고마움을 자연스럽게 표현합니다.',
        icon: 'users',
        category: 'casual',
        contexts: ['도움을 요청하는 상황', '감사를 표현하는 상황', '사과하는 상황'],
      },
      {
        id: 'friend_movie',
        name_ko: '같이 볼 콘텐츠 고르기',
        name_en: 'Choosing Something to Watch',
        description_ko: '친구와 보고 싶은 콘텐츠나 취향을 편하게 이야기하며 선택합니다.',
        icon: 'party',
        category: 'casual',
        contexts: ['질문하는 상황', '약속을 잡는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'friend_apology',
        name_ko: '약속 변경 사과하기',
        name_en: 'Apologizing for Changing Plans',
        description_ko: '친구에게 약속 변경을 말하고 미안한 마음을 자연스럽게 전합니다.',
        icon: 'users',
        category: 'casual',
        contexts: ['사과하는 상황', '약속을 잡는 상황', '감사를 표현하는 상황'],
      },
      {
        id: 'friend_trip',
        name_ko: '주말 계획 이야기하기',
        name_en: 'Talking About Weekend Plans',
        description_ko: '친구와 주말에 무엇을 할지 취향을 묻고 편하게 계획을 세웁니다.',
        icon: 'mapPin',
        category: 'casual',
        contexts: ['약속을 잡는 상황', '질문하는 상황', '감사를 표현하는 상황'],
      },
    ];
  }

  return [
    {
      id: 'default_first_meeting',
      name_ko: '처음 만나 인사하기',
      name_en: 'First Meeting Greeting',
      description_ko: '상대와 처음 만난 상황에서 자연스럽게 인사하고 기본 정보를 묻습니다.',
      icon: 'users',
      category: 'casual',
      contexts: ['처음 만나는 상황', '인사하는 상황', '질문하는 상황'],
    },
    {
      id: 'default_help',
      name_ko: '정중하게 도움 요청하기',
      name_en: 'Politely Asking for Help',
      description_ko: '상대와의 관계에 맞는 말투로 필요한 도움을 요청합니다.',
      icon: 'handshake',
      category: 'formal',
      contexts: ['도움을 요청하는 상황', '질문하는 상황', '감사를 표현하는 상황'],
    },
    {
      id: 'default_plan',
      name_ko: '약속 시간 정하기',
      name_en: 'Setting a Meeting Time',
      description_ko: '상대와 가능한 시간을 확인하고 부담스럽지 않게 약속을 조율합니다.',
      icon: 'coffee',
      category: 'casual',
      contexts: ['약속을 잡는 상황', '질문하는 상황', '감사를 표현하는 상황'],
    },
    {
      id: 'default_question',
      name_ko: '궁금한 점 물어보기',
      name_en: 'Asking a Question',
      description_ko: '상대에게 궁금한 내용을 관계에 맞는 말투로 자연스럽게 질문합니다.',
      icon: 'handshake',
      category: 'formal',
      contexts: ['질문하는 상황', '인사하는 상황', '감사를 표현하는 상황'],
    },
    {
      id: 'default_thanks',
      name_ko: '도움에 감사 표현하기',
      name_en: 'Thanking Someone for Help',
      description_ko: '상대가 도와준 뒤 고마움을 구체적이고 자연스럽게 표현합니다.',
      icon: 'users',
      category: 'casual',
      contexts: ['감사를 표현하는 상황', '인사하는 상황', '질문하는 상황'],
    },
  ];
};

export default function CreateSituationScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const avatar = route.params?.avatar;
  const editing = route.params?.editing as any | undefined;
  const mode = (route.params?.mode || 'manual') as CreationMode;
  const isEditing = !!editing;

  const [name, setName] = useState(editing?.name_ko || '');
  const [nameEn, setNameEn] = useState(editing?.name_en || '');
  const [description, setDescription] = useState(editing?.description_ko || '');
  const [selectedIcon, setSelectedIcon] = useState(editing?.icon || 'coffee');
  const [selectedCategory, setSelectedCategory] = useState(editing?.category || 'casual');
  const [contexts, setContexts] = useState<string[]>(editing?.contexts || []);
  const [customContext, setCustomContext] = useState('');
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const fallbackRecommendations = useMemo(
    () => personalizeRecommendations(buildRecommendedSituations(avatar), avatar, userProfile),
    [avatar, userProfile],
  );
  const [recommendations, setRecommendations] = useState<RecommendedSituation[]>(fallbackRecommendations);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
  const [selectedRecommendation, setSelectedRecommendation] = useState<string | null>(editing?.recommendationId || null);
  const [isSaving, setIsSaving] = useState(false);

  const avatarId = avatar?.id || avatar?.name_ko || avatar?.name || editing?.avatarId || 'default_avatar';
  const avatarName = avatar?.name_ko || avatar?.name || editing?.avatarName;

  useEffect(() => {
    getMyProfile()
      .then(setUserProfile)
      .catch((error) => console.log('Failed to load user profile for situation recommendations:', error))
      .finally(() => setProfileLoaded(true));
  }, []);

  useEffect(() => {
    setRecommendations(fallbackRecommendations);
  }, [fallbackRecommendations]);

  useEffect(() => {
    if (mode !== 'ai' || isEditing || !profileLoaded) return;

    let isMounted = true;
    const loadRecommendations = async () => {
      setIsLoadingRecommendations(true);
      try {
        const response = await fetch(`${AI_SERVER}/api/v1/chat/suggest-situations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            avatar: avatar || {},
            user_profile: userProfile || {},
            count: 5,
          }),
        });

        if (!response.ok) throw new Error(`Situation recommendation error: ${response.status}`);
        const data = await response.json();
        if (isMounted && Array.isArray(data?.situations) && data.situations.length > 0) {
          setRecommendations(data.situations);
        }
      } catch (error) {
        console.log('Failed to load AI situation recommendations:', error);
        if (isMounted) setRecommendations(fallbackRecommendations);
      } finally {
        if (isMounted) setIsLoadingRecommendations(false);
      }
    };

    loadRecommendations();
    return () => {
      isMounted = false;
    };
  }, [avatar, fallbackRecommendations, isEditing, mode, profileLoaded, userProfile]);

  const toggleContext = (context: string) => {
    if (contexts.includes(context)) {
      setContexts(contexts.filter((c) => c !== context));
    } else {
      setContexts([...contexts, context]);
    }
  };

  const addCustomContext = () => {
    if (customContext.trim() && !contexts.includes(customContext.trim())) {
      setContexts([...contexts, customContext.trim()]);
      setCustomContext('');
    }
  };

  const applyRecommendation = (recommendation: RecommendedSituation) => {
    setSelectedRecommendation(recommendation.id);
    setName(recommendation.name_ko);
    setNameEn(recommendation.name_en);
    setDescription(recommendation.description_ko);
    setSelectedIcon(recommendation.icon);
    setSelectedCategory(recommendation.category);
    setContexts(recommendation.contexts);
  };

  const handleCreate = async () => {
    if (!name.trim() || !description.trim()) return;

    setIsSaving(true);

    try {
      const situationPayload = {
        id: editing?.id || `custom_${Date.now()}`,
        name_ko: name.trim(),
        name_en: nameEn.trim(),
        description_ko: description.trim(),
        icon: selectedIcon as IconName,
        category: selectedCategory,
        contexts,
        isCustom: true,
        avatarId,
        avatarName,
        source: isEditing ? editing?.source || 'manual' : mode,
        recommendationId: selectedRecommendation,
      };

      const existing = await AsyncStorage.getItem(CUSTOM_SITUATIONS_KEY);
      const existingList: any[] = existing ? JSON.parse(existing) : [];

      const updatedList = isEditing
        ? existingList.map((s) => (s.id === editing.id ? situationPayload : s))
        : [...existingList, situationPayload];

      await AsyncStorage.setItem(CUSTOM_SITUATIONS_KEY, JSON.stringify(updatedList));

      Alert.alert(
        '완료',
        `"${name}" 상황이 ${isEditing ? '수정' : '저장'}되었습니다.`,
        [{ text: '확인', onPress: () => navigation.goBack() }],
      );
    } catch (error) {
      console.log('Failed to save situation:', error);
      Alert.alert('오류', '상황 저장에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsSaving(false);
    }
  };

  const isValid = name.trim().length > 0 && description.trim().length > 0;

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <Header title={isEditing ? '상황 수정하기' : mode === 'ai' ? 'AI 추천 상황' : '새 상황 만들기'} />

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {mode === 'ai' && !isEditing && (
          <View style={styles.recommendationSection}>
            <View style={styles.recommendationHeader}>
              <Sparkles size={18} color="#6C3BFF" />
              <Text style={styles.recommendationTitle}>이 아바타에게 어울리는 상황</Text>
            </View>
            <Text style={styles.recommendationHint}>
              추천을 고르면 아래 입력칸에 채워지고, 원하는 대로 수정할 수 있어요.
            </Text>
            {isLoadingRecommendations && (
              <View style={styles.recommendationLoading}>
                <ActivityIndicator size="small" color="#6C3BFF" />
                <Text style={styles.recommendationLoadingText}>상황을 만들고 있어요</Text>
              </View>
            )}
            <View style={styles.recommendationList}>
              {recommendations.map((recommendation) => {
                const isSelected = selectedRecommendation === recommendation.id;
                return (
                  <TouchableOpacity
                    key={recommendation.id}
                    style={[
                      styles.recommendationCard,
                      isSelected && styles.recommendationCardActive,
                    ]}
                    onPress={() => applyRecommendation(recommendation)}
                  >
                    <View style={styles.recommendationCardTop}>
                      <View style={styles.recommendationIcon}>
                        {React.createElement(
                          SITUATION_ICONS.find((i) => i.id === recommendation.icon)?.icon || Sparkles,
                          { size: 20, color: '#6C3BFF' },
                        )}
                      </View>
                      {isSelected && <Check size={18} color="#6C3BFF" />}
                    </View>
                    <Text style={styles.recommendationName}>{recommendation.name_ko}</Text>
                    <Text style={styles.recommendationDesc}>{recommendation.description_ko}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        )}

        {/* Name */}
        <InputField
          label="상황 이름 (한국어) *"
          value={name}
          onChangeText={setName}
          placeholder="예: 도서관에서 공부"
        />

        <InputField
          label="상황 이름 (영어)"
          value={nameEn}
          onChangeText={setNameEn}
          placeholder="예: Studying at Library"
        />

        {/* Description */}
        <InputField
          label="상황 설명 *"
          value={description}
          onChangeText={setDescription}
          placeholder="이 상황에서 어떤 대화가 이루어지나요?"
          multiline
          numberOfLines={3}
        />

        {/* Icon Selection */}
        <Text style={styles.fieldLabel}>아이콘 선택</Text>
        <View style={styles.iconGrid}>
          {SITUATION_ICONS.map((item) => (
            <TouchableOpacity
              key={item.id}
              style={[
                styles.iconButton,
                selectedIcon === item.id && styles.iconButtonActive,
              ]}
              onPress={() => setSelectedIcon(item.id)}
            >
              <item.icon 
                size={24} 
                color={selectedIcon === item.id ? '#FFFFFF' : '#6C6C80'} 
              />
              <Text style={[
                styles.iconLabel,
                selectedIcon === item.id && styles.iconLabelActive,
              ]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Category */}
        <Text style={styles.fieldLabel}>카테고리</Text>
        <View style={styles.categoryRow}>
          {CATEGORIES.map((cat) => (
            <TouchableOpacity
              key={cat.id}
              style={[
                styles.categoryButton,
                selectedCategory === cat.id && styles.categoryButtonActive,
              ]}
              onPress={() => setSelectedCategory(cat.id)}
            >
              <Text style={[
                styles.categoryText,
                selectedCategory === cat.id && styles.categoryTextActive,
              ]}>
                {cat.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Context Suggestions */}
        <Text style={styles.fieldLabel}>상황 맥락 (선택)</Text>
        <Text style={styles.fieldHint}>AI가 더 자연스러운 대화를 생성하는 데 도움이 됩니다</Text>
        
        <View style={styles.contextGrid}>
          {CONTEXT_SUGGESTIONS.map((context) => (
            <Tag
              key={context}
              label={context}
              selected={contexts.includes(context)}
              onPress={() => toggleContext(context)}
            />
          ))}
        </View>

        {/* Custom Context Input */}
        <View style={styles.customContextRow}>
          <View style={styles.customContextInput}>
            <InputField
              value={customContext}
              onChangeText={setCustomContext}
              placeholder="직접 입력..."
            />
          </View>
          <TouchableOpacity 
            style={styles.addButton}
            onPress={addCustomContext}
          >
            <Text style={styles.addButtonText}>추가</Text>
          </TouchableOpacity>
        </View>

        {/* Selected Contexts */}
        {contexts.length > 0 && (
          <View style={styles.selectedContexts}>
            <Text style={styles.selectedLabel}>선택된 맥락:</Text>
            <View style={styles.contextGrid}>
              {contexts.map((context) => (
                <Tag
                  key={context}
                  label={context}
                  selected
                  onPress={() => toggleContext(context)}
                />
              ))}
            </View>
          </View>
        )}

        {/* Preview */}
        <Text style={styles.fieldLabel}>미리보기</Text>
        <Card variant="elevated" style={styles.previewCard}>
          <View style={styles.previewRow}>
            <View style={[styles.previewIcon, styles.previewIconActive]}>
              {SITUATION_ICONS.find((i) => i.id === selectedIcon)?.icon && 
                React.createElement(
                  SITUATION_ICONS.find((i) => i.id === selectedIcon)!.icon,
                  { size: 24, color: '#FFFFFF' }
                )
              }
            </View>
            <View style={styles.previewInfo}>
              <Text style={styles.previewName}>{name || '상황 이름'}</Text>
              <Text style={styles.previewDesc}>{description || '상황 설명'}</Text>
            </View>
          </View>
        </Card>

      </ScrollView>

      {/* Create Button */}
      <View style={styles.footer}>
        <Button
          title={isSaving ? '저장 중...' : isEditing ? '수정 완료' : '상황 만들기'}
          onPress={handleCreate}
          disabled={!isValid || isSaving}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  content: { paddingHorizontal: 20, paddingBottom: 100 },

  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1A1A2E',
    marginBottom: 10,
    marginTop: 16,
  },
  fieldHint: {
    fontSize: 12,
    color: '#6C6C80',
    marginTop: -6,
    marginBottom: 12,
  },

  recommendationSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E2E2EC',
  },
  recommendationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1A1A2E',
  },
  recommendationHint: {
    fontSize: 12,
    color: '#6C6C80',
    lineHeight: 18,
    marginBottom: 12,
  },
  recommendationLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  recommendationLoadingText: {
    fontSize: 12,
    color: '#6C6C80',
  },
  recommendationList: {
    gap: 10,
  },
  recommendationCard: {
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E2E2EC',
    backgroundColor: '#F7F7FB',
    padding: 14,
  },
  recommendationCardActive: {
    borderColor: '#6C3BFF',
    backgroundColor: '#F0EDFF',
  },
  recommendationCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  recommendationIcon: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
  },
  recommendationName: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 4,
  },
  recommendationDesc: {
    fontSize: 12,
    color: '#6C6C80',
    lineHeight: 18,
  },

  iconGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 8,
  },
  iconButton: {
    width: '18%',
    aspectRatio: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: '#E2E2EC',
  },
  iconButtonActive: {
    backgroundColor: '#6C3BFF',
    borderColor: '#6C3BFF',
  },
  iconLabel: {
    fontSize: 10,
    color: '#6C6C80',
    marginTop: 4,
  },
  iconLabelActive: {
    color: '#FFFFFF',
  },

  categoryRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 8,
  },
  categoryButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E2EC',
    alignItems: 'center',
  },
  categoryButtonActive: {
    backgroundColor: '#6C3BFF',
    borderColor: '#6C3BFF',
  },
  categoryText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6C6C80',
  },
  categoryTextActive: {
    color: '#FFFFFF',
  },

  contextGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  customContextRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 12,
    alignItems: 'flex-start',
  },
  customContextInput: {
    flex: 1,
  },
  addButton: {
    backgroundColor: '#6C3BFF',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 8,
  },
  addButtonText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 14,
  },
  selectedContexts: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#F0EDFF',
    borderRadius: 12,
  },
  selectedLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6C3BFF',
    marginBottom: 8,
  },

  previewCard: {
    marginTop: 8,
    marginBottom: 20,
  },
  previewRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  previewIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  previewIconActive: {
    backgroundColor: '#6C3BFF',
  },
  previewInfo: {
    flex: 1,
  },
  previewName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A2E',
    marginBottom: 2,
  },
  previewDesc: {
    fontSize: 13,
    color: '#6C6C80',
  },

  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#F7F7FB',
  },
});
