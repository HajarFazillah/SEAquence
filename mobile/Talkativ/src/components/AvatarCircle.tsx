import React from 'react';
import { View, Text, StyleSheet, ViewStyle, Image } from 'react-native';
import { User } from 'lucide-react-native';

interface AvatarCircleProps {
  emoji?: string;
  imageUrl?: string;
  backgroundColor?: string;
  size?: 'small' | 'medium' | 'large' | 'xlarge';
  style?: ViewStyle;
  showIcon?: boolean;
}

const SIZES = {
  small: { container: 32, emoji: 14, image: 32, icon: 16 },
  medium: { container: 48, emoji: 22, image: 48, icon: 24 },
  large: { container: 64, emoji: 28, image: 64, icon: 32 },
  xlarge: { container: 80, emoji: 36, image: 80, icon: 40 },
};

export const AvatarCircle: React.FC<AvatarCircleProps> = ({
  emoji,
  imageUrl,
  backgroundColor = '#FFB6C1',
  size = 'medium',
  style,
  showIcon = false,
}) => {
  const sizeStyle = SIZES[size];

  return (
    <View
      style={[
        styles.container,
        {
          width: sizeStyle.container,
          height: sizeStyle.container,
          borderRadius: sizeStyle.container / 2,
          backgroundColor,
        },
        style,
      ]}
    >
      {imageUrl ? (
        <Image 
          source={{ uri: imageUrl }} 
          style={{ 
            width: sizeStyle.image, 
            height: sizeStyle.image, 
            borderRadius: sizeStyle.image / 2 
          }} 
        />
      ) : emoji ? (
        <Text style={{ fontSize: sizeStyle.emoji }}>{emoji}</Text>
      ) : showIcon ? (
        <User size={sizeStyle.icon} color="#FFFFFF" />
      ) : (
        <Text style={{ fontSize: sizeStyle.emoji }}>👤</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
});
