import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ViewStyle } from 'react-native';

interface TagProps {
  label: string;
  selected?: boolean;
  onPress?: () => void;
  variant?: 'default' | 'outline' | 'filled';
  color?: string;
  style?: ViewStyle;
}

export const Tag: React.FC<TagProps> = ({
  label,
  selected = false,
  onPress,
  variant = 'default',
  color = '#6C3BFF',
  style,
}) => {
  const tagStyles = [
    styles.tag,
    variant === 'outline' && styles.tagOutline,
    variant === 'filled' && [styles.tagFilled, { backgroundColor: color }],
    selected && [styles.tagActive, { borderColor: color, backgroundColor: color }],
    style,
  ];

  const textStyles = [
    styles.tagText,
    variant === 'filled' && styles.tagTextFilled,
    selected && styles.tagTextActive,
  ];

  return (
    <TouchableOpacity style={tagStyles} onPress={onPress} activeOpacity={0.7}>
      <Text style={textStyles}>{label}</Text>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  tag: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: '#E2E2EC',
    backgroundColor: '#FFFFFF',
  },
  tagOutline: {
    backgroundColor: 'transparent',
  },
  tagFilled: {
    borderWidth: 0,
  },
  tagActive: {
    backgroundColor: '#6C3BFF',
    borderColor: '#6C3BFF',
  },
  tagText: {
    fontSize: 12,
    color: '#6C6C80',
    fontWeight: '500',
  },
  tagTextFilled: {
    color: '#FFFFFF',
  },
  tagTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
});
