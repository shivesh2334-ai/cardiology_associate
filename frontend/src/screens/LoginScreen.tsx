/**
 * AC Agent — Login Screen
 */

import React, { useState } from 'react';
import {
  View, Text, TextInput, StyleSheet, KeyboardAvoidingView,
  Platform, Alert, TouchableOpacity, ScrollView
} from 'react-native';
import { Colors, Typography, Spacing, Radius } from '../utils/design';
import { Button } from '../components/ui';
import { useAuth } from '../context/AuthContext';

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading]   = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Required', 'Please enter your email and password');
      return;
    }
    setLoading(true);
    try {
      await login(email.trim().toLowerCase(), password);
    } catch (err: any) {
      Alert.alert('Login Failed', err.message ?? 'Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">

        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logoContainer}>
            <Text style={styles.logoIcon}>🏥</Text>
          </View>
          <Text style={styles.appName}>AC Agent</Text>
          <Text style={styles.tagline}>Associate Consultant AI</Text>
          <Text style={styles.powered}>Powered by EasyMyCare</Text>
        </View>

        {/* Form */}
        <View style={styles.form}>
          <Text style={styles.formTitle}>Sign In</Text>

          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Email / Username</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              placeholder="doctor@hospital.in"
              placeholderTextColor={Colors.textMuted}
            />
          </View>

          <View style={styles.fieldGroup}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              secureTextEntry
              placeholder="••••••••"
              placeholderTextColor={Colors.textMuted}
            />
          </View>

          <Button
            label={loading ? 'Signing in...' : 'Sign In'}
            onPress={handleLogin}
            loading={loading}
            style={styles.loginBtn}
          />

          <Text style={styles.disclaimer}>
            This application is for use by authorised clinical staff only.
            All actions are logged and audited for medico-legal compliance.
          </Text>
        </View>

        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            EMC Digitals — Healthcare AI Platform {'\n'}
            Data stored in India (AWS Mumbai) | DPDPA Compliant
          </Text>
        </View>

      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.brandDark },
  scroll: { flexGrow: 1 },
  header: {
    alignItems: 'center',
    paddingTop: 80,
    paddingBottom: 40,
    paddingHorizontal: Spacing.xxl,
  },
  logoContainer: {
    width: 80, height: 80, borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.15)',
    alignItems: 'center', justifyContent: 'center',
    marginBottom: Spacing.base,
  },
  logoIcon:    { fontSize: 40 },
  appName:     { fontSize: Typography.xxxl, fontWeight: '800', color: Colors.white, letterSpacing: 1 },
  tagline:     { fontSize: Typography.md, color: 'rgba(255,255,255,0.8)', marginTop: 4 },
  powered:     { fontSize: Typography.sm, color: 'rgba(255,255,255,0.5)', marginTop: 6 },
  form: {
    backgroundColor: Colors.white,
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: Spacing.xxl,
    flex: 1,
    minHeight: 400,
  },
  formTitle: {
    fontSize: Typography.xxl,
    fontWeight: Typography.bold,
    color: Colors.brandDark,
    marginBottom: Spacing.xl,
  },
  fieldGroup:  { marginBottom: Spacing.base },
  label:       { fontSize: Typography.sm, fontWeight: '600', color: Colors.textSecondary, marginBottom: 6 },
  input: {
    backgroundColor: Colors.background,
    borderWidth: 1, borderColor: Colors.border,
    borderRadius: Radius.md,
    padding: Spacing.md,
    fontSize: Typography.base,
    color: Colors.textPrimary,
    minHeight: 52,
  },
  loginBtn:    { marginTop: Spacing.base },
  disclaimer: {
    fontSize: Typography.xs,
    color: Colors.textMuted,
    textAlign: 'center',
    marginTop: Spacing.base,
    lineHeight: 18,
  },
  footer: {
    backgroundColor: Colors.white,
    padding: Spacing.xl,
    alignItems: 'center',
  },
  footerText: {
    fontSize: Typography.xs,
    color: Colors.textMuted,
    textAlign: 'center',
    lineHeight: 18,
  },
});
