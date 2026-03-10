import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export const MyProfileScreen: React.FC = () => (
  <View style={styles.container}>
    <Text>My Profile</Text>
  </View>
);

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', alignItems: 'center' },
});
