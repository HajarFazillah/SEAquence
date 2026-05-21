import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
  Animated,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';

const { width: SW, height: SH } = Dimensions.get('window');

const LOGO_SIZE = 120;
const CY_LOGO   = SH * 0.38;
const RADIUS    = SW * 0.32;

type TailSide = 'top' | 'bottom' | 'left' | 'right';

const BUBBLES: { text: string; bg: string; color: string; deg: number; delay: number; tail: TailSide }[] = [
  { text: '안녕',   bg: '#EDE7FF', color: '#6C3BFF', deg: -88, delay: 0,    tail: 'bottom' },
  { text: '말해봐', bg: '#FFF0E5', color: '#E07030', deg: -22, delay: 350,  tail: 'left'   },
  { text: '잘했어', bg: '#E5F9EE', color: '#28A55A', deg:  42, delay: 700,  tail: 'left'   },
  { text: '연습',   bg: '#E5F0FF', color: '#2B6BE8', deg: 100, delay: 1050, tail: 'top'    },
  { text: '화이팅', bg: '#FFE5F0', color: '#D42F78', deg: 162, delay: 250,  tail: 'right'  },
  { text: '한국어', bg: '#FFFCE5', color: '#B89010', deg: 222, delay: 600,  tail: 'right'  },
];

function tailStyle(side: TailSide, bg: string) {
  const base = { position: 'absolute' as const, width: 0, height: 0 };
  switch (side) {
    case 'left':
      return { ...base, left: -8, bottom: 9,
        borderTopWidth: 5, borderBottomWidth: 5, borderRightWidth: 9,
        borderTopColor: 'transparent', borderBottomColor: 'transparent', borderRightColor: bg };
    case 'right':
      return { ...base, right: -8, bottom: 9,
        borderTopWidth: 5, borderBottomWidth: 5, borderLeftWidth: 9,
        borderTopColor: 'transparent', borderBottomColor: 'transparent', borderLeftColor: bg };
    case 'top':
      return { ...base, top: -8, left: 16,
        borderLeftWidth: 6, borderRightWidth: 6, borderBottomWidth: 9,
        borderLeftColor: 'transparent', borderRightColor: 'transparent', borderBottomColor: bg };
    case 'bottom':
    default:
      return { ...base, bottom: -8, left: 16,
        borderLeftWidth: 6, borderRightWidth: 6, borderTopWidth: 9,
        borderLeftColor: 'transparent', borderRightColor: 'transparent', borderTopColor: bg };
  }
}

function Bubble({ item }: { item: (typeof BUBBLES)[0] }) {
  const ty = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(ty, { toValue: -8, duration: 1800, useNativeDriver: true }),
        Animated.timing(ty, { toValue: 0,  duration: 1800, useNativeDriver: true }),
      ]),
    );
    const t = setTimeout(() => loop.start(), item.delay);
    return () => { clearTimeout(t); loop.stop(); };
  }, [item.delay, ty]);

  const rad = (item.deg * Math.PI) / 180;
  const cx  = SW / 2 + Math.cos(rad) * RADIUS;
  const cy  = CY_LOGO + Math.sin(rad) * RADIUS;

  return (
    <View style={{ position: 'absolute', left: cx - 52, top: cy - 18, width: 104, alignItems: 'center' }}>
      <Animated.View
        style={[styles.bubble, { backgroundColor: item.bg, transform: [{ translateY: ty }], overflow: 'visible' }]}
      >
        <Text style={[styles.bubbleText, { color: item.color }]}>{item.text}</Text>
        <View style={tailStyle(item.tail, item.bg)} />
      </Animated.View>
    </View>
  );
}

export default function WelcomeScreen() {
  const navigation = useNavigation<any>();

  return (
    <SafeAreaView style={styles.container}>
      {/* Team credit — single line */}
      <Text style={styles.creditText}>
        CSE · Ewha Womans University © SEAquence 2026
      </Text>

      {BUBBLES.map(b => <Bubble key={b.text} item={b} />)}

      {/* Logo */}
      <View style={[styles.logoWrapper, { top: CY_LOGO - LOGO_SIZE / 2 }]}>
        <Image
          source={require('../assets/images/app_logo.png')}
          style={styles.logo}
          resizeMode="contain"
        />
      </View>

      {/* Tagline */}
      <View style={[styles.tagline, { top: CY_LOGO + RADIUS + 36 }]}>
        <Text style={styles.taglineMain}>말이 막혀도 괜찮아.</Text>
        <Text style={styles.taglineSub}>Talkativ와 함께 자신 있게 연습하세요.</Text>
      </View>

      {/* CTA */}
      <View style={styles.footer}>
        <TouchableOpacity
          style={styles.ctaBtn}
          activeOpacity={0.85}
          onPress={() => navigation.navigate('SignUp')}
        >
          <Text style={styles.ctaBtnText}>시작하기</Text>
        </TouchableOpacity>
        <Text style={styles.loginRow}>
          이미 계정이 있으신가요?{' '}
          <Text style={styles.loginLink} onPress={() => navigation.navigate('Login')}>
            로그인하기
          </Text>
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  creditText: {
    alignSelf: 'center',
    marginTop: 12,
    fontSize: 11,
    fontWeight: '400',
    color: '#B0B0C5',
    letterSpacing: 0.2,
  },
  logoWrapper: {
    position: 'absolute',
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  logo: {
    width: LOGO_SIZE,
    height: LOGO_SIZE,
  },
  bubble: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.07,
    shadowRadius: 6,
    elevation: 2,
  },
  bubbleText: {
    fontSize: 14,
    fontWeight: '600',
  },
  tagline: {
    position: 'absolute',
    left: 32,
    right: 32,
    alignItems: 'center',
  },
  taglineMain: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1A1A2E',
    textAlign: 'center',
    marginBottom: 10,
  },
  taglineSub: {
    fontSize: 15,
    color: '#6C6C80',
    textAlign: 'center',
    lineHeight: 22,
  },
  footer: {
    position: 'absolute',
    bottom: 36,
    left: 24,
    right: 24,
    alignItems: 'center',
    gap: 16,
  },
  ctaBtn: {
    width: '100%',
    height: 54,
    backgroundColor: '#6C3BFF',
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  ctaBtnText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.3,
  },
  loginRow: {
    fontSize: 14,
    color: '#6C6C80',
  },
  loginLink: {
    color: '#6C3BFF',
    fontWeight: '600',
  },
});
