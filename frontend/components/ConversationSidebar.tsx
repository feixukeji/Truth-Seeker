/**
 * Conversation Sidebar Component
 * Displays conversation list, supports creating, switching, and deleting conversations.
 */

'use client';

import { MessageSquarePlus, Trash2, X, Menu } from 'lucide-react';
import type { Conversation } from '@/hooks/useConversationHistory';
import { useLanguage } from '@/hooks/useLanguage';

interface ConversationSidebarProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string) => void;
}

export function ConversationSidebar({
  conversations,
  currentConversationId,
  isOpen,
  onClose,
  onNewConversation,
  onSelectConversation,
  onDeleteConversation,
}: ConversationSidebarProps) {
  const { language, t } = useLanguage();

  /**
   * Format time
   */
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return date.toLocaleTimeString(language === 'zh' ? 'zh-CN' : 'en-US', { hour: '2-digit', minute: '2-digit' });
    } else if (days === 1) {
      return t.sidebar.yesterday;
    } else if (days < 7) {
      return `${days}${t.sidebar.daysAgo}`;
    } else {
      return date.toLocaleDateString(language === 'zh' ? 'zh-CN' : 'en-US', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <>
      {/* Overlay (Mobile) */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-72 bg-white border-r transform transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        } md:translate-x-0 flex flex-col`}
      >
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900">{t.sidebar.title}</h1>
          <button
            onClick={onClose}
            className="p-1 text-gray-500 hover:text-gray-700 md:hidden"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* New Conversation Button */}
        <div className="p-3">
          <button
            onClick={() => {
              onNewConversation();
              onClose();
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-900 text-white rounded-md hover:bg-gray-800 transition-colors"
          >
            <MessageSquarePlus className="w-5 h-5" />
            <span>{t.sidebar.newConversation}</span>
          </button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="p-4 text-center text-gray-500 text-sm">
              {t.sidebar.noHistory}
            </div>
          ) : (
            <ul className="space-y-1 p-2">
              {conversations.map((conv) => (
                <li key={conv.id}>
                  <div
                    role="button"
                    tabIndex={0}
                    onClick={() => {
                      onSelectConversation(conv.id);
                      onClose();
                    }}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onSelectConversation(conv.id);
                        onClose();
                      }
                    }}
                    className={`w-full text-left px-3 py-2 rounded-md transition-colors group flex items-start gap-2 cursor-pointer ${
                      currentConversationId === conv.id
                        ? 'bg-gray-100 text-gray-900 font-medium'
                        : 'hover:bg-gray-50 text-gray-700'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="truncate text-sm font-medium">{conv.title}</div>
                      <div className="text-xs text-gray-400 mt-0.5">
                        {formatTime(conv.updatedAt)} · {conv.messages.length}{t.sidebar.messages}
                      </div>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteConversation(conv.id);
                      }}
                      className="p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                      title={t.sidebar.deleteConversation}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>
    </>
  );
}

/**
 * Mobile Menu Button
 */
export function MobileMenuButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg md:hidden"
    >
      <Menu className="w-6 h-6" />
    </button>
  );
}
