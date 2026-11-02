import React, { useState, useRef, useEffect } from 'react';
import { View, Text, StyleSheet, SafeAreaView, TextInput, TouchableOpacity, ScrollView, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { api } from '@/services/api';
import { Colors } from '@/constants';
import Markdown from 'react-native-markdown-display';
import { HealthVaultAILogo } from '@/components/AILogo';

export default function AIAssistantScreen() {
  const [messages, setMessages] = useState<{ role: 'user' | 'ai', text: string }[]>([
    { role: 'ai', text: 'Hello! I am your HealthVault AI Assistant. I have secure access to your medical records, lab reports, and timeline. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);

  useEffect(() => {
    api.post('/api/v1/ai/clear-history').catch(() => { });
  }, []);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;
    const userMsg = text.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const response = await api.post('/api/v1/ai/chat', { message: userMsg });
      if (response.data?.response) {
        setMessages(prev => [...prev, { role: 'ai', text: response.data.response }]);
      } else if (response.data?.error) {
        setMessages(prev => [...prev, { role: 'ai', text: `Error: ${response.data.error}` }]);
      }
    } catch (error: any) {
      setMessages(prev => [...prev, { role: 'ai', text: `Sorry, I encountered an error: ${error.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  const suggest = (text: string) => {
    sendMessage(text);
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.aiIconContainer}>
          <HealthVaultAILogo width={24} height={24} />
        </View>
        <View>
          <Text style={styles.headerTitle}>HealthVault AI</Text>
          <Text style={styles.headerSubtitle}>Personal Health Assistant</Text>
        </View>
      </View>

      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined} keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}>
        <ScrollView
          ref={scrollViewRef}
          style={styles.chatArea}
          contentContainerStyle={styles.chatContent}
          onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
        >
          {messages.map((msg, idx) => (
            <View key={idx} style={[styles.messageRow, msg.role === 'user' ? styles.userRow : styles.aiRow]}>
              {msg.role === 'ai' && (
                <View style={styles.aiAvatar}>
                  <HealthVaultAILogo width={20} height={20} />
                </View>
              )}
              <View style={[styles.messageBubble, msg.role === 'user' ? styles.userBubble : styles.aiBubble]}>
                {msg.role === 'ai' ? (
                  <Markdown style={markdownStyles}>{msg.text}</Markdown>
                ) : (
                  <Text style={styles.userText}>{msg.text}</Text>
                )}
              </View>
            </View>
          ))}
          {loading && (
            <View style={[styles.messageRow, styles.aiRow]}>
              <View style={styles.aiAvatar}>
                <HealthVaultAILogo width={20} height={20} />
              </View>
              <View style={[styles.messageBubble, styles.aiBubble, { width: 60, alignItems: 'center' }]}>
                <ActivityIndicator color={Colors.primary} size="small" />
              </View>
            </View>
          )}
        </ScrollView>

        {/* Suggestions */}
        {messages.length === 1 && (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.suggestionsContainer} contentContainerStyle={styles.suggestionsContent}>
            <TouchableOpacity style={styles.suggestionChip} onPress={() => suggest("Summarize my latest lab report")}>
              <Text style={styles.suggestionText}>Summarize my latest lab report</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.suggestionChip} onPress={() => suggest("What are my active medications?")}>
              <Text style={styles.suggestionText}>What are my active medications?</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.suggestionChip} onPress={() => suggest("Do I have any allergies recorded?")}>
              <Text style={styles.suggestionText}>Do I have any allergies recorded?</Text>
            </TouchableOpacity>
          </ScrollView>
        )}

        {/* Input Area */}
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="Ask about your health..."
            placeholderTextColor={Colors.textMuted}
            value={input}
            onChangeText={setInput}
            multiline
            maxLength={500}
          />
          <TouchableOpacity
            style={[styles.sendBtn, !input.trim() && { opacity: 0.5 }]}
            onPress={() => sendMessage(input)}
            disabled={!input.trim() || loading}
          >
            <Ionicons name="send" size={18} color="#fff" />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: { flexDirection: 'row', alignItems: 'center', padding: 16, backgroundColor: Colors.surface, borderBottomWidth: 1, borderBottomColor: Colors.border },
  aiIconContainer: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center', marginRight: 12 },
  headerTitle: { fontSize: 16, fontWeight: '700', color: Colors.primary },
  headerSubtitle: { fontSize: 12, color: Colors.teal },
  chatArea: { flex: 1 },
  chatContent: { padding: 16, paddingBottom: 24, gap: 16 },
  messageRow: { flexDirection: 'row', alignItems: 'flex-end', marginBottom: 4 },
  userRow: { justifyContent: 'flex-end' },
  aiRow: { justifyContent: 'flex-start' },
  aiAvatar: { width: 28, height: 28, alignItems: 'center', justifyContent: 'center', marginRight: 8, marginBottom: 2 },
  messageBubble: { maxWidth: '82%', padding: 14, borderRadius: 20 },
  userBubble: { backgroundColor: Colors.primary, borderBottomRightRadius: 4 },
  aiBubble: { backgroundColor: Colors.surface, borderBottomLeftRadius: 4, borderWidth: 1, borderColor: Colors.border, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 4, elevation: 1 },
  userText: { color: '#fff', fontSize: 15, lineHeight: 22 },
  suggestionsContainer: { flexGrow: 0, paddingVertical: 12, borderTopWidth: 1, borderTopColor: Colors.border, backgroundColor: Colors.background },
  suggestionsContent: { paddingHorizontal: 16, gap: 10 },
  suggestionChip: { backgroundColor: Colors.surfaceVariant, paddingHorizontal: 16, paddingVertical: 10, borderRadius: 20, borderWidth: 1, borderColor: Colors.border },
  suggestionText: { color: Colors.primary, fontSize: 13, fontWeight: '600' },
  inputContainer: { flexDirection: 'row', alignItems: 'flex-end', padding: 12, paddingBottom: Platform.OS === 'ios' ? 24 : 12, backgroundColor: Colors.surface, borderTopWidth: 1, borderTopColor: Colors.border },
  input: { flex: 1, backgroundColor: Colors.background, borderRadius: 20, paddingHorizontal: 16, paddingTop: 12, paddingBottom: 12, fontSize: 15, color: Colors.text, maxHeight: 100, minHeight: 44 },
  sendBtn: { width: 44, height: 44, borderRadius: 22, backgroundColor: Colors.primary, alignItems: 'center', justifyContent: 'center', marginLeft: 10 },
});

const markdownStyles = {
  body: { fontSize: 15, lineHeight: 22, color: Colors.text },
  strong: { fontWeight: '700', color: Colors.primary },
  em: { fontStyle: 'italic' },
  heading1: { fontSize: 18, fontWeight: '700', color: Colors.primary, marginVertical: 8 },
  heading2: { fontSize: 16, fontWeight: '700', color: Colors.primary, marginVertical: 8 },
  paragraph: { marginVertical: 4 },
  bullet_list: { marginVertical: 4 },
  list_item: { marginVertical: 2 },
};
