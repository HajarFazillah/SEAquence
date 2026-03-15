import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { ChevronLeft, Bell } from 'lucide-react-native';

interface HeaderProps {
  title: string;
  showBack?: boolean;
  showBell?: boolean;
  onBellPress?: () => void;
  rightElement?: React.ReactNode;
  backgroundColor?: string;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  showBack = true,
  showBell = false,
  onBellPress,
  rightElement,
  backgroundColor = 'transparent',
}) => {
  const navigation = useNavigation();

  return (
    <View style={[styles.header, { backgroundColor }]}>
      {showBack ? (
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <ChevronLeft size={24} color="#1A1A2E" />
        </TouchableOpacity>
      ) : (
        <View style={styles.headerBtn} />
      )}

      <Text style={styles.headerTitle}>{title}</Text>

      {rightElement ? (
        rightElement
      ) : showBell ? (
        <TouchableOpacity style={styles.headerBtn} onPress={onBellPress}>
          <Bell size={22} color="#1A1A2E" />
        </TouchableOpacity>
      ) : (
        <View style={styles.headerBtn} />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 14,
  },
  headerBtn: {
    width: 36,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1A1A2E',
  },
});
