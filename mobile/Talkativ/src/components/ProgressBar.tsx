import React from 'react';
import { View, StyleSheet, ViewStyle } from 'react-native';

interface ProgressBarProps {
  progress: number; // 0 to 1
  color?: string;
  backgroundColor?: string;
  height?: number;
  style?: ViewStyle;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  color = '#6C3BFF',
  backgroundColor = '#E2E2EC',
  height = 6,
  style,
}) => {
  const clampedProgress = Math.min(Math.max(progress, 0), 1);

  return (
    <View style={[styles.background, { height, backgroundColor }, style]}>
      <View
        style={[
          styles.fill,
          {
            width: `${clampedProgress * 100}%`,
            backgroundColor: color,
            height,
          },
        ]}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  background: {
    borderRadius: 4,
    overflow: 'hidden',
  },
  fill: {
    borderRadius: 4,
  },
});
