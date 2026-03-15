import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ViewStyle, ActivityIndicator } from 'react-native';
import { ArrowRight } from 'lucide-react-native';

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  showArrow?: boolean;
  disabled?: boolean;
  loading?: boolean;
  style?: ViewStyle;
  size?: 'small' | 'medium' | 'large';
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  showArrow = false,
  disabled = false,
  loading = false,
  style,
  size = 'large',
}) => {
  const buttonStyles = [
    styles.button,
    styles[`button_${variant}`],
    styles[`button_${size}`],
    disabled && styles.buttonDisabled,
    style,
  ];

  const textColor = variant === 'primary' || variant === 'secondary' ? '#FFFFFF' : 
                    variant === 'ghost' ? '#6C3BFF' : '#1A1A2E';

  return (
    <TouchableOpacity 
      style={buttonStyles} 
      onPress={onPress} 
      disabled={disabled || loading}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? '#FFFFFF' : '#6C3BFF'} />
      ) : (
        <>
          <Text style={[styles.buttonText, styles[`text_${size}`], { color: textColor }]}>
            {title}
          </Text>
          {showArrow && <ArrowRight size={size === 'small' ? 16 : 18} color={textColor} style={styles.arrow} />}
        </>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  button_small: {
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  button_medium: {
    paddingVertical: 12,
    paddingHorizontal: 20,
  },
  button_large: {
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  button_primary: {
    backgroundColor: '#6C3BFF',
  },
  button_secondary: {
    backgroundColor: '#1A1A2E',
  },
  button_outline: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: '#E2E2EC',
  },
  button_ghost: {
    backgroundColor: 'transparent',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    fontWeight: '700',
  },
  text_small: {
    fontSize: 13,
  },
  text_medium: {
    fontSize: 14,
  },
  text_large: {
    fontSize: 16,
  },
  arrow: {
    marginLeft: 6,
  },
});
