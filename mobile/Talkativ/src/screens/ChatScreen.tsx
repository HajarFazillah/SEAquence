import React, { useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  SafeAreaView, FlatList, TextInput, KeyboardAvoidingView, Platform,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';

// Mock messages — replace with real API later
const mockMessages = [
  { id: '1', text: '안녕하세요. 토커티브입니다.', sender: 'ai' },
  { id: '2', text: 'Yes', sender: 'user' },
  { id: '3', text: "you can use 'word' for 'word'", sender: 'ai' },
  { id: '4', text: 'Yes', sender: 'user' },
];

export default function ChatScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const profileName = route.params?.name ?? '김예은';
  const profileBg   = route.params?.avatarBg ?? '#FFB6C1';

  const [messages, setMessages] = useState(mockMessages);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), text: input.trim(), sender: 'user' },
    ]);
    setInput('');
    // TODO: call AI API here later
  };

  return (
    <SafeAreaView style={styles.safe}>

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <Text style={styles.backArrow}>◀</Text>
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <View style={[styles.headerAvatar, { backgroundColor: profileBg }]}>
            <Text style={styles.headerAvatarEmoji}>👜</Text>
          </View>
          <Text style={styles.headerName}>{profileName}</Text>
        </View>
        <TouchableOpacity style={styles.headerBtn}>
          <Text style={styles.bellIcon}>🔔</Text>
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={0}
      >
        {/* Messages */}
        <FlatList
          data={messages}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.messageList}
          renderItem={({ item }) => (
            <View style={[
              styles.bubbleRow,
              item.sender === 'user' ? styles.bubbleRowUser : styles.bubbleRowAi,
            ]}>
              <View style={[
                styles.bubble,
                item.sender === 'user' ? styles.bubbleUser : styles.bubbleAi,
              ]}>
                <Text style={[
                  styles.bubbleText,
                  item.sender === 'user' && styles.bubbleTextUser,
                ]}>
                  {item.text}
                </Text>
              </View>
            </View>
          )}
          ListFooterComponent={
            <View>
              {/* TODO: Word correction widget — show conditionally when AI activates */}
              {/* <CorrectionWidget original="better" corrected="correction" /> */}

              {/* TODO: Conversation status — show at end of session */}
              {/* <ConversationStatus status="Perfect conversation" /> */}
            </View>
          }
        />

        {/* Chat Input */}
        <View style={styles.inputBar}>
          <TextInput
            style={styles.input}
            placeholder="Chat"
            placeholderTextColor="#C0C0D0"
            value={input}
            onChangeText={setInput}
            returnKeyType="send"
            onSubmitEditing={handleSend}
          />
          <TouchableOpacity style={styles.sendBtn} onPress={handleSend}>
            <Text style={styles.sendText}>Send</Text>
          </TouchableOpacity>
        </View>

      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:               { flex: 1, backgroundColor: '#FFFFFF' },

  // Header
  header:             { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14, borderBottomWidth: 1, borderBottomColor: '#F0F0F8' },
  headerBtn:          { width: 36, alignItems: 'center' },
  backArrow:          { fontSize: 18, color: '#1A1A2E' },
  bellIcon:           { fontSize: 20 },
  headerCenter:       { flexDirection: 'row', alignItems: 'center', gap: 8 },
  headerAvatar:       { width: 32, height: 32, borderRadius: 16, alignItems: 'center', justifyContent: 'center' },
  headerAvatarEmoji:  { fontSize: 16 },
  headerName:         { fontSize: 16, fontWeight: '700', color: '#1A1A2E' },

  // Messages
  messageList:        { padding: 20, gap: 12 },
  bubbleRow:          { flexDirection: 'row' },
  bubbleRowAi:        { justifyContent: 'flex-start' },
  bubbleRowUser:      { justifyContent: 'flex-end' },
  bubble:             { maxWidth: '75%', paddingHorizontal: 16, paddingVertical: 12, borderRadius: 20 },
  bubbleAi:           { backgroundColor: '#F5F5FA', borderBottomLeftRadius: 4 },
  bubbleUser:         { backgroundColor: '#6C3BFF', borderBottomRightRadius: 4 },
  bubbleText:         { fontSize: 14, color: '#1A1A2E', lineHeight: 20 },
  bubbleTextUser:     { color: '#FFFFFF' },

  // Input bar
  inputBar:           { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingVertical: 12, borderTopWidth: 1, borderTopColor: '#F0F0F8', backgroundColor: '#FFFFFF', gap: 10 },
  input:              { flex: 1, backgroundColor: '#F5F5FA', borderRadius: 24, paddingHorizontal: 16, paddingVertical: 10, fontSize: 14, color: '#1A1A2E' },
  sendBtn:            { backgroundColor: '#6C3BFF', borderRadius: 20, paddingHorizontal: 20, paddingVertical: 10 },
  sendText:           { color: '#FFFFFF', fontWeight: '600', fontSize: 14 },
});
