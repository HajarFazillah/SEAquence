import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';

type SpeechLevel = 'formal' | 'polite' | 'informal';

interface SpeechLevelBadgeProps {
  level: SpeechLevel;
  size?: 'small' | 'medium' | 'large';
  style?: ViewStyle;
}

const LEVEL_CONFIG: Record<SpeechLevel, { 
  bg: string; 
  color: string; 
  label: string; 
  labelKo: string;
  endings: string;
}> = {
  formal: { 
    bg: '#EAE8FF', 
    color: '#6C3BFF', 
    label: 'Formal',
    labelKo: '합쇼체',
    endings: '-습니다, -습니까',
  },
  polite: { 
    bg: '#E8F5E9', 
    color: '#4CAF50', 
    label: 'Polite',
    labelKo: '해요체',
    endings: '-어요, -아요',
  },
  informal: { 
    bg: '#FFF0E0', 
    color: '#F4A261', 
    label: 'Informal',
    labelKo: '반말',
    endings: '-어, -아, -야',
  },
};

export const SpeechLevelBadge: React.FC<SpeechLevelBadgeProps> = ({ 
  level, 
  size = 'medium',
  style,
}) => {
  const config = LEVEL_CONFIG[level];

  return (
    <View style={[styles.container, styles[`container_${size}`], { backgroundColor: config.bg }, style]}>
      <Text style={[styles.labelKo, styles[`text_${size}`], { color: config.color }]}>
        {config.labelKo}
      </Text>
      <Text style={[styles.endings, styles[`subtext_${size}`], { color: config.color }]}>
        ({config.endings})
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  container_small: {
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  container_medium: {
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  container_large: {
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  labelKo: {
    fontWeight: '700',
  },
  text_small: {
    fontSize: 12,
  },
  text_medium: {
    fontSize: 16,
  },
  text_large: {
    fontSize: 20,
  },
  endings: {
    marginTop: 2,
  },
  subtext_small: {
    fontSize: 10,
  },
  subtext_medium: {
    fontSize: 12,
  },
  subtext_large: {
    fontSize: 14,
  },
});
