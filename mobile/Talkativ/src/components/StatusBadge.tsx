import React from 'react';
import { View, Text, StyleSheet, ViewStyle } from 'react-native';

type StatusType = 'done' | 'in_progress' | 'todo' | 'active' | 'easy' | 'medium' | 'hard';

interface StatusBadgeProps {
  status: StatusType;
  label?: string;
  style?: ViewStyle;
}

const STATUS_CONFIG: Record<StatusType, { bg: string; color: string; label: string }> = {
  done: { bg: '#EAE8FF', color: '#6C3BFF', label: 'Done' },
  in_progress: { bg: '#FFF0E0', color: '#F4A261', label: 'In Progress' },
  todo: { bg: '#E8F5E9', color: '#4CAF50', label: 'To-do' },
  active: { bg: '#EAE8FF', color: '#6C3BFF', label: 'Active' },
  easy: { bg: '#E8F5E9', color: '#4CAF50', label: '쉬움' },
  medium: { bg: '#FFF0E0', color: '#F4A261', label: '보통' },
  hard: { bg: '#FFEBEE', color: '#E53935', label: '어려움' },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label, style }) => {
  const config = STATUS_CONFIG[status];

  return (
    <View style={[styles.badge, { backgroundColor: config.bg }, style]}>
      <Text style={[styles.text, { color: config.color }]}>
        {label || config.label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 10,
  },
  text: {
    fontSize: 11,
    fontWeight: '600',
  },
});
