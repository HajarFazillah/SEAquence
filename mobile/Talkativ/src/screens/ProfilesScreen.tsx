import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet,
  TouchableOpacity, Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Plus, User } from 'lucide-react-native';
import { Card, Button } from '../components';

// Mock profiles
const mockProfiles = [
  {
    id: '1',
    name: 'Nunnalin',
    avatarUrl: 'https://i.pravatar.cc/100?img=47',
    level: '중급',
  },
];

export default function ProfilesScreen() {
  const navigation = useNavigation<any>();

  const handleSelectProfile = (profileId: string) => {
    navigation.navigate('Main');
  };

  const handleCreateProfile = () => {
    navigation.navigate('CreateProfileStep1');
  };

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>프로필 선택</Text>
          <Text style={styles.subtitle}>학습할 프로필을 선택하세요</Text>
        </View>

        {/* Profiles */}
        <View style={styles.profilesGrid}>
          {mockProfiles.map((profile) => (
            <TouchableOpacity
              key={profile.id}
              style={styles.profileCard}
              onPress={() => handleSelectProfile(profile.id)}
            >
              <Image source={{ uri: profile.avatarUrl }} style={styles.profileAvatar} />
              <Text style={styles.profileName}>{profile.name}</Text>
              <Text style={styles.profileLevel}>{profile.level}</Text>
            </TouchableOpacity>
          ))}

          {/* Add Profile */}
          <TouchableOpacity style={styles.addProfileCard} onPress={handleCreateProfile}>
            <View style={styles.addProfileIcon}>
              <Plus size={32} color="#6C3BFF" />
            </View>
            <Text style={styles.addProfileText}>새 프로필</Text>
          </TouchableOpacity>
        </View>

        {/* Continue Button */}
        <View style={styles.footer}>
          <Button
            title="계속하기"
            onPress={() => navigation.navigate('Main')}
            disabled={mockProfiles.length === 0}
          />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F7F7FB' },
  container: { flex: 1, paddingHorizontal: 24 },

  // Header
  header: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1A1A2E',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: '#6C6C80',
  },

  // Profiles Grid
  profilesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 16,
  },
  profileCard: {
    width: 140,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  profileAvatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#E8E8F0',
    marginBottom: 12,
  },
  profileName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1A1A2E',
    marginBottom: 4,
  },
  profileLevel: {
    fontSize: 12,
    color: '#6C6C80',
  },

  // Add Profile
  addProfileCard: {
    width: 140,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 20,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#6C3BFF',
    borderStyle: 'dashed',
  },
  addProfileIcon: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: '#F0EDFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  addProfileText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6C3BFF',
  },

  // Footer
  footer: {
    position: 'absolute',
    bottom: 40,
    left: 24,
    right: 24,
  },
});
