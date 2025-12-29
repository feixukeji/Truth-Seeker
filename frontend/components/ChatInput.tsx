/**
 * Chat Input Component
 * Supports text input and file uploads.
 */

'use client';

import { useState, useRef, useCallback } from 'react';
import { Send, Paperclip, X, Loader2 } from 'lucide-react';
import { useLanguage } from '@/hooks/useLanguage';

interface FilePreview {
  file: File;
  preview?: string;
}

interface ChatInputProps {
  onSubmit: (message: string, files: File[]) => void;
  disabled?: boolean;
  placeholder?: string;
}

const ALLOWED_TYPES = [
  // Image types
  'image/jpeg',
  'image/png',
  'image/webp',
  'image/heic',
  'image/heif',
  // Document types
  'application/pdf',
  'text/plain',           // TXT
  'text/markdown',        // Markdown
  'text/x-markdown',      // Markdown (fallback)
  'text/html',            // HTML
  'text/xml',             // XML
  'application/xml',      // XML (fallback)
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export function ChatInput({ onSubmit, disabled, placeholder }: ChatInputProps) {
  const { t } = useLanguage();
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState<FilePreview[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /**
   * Check if two files are the same
   */
  const isSameFile = (a: File, b: File) => {
    return a.name === b.name && a.size === b.size && a.lastModified === b.lastModified;
  };

  /**
   * Handle file selection
   */
  const handleFileSelect = useCallback((selectedFiles: FileList | null) => {
    if (!selectedFiles) return;

    const newFiles: FilePreview[] = [];
    const duplicateNames: string[] = [];

    for (const file of Array.from(selectedFiles)) {
      // Check file type
      if (!ALLOWED_TYPES.includes(file.type)) {
        alert(`${t.files.unsupportedType}: ${file.type}\n${t.files.supportedTypes}`);
        continue;
      }

      // Check file size
      if (file.size > MAX_FILE_SIZE) {
        alert(`${t.files.tooLarge}: ${file.name}\n${t.files.maxSize}`);
        continue;
      }

      // Check for duplicates in existing files
      const isDuplicate = files.some((f) => isSameFile(f.file, file));
      if (isDuplicate) {
        duplicateNames.push(file.name);
        continue;
      }

      // Check for duplicates in current batch
      const isDuplicateInBatch = newFiles.some((f) => isSameFile(f.file, file));
      if (isDuplicateInBatch) {
        duplicateNames.push(file.name);
        continue;
      }

      // Create preview
      const preview = file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined;
      newFiles.push({ file, preview });
    }

    // Alert duplicate files
    if (duplicateNames.length > 0) {
      alert(`${t.files.duplicateFiles}:\n${duplicateNames.join('\n')}`);
    }

    if (newFiles.length > 0) {
      setFiles((prev) => [...prev, ...newFiles]);
    }
  }, [files]);

  /**
   * Remove file
   */
  const removeFile = useCallback((index: number) => {
    setFiles((prev) => {
      const file = prev[index];
      if (file.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter((_, i) => i !== index);
    });
  }, []);

  /**
   * Handle submission
   */
  const handleSubmit = useCallback(() => {
    if (disabled) return;

    const trimmedMessage = message.trim();
    if (!trimmedMessage && files.length === 0) return;

    onSubmit(trimmedMessage, files.map((f) => f.file));

    // Clear input
    setMessage('');
    files.forEach((f) => {
      if (f.preview) URL.revokeObjectURL(f.preview);
    });
    setFiles([]);

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }, [message, files, disabled, onSubmit]);

  /**
   * Handle keyboard events
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  /**
   * Auto-adjust textarea height
   */
  const handleInput = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  };

  return (
    <div className="border-t bg-white p-4">
      {/* File Previews */}
      {files.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {files.map((file, index) => (
            <div key={index} className="relative group">
              {file.preview ? (
                <img
                  src={file.preview}
                  alt={file.file.name}
                  className="w-16 h-16 object-cover rounded-lg border"
                />
              ) : (
                <div className="w-16 h-16 flex items-center justify-center bg-gray-100 rounded-lg border">
                  <span className="text-xs text-gray-500 text-center px-1 truncate">
                    {file.file.name.split('.').pop()?.toUpperCase()}
                  </span>
                </div>
              )}
              <button
                onClick={() => removeFile(index)}
                className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                type="button"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className="flex items-center gap-2">
        {/* Attachment Button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          type="button"
          title={t.files.uploadFiles}
        >
          <Paperclip className="w-5 h-5" />
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept={ALLOWED_TYPES.join(',')}
          multiple
          onChange={(e) => {
            handleFileSelect(e.target.files);
            // Reset value to allow selecting the same file again
            e.target.value = '';
          }}
          className="hidden"
        />

        {/* Text Input */}
        <div className="flex-1 relative flex items-center">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full resize-none border border-slate-300 rounded-md px-4 py-2 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed min-h-[40px]"
            style={{ maxHeight: '200px' }}
          />
        </div>

        {/* Send Button */}
        <button
          onClick={handleSubmit}
          disabled={disabled || (!message.trim() && files.length === 0)}
          className="flex-shrink-0 w-10 h-10 flex items-center justify-center bg-gray-900 text-white rounded-md hover:bg-gray-800 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          type="button"
        >
          {disabled ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  );
}
