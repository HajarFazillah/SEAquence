import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView, ScrollView,
  TouchableOpacity, TextInput,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';

const LIKE_TAGS    = ['EASY TO USE', 'COMPLETE', 'HELPFUL', 'CONVENIENT', 'LOOKS GOOD'];
const IMPROVE_TAGS = ['COULD HAVE MORE COMPONENTS', 'COMPLEX', 'NOT INTERACTIVE', 'BE MORE NATURAL'];

export default function FeedbackScreen() {
  const navigation = useNavigation<any>();
  const route      = useRoute<any>();
  const avatar     = route.params?.avatar;
  const duration   = route.params?.duration ?? '00:00';

  const [rating, setRating]               = useState(4);
  const [selectedLikes, setSelectedLikes] = useState<string[]>(['HELPFUL']);
  const [selectedImprove, setSelectedImprove] = useState<string[]>(['BE MORE NATURAL']);
  const [feedback, setFeedback]           = useState('');

  const toggleTag = (
    tag: string,
    selected: string[],
    setSelected: (v: string[]) => void
  ) => {
    setSelected(
      selected.includes(tag) ? selected.filter((t) => t !== tag) : [...selected, tag]
    );
  };

  const handleSubmit = () => {
    // TODO: send feedback to API
    navigation.navigate('Analytics', { avatar, duration, rating });
  };

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.headerBtn}>
          <Text style={styles.backArrow}>◀</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Feedback</Text>
        <View style={styles.headerBtn} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

        {/* Session finished */}
        <Text style={styles.finishedTitle}>Your session is finished.</Text>
        <Text style={styles.finishedSubtitle}>How would you rate talkativ?</Text>

        {/* Star rating */}
        <View style={styles.starsRow}>
          {[1, 2, 3, 4, 5].map((star) => (
            <TouchableOpacity key={star} onPress={() => setRating(star)}>
              <Text style={[styles.star, star <= rating && styles.starActive]}>★</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* What did you like */}
        <Text style={styles.sectionLabel}>What did you like about it?</Text>
        <View style={styles.tagWrap}>
          {LIKE_TAGS.map((tag) => (
            <TouchableOpacity
              key={tag}
              style={[styles.tag, selectedLikes.includes(tag) && styles.tagActive]}
              onPress={() => toggleTag(tag, selectedLikes, setSelectedLikes)}
            >
              <Text style={[styles.tagText, selectedLikes.includes(tag) && styles.tagTextActive]}>
                {tag}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* What could be improved */}
        <Text style={styles.sectionLabel}>What could be improved?</Text>
        <View style={styles.tagWrap}>
          {IMPROVE_TAGS.map((tag) => (
            <TouchableOpacity
              key={tag}
              style={[styles.tag, selectedImprove.includes(tag) && styles.tagActive]}
              onPress={() => toggleTag(tag, selectedImprove, setSelectedImprove)}
            >
              <Text style={[styles.tagText, selectedImprove.includes(tag) && styles.tagTextActive]}>
                {tag}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Anything else */}
        <Text style={styles.sectionLabel}>Anything else?</Text>
        <TextInput
          style={styles.textArea}
          placeholder="Tell us everything."
          placeholderTextColor="#C0C0D0"
          value={feedback}
          onChangeText={setFeedback}
          multiline
          numberOfLines={5}
          textAlignVertical="top"
        />

      </ScrollView>

      {/* Submit button */}
      <View style={styles.footer}>
        <TouchableOpacity style={styles.submitBtn} onPress={handleSubmit}>
          <Text style={styles.submitText}>Submit</Text>
          <Text style={styles.submitArrow}>→</Text>
        </TouchableOpacity>
      </View>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe:             { flex: 1, backgroundColor: '#FFFFFF' },

  header:           { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 20, paddingVertical: 14 },
  headerBtn:        { width: 36, alignItems: 'center' },
  backArrow:        { fontSize: 18, color: '#1A1A2E' },
  headerTitle:      { fontSize: 18, fontWeight: '700', color: '#1A1A2E' },

  content:          { paddingHorizontal: 20, paddingBottom: 100 },

  finishedTitle:    { fontSize: 22, fontWeight: '700', color: '#1A1A2E', marginBottom: 6, marginTop: 8 },
  finishedSubtitle: { fontSize: 14, color: '#6C6C80', marginBottom: 20 },

  starsRow:         { flexDirection: 'row', gap: 8, marginBottom: 32 },
  star:             { fontSize: 36, color: '#E0E0E0' },
  starActive:       { color: '#6C3BFF' },

  sectionLabel:     { fontSize: 15, fontWeight: '600', color: '#1A1A2E', marginBottom: 14 },
  tagWrap:          { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 28 },
  tag:              { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20, borderWidth: 1.5, borderColor: '#E2E2EC', backgroundColor: '#FFFFFF' },
  tagActive:        { backgroundColor: '#6C3BFF', borderColor: '#6C3BFF' },
  tagText:          { fontSize: 12, color: '#6C6C80', fontWeight: '500' },
  tagTextActive:    { color: '#FFFFFF', fontWeight: '600' },

  textArea:         { backgroundColor: '#F7F7FB', borderRadius: 16, padding: 16, fontSize: 14, color: '#1A1A2E', minHeight: 120, marginBottom: 20 },

  footer:           { position: 'absolute', bottom: 0, left: 0, right: 0, padding: 20, backgroundColor: '#FFFFFF' },
  submitBtn:        { backgroundColor: '#6C3BFF', borderRadius: 16, paddingVertical: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10 },
  submitText:       { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  submitArrow:      { color: '#FFFFFF', fontSize: 18 },
});
