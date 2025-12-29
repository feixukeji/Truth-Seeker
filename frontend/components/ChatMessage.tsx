/**
 * Chat Message Component
 * Supports Markdown rendering.
 */

'use client';

import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Bot, FileText, Image as ImageIcon, Search, BookOpen, Brain, Sparkles, FileSearch, Lightbulb, Target } from 'lucide-react';
import { useLanguage } from '@/hooks/useLanguage';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  files?: Array<{
    filename: string;
    mime_type: string;
  }>;
  isLoading?: boolean;
}

export function ChatMessage({ role, content, files, isLoading }: ChatMessageProps) {
  const { t } = useLanguage();
  const isUser = role === 'user';

  return (
    <div className={`flex gap-3 p-4 ${isUser ? 'bg-white' : 'bg-gray-50'}`}>
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center ${
        isUser ? 'bg-gray-800' : 'bg-gray-600'
      }`}>
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className="flex-1 min-w-0">
        {/* Role Label */}
        <div className="text-xs text-gray-500 mb-1">
          {isUser ? t.chat.you : t.chat.assistant}
        </div>

        {/* Attachments */}
        {files && files.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2">
            {files.map((file, index) => (
              <div
                key={index}
                className="inline-flex items-center gap-1.5 px-2 py-1 bg-gray-100 rounded text-sm text-gray-600"
              >
                {file.mime_type.startsWith('image/') ? (
                  <ImageIcon className="w-4 h-4" />
                ) : (
                  <FileText className="w-4 h-4" />
                )}
                <span className="truncate max-w-[150px]">{file.filename}</span>
              </div>
            ))}
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        ) : (
          /* Markdown Content */
          <div className="markdown-content">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                // Custom link to open in new tab
                a: ({ href, children }) => (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-700 hover:text-gray-900 underline"
                  >
                    {children}
                  </a>
                ),
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Thinking phase icon configuration
 */
const THINKING_ICONS = [
  { icon: Target, color: 'text-orange-500' },
  { icon: Search, color: 'text-blue-500' },
  { icon: BookOpen, color: 'text-emerald-500' },
  { icon: FileSearch, color: 'text-violet-500' },
  { icon: Brain, color: 'text-amber-500' },
  { icon: Lightbulb, color: 'text-rose-500' },
  { icon: Sparkles, color: 'text-cyan-500' },
];

/**
 * Loading message component with rich thinking animations
 */
export function LoadingMessage({ status, position }: { status: string; position?: number }) {
  const { t } = useLanguage();
  const [currentStep, setCurrentStep] = useState(0);
  const [dots, setDots] = useState('');
  const stepRef = useRef(0);
  const isRunningRef = useRef(false);

  // Thinking step text (i18n)
  const thinkingSteps = [
    t.thinking.analyzing,
    t.thinking.searchingDatabase,
    t.thinking.readingLiterature,
    t.thinking.analyzingLiterature,
    t.thinking.synthesizingEvidence,
    t.thinking.formingConclusion,
    t.thinking.organizingResults,
  ];

  // Switch thinking steps
  useEffect(() => {
    if (status !== 'processing') {
      // Reset state
      stepRef.current = 0;
      isRunningRef.current = false;
      setCurrentStep(0);
      return;
    }
    
    // Prevent duplicate start (React Strict Mode double-invokes)
    if (isRunningRef.current) return;
    isRunningRef.current = true;
    
    let timeoutId: NodeJS.Timeout;
    let isCancelled = false;
    
    const scheduleNextStep = () => {
      if (isCancelled) return;
      
      // Stop scheduling if at last step
      if (stepRef.current >= THINKING_ICONS.length - 1) return;
      
      // Random interval 4~8 seconds
      const randomDelay = 4000 + Math.random() * 4000;
      
      timeoutId = setTimeout(() => {
        if (isCancelled) return;
        
        stepRef.current += 1;
        setCurrentStep(stepRef.current);
        
        // Schedule next step
        scheduleNextStep();
      }, randomDelay);
    };
    
    scheduleNextStep();

    return () => {
      isCancelled = true;
      isRunningRef.current = false;
      clearTimeout(timeoutId);
    };
  }, [status]);

  // Dynamic ellipsis animation
  useEffect(() => {
    const dotsInterval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? '' : prev + '.'));
    }, 500);

    return () => clearInterval(dotsInterval);
  }, []);

  const CurrentIcon = THINKING_ICONS[currentStep].icon;

  return (
    <div className="flex gap-3 p-4 bg-gradient-to-r from-gray-50 to-slate-50">
      {/* Animated avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center bg-gradient-to-br from-gray-600 to-gray-700 thinking-avatar">
        <Bot className="w-5 h-5 text-white" />
      </div>

      <div className="flex-1">
        <div className="text-xs text-gray-500 mb-2">{t.chat.assistant}</div>
        
        {/* Queue status */}
        {status === 'pending' && position ? (
          <div className="flex items-center gap-3">
            <div className="queue-indicator">
              <div className="queue-circle"></div>
              <div className="queue-circle"></div>
              <div className="queue-circle"></div>
            </div>
            <span className="text-sm text-gray-600">
              {t.thinking.queuing}（{t.thinking.position.replace('{position}', String(position))}）{dots}
            </span>
          </div>
        ) : (
          /* Processing status (including default) */
          <div className="space-y-3">
            {/* Main status indicator */}
            <div className="flex items-center gap-3">
              <div className={`thinking-icon ${THINKING_ICONS[currentStep].color}`}>
                <CurrentIcon className="w-5 h-5" />
              </div>
              <span className="text-sm text-gray-700 font-medium thinking-text">
                {thinkingSteps[currentStep]}
              </span>
            </div>

            {/* Progress bar animation */}
            <div className="thinking-progress-container">
              <div className="thinking-progress-bar"></div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
