/**
 * Truth Seeker - Main Page
 * AI Claim Verifier Assistant
 */

'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { ChatMessage, LoadingMessage } from '@/components/ChatMessage';
import { ChatInput } from '@/components/ChatInput';
import { ConversationSidebar, MobileMenuButton } from '@/components/ConversationSidebar';
import { LanguageSwitch } from '@/components/LanguageSwitch';
import { useConversationHistory } from '@/hooks/useConversationHistory';
import { useLanguage } from '@/hooks/useLanguage';
import { submitChat, pollTaskResult, fileToBase64, type FileData } from '@/lib/api';
import { AlertCircle, RefreshCw, Github } from 'lucide-react';

export default function HomePage() {
  const { language, t } = useLanguage();
  const {
    conversations,
    currentConversation,
    currentConversationId,
    isLoaded,
    createConversation,
    addMessage,
    deleteConversation,
    switchConversation,
  } = useConversationHistory();

  const [isLoading, setIsLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState<string>('');
  const [loadingPosition, setLoadingPosition] = useState<number | undefined>();
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  /**
   * Scroll to bottom
   */
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Scroll to bottom when messages change or loading state changes
  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages, isLoading, scrollToBottom]);

  /**
   * Handle message submission
   */
  const handleSubmit = async (message: string, files: File[]) => {
    if (!message.trim() && files.length === 0) {
      return;
    }

    setError(null);
    setIsLoading(true);
    setLoadingStatus('pending');
    setLoadingPosition(undefined);

    try {
      // Ensure there is a current conversation
      let convId = currentConversationId;
      if (!convId) {
        // Use message or first filename as title
        const title = message || (files.length > 0 ? files[0].name : t.sidebar.newConversation);
        convId = createConversation(title);
      }

      // Prepare file info
      const fileInfos = files.map(f => ({
        filename: f.name,
        mime_type: f.type,
      }));

      // Add user message
      addMessage(convId, 'user', message, fileInfos.length > 0 ? fileInfos : undefined);

      // Convert files to base64
      let fileData: FileData[] | undefined;
      if (files.length > 0) {
        fileData = await Promise.all(files.map(fileToBase64));
      }

      // Get conversation history (excluding the newly added user message)
      const historyMessages = currentConversation?.messages.map(msg => ({
        role: msg.role === 'assistant' ? 'model' as const : 'user' as const,
        content: msg.content,
      })) || [];

      // Submit request
      const taskResponse = await submitChat(message, historyMessages, fileData, language);

      // Poll for result
      const result = await pollTaskResult(
        taskResponse.task_id,
        (status, position) => {
          setLoadingStatus(status);
          setLoadingPosition(position);
        }
      );

      if (result.status === 'completed') {
        if (result.result) {
          // Add assistant response
          addMessage(convId, 'assistant', result.result);
        } else {
          // Task completed but no response content
          setError(t.errors.emptyResponse);
        }
      } else if (result.status === 'failed') {
        setError(result.error || t.errors.processingFailed);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : t.errors.networkError);
    } finally {
      setIsLoading(false);
      setLoadingStatus('');
      setLoadingPosition(undefined);
    }
  };

  /**
   * Handle new conversation
   */
  const handleNewConversation = () => {
    switchConversation(null);
  };

  // Wait for loading
  if (!isLoaded) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-gray-600 animate-spin mx-auto mb-2" />
          <p className="text-gray-600">{t.loading}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <ConversationSidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewConversation={handleNewConversation}
        onSelectConversation={switchConversation}
        onDeleteConversation={deleteConversation}
      />

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="flex-shrink-0 h-14 bg-white border-b flex items-center px-4 gap-3">
          <MobileMenuButton onClick={() => setSidebarOpen(true)} />
          <h2 className="font-medium text-gray-900 truncate flex-1">
            {currentConversation?.title || t.appName}
          </h2>
          <a
            href="https://github.com/feixukeji/truth-seeker"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-2 py-1.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            title="GitHub Repository"
          >
            <Github className="w-4 h-4" />
            <span className="hidden sm:inline">GitHub</span>
          </a>
          <LanguageSwitch />
        </header>

        {/* Message Area */}
        <div className="flex-1 overflow-y-auto">
          {!currentConversation || currentConversation.messages.length === 0 ? (
            /* Welcome Screen */
            <div className="h-full flex items-center justify-center p-6">
              <div className="max-w-md text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-md flex items-center justify-center mx-auto mb-4 border border-gray-200">
                  <span className="text-3xl">🔍</span>
                </div>
                <h2 className="text-xl font-bold text-gray-900 mb-2">
                  {t.welcome.title}
                </h2>
                <p className="text-gray-600 mb-6">
                  {t.welcome.subtitle}
                </p>
                <div className="space-y-2 text-left">
                  <p className="text-sm text-gray-500">{t.welcome.tryExamples}</p>
                  <div className="space-y-2">
                    {t.welcome.examples.map((example, index) => (
                      <button
                        key={index}
                        onClick={() => handleSubmit(example, [])}
                        disabled={isLoading}
                        className="block w-full text-left px-4 py-2 bg-white rounded-md border border-slate-300 hover:bg-gray-50 text-sm text-gray-700 disabled:opacity-50"
                      >
                        {example}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Message List */
            <div>
              {currentConversation.messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  role={msg.role === 'assistant' ? 'assistant' : 'user'}
                  content={msg.content}
                  files={msg.files}
                />
              ))}
              
              {/* Loading State */}
              {isLoading && (
                <LoadingMessage status={loadingStatus} position={loadingPosition} />
              )}
              
              {/* Scroll Anchor */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex-shrink-0 px-4 py-2 bg-red-50 border-t border-red-200">
            <div className="flex items-center gap-2 text-red-700 text-sm">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-500 hover:text-red-700"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* Input Area */}
        <ChatInput
          onSubmit={handleSubmit}
          disabled={isLoading}
          placeholder={
            currentConversation?.messages.length
              ? t.chat.followUpPlaceholder
              : t.chat.placeholder
          }
        />

        {/* Disclaimer */}
        <div className="flex-shrink-0 px-4 py-2 bg-white border-t">
          <p className="text-xs text-gray-400 text-center">
            {t.chat.disclaimer}
          </p>
        </div>
      </main>
    </div>
  );
}
