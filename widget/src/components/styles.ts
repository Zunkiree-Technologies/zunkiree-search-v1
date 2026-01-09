export const styles = (primaryColor: string) => `
  /* Widget Container */
  .zk-widget {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    pointer-events: none;
  }

  .zk-widget > * {
    pointer-events: auto;
  }

  /* Unified Chat Panel - Expands/Collapses Smoothly */
  .zk-chat-panel {
    width: 100%;
    max-width: 600px;
    margin: 0 16px;
    background: #ebebeb;
    border-radius: 16px 16px 0 0;
    border: 0.5px solid #d4d4d4;
    border-bottom: none;
    box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.06);
    position: relative;
    z-index: 1;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Collapsed State */
  .zk-chat-collapsed {
    padding-bottom: 20px;
  }

  .zk-chat-collapsed .zk-messages-wrapper {
    max-height: 0;
    opacity: 0;
    overflow: hidden;
  }

  /* Expanded State */
  .zk-chat-expanded {
    padding-bottom: 20px;
  }

  .zk-chat-expanded .zk-messages-wrapper {
    max-height: 350px;
    opacity: 1;
  }

  /* Chat Header */
  .zk-chat-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    cursor: pointer;
    transition: background 0.15s;
  }

  .zk-chat-header:hover {
    background: #e0e0e0;
  }

  .zk-panel-title {
    flex: 1;
    font-weight: 600;
    font-size: 14px;
    color: #374151;
  }

  .zk-toggle-btn {
    background: none;
    border: none;
    color: #6b7280;
    cursor: pointer;
    padding: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    transition: background 0.15s, color 0.15s;
  }

  .zk-toggle-btn:hover {
    background: rgba(0, 0, 0, 0.05);
    color: #374151;
  }

  /* Messages Wrapper - Animates height */
  .zk-messages-wrapper {
    overflow: hidden;
    transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease;
  }

  .zk-messages {
    overflow-y: auto;
    padding: 8px 16px 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    max-height: 320px;
  }

  .zk-message {
    max-width: 85%;
    animation: zk-fade-in 0.2s ease;
  }

  @keyframes zk-fade-in {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .zk-message-user {
    align-self: flex-end;
  }

  .zk-message-assistant {
    align-self: flex-start;
  }

  .zk-message-content {
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.5;
  }

  .zk-message-user .zk-message-content {
    background: ${primaryColor};
    color: white;
    border-bottom-right-radius: 4px;
  }

  .zk-message-assistant .zk-message-content {
    background: #f3f4f6;
    color: #1f2937;
    border-bottom-left-radius: 4px;
  }

  .zk-typing {
    display: flex;
    gap: 4px;
    padding: 12px 14px;
  }

  .zk-typing span {
    width: 8px;
    height: 8px;
    background: #9ca3af;
    border-radius: 50%;
    animation: zk-bounce 1.4s infinite ease-in-out both;
  }

  .zk-typing span:nth-child(1) { animation-delay: -0.32s; }
  .zk-typing span:nth-child(2) { animation-delay: -0.16s; }

  @keyframes zk-bounce {
    0%, 80%, 100% { transform: scale(0); }
    40% { transform: scale(1); }
  }

  .zk-suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
  }

  .zk-suggestion {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 6px 12px;
    font-size: 12px;
    color: #4b5563;
    cursor: pointer;
    transition: all 0.15s;
  }

  .zk-suggestion:hover {
    background: #f9fafb;
    border-color: ${primaryColor};
    color: ${primaryColor};
  }

  /* Animated border custom property */
  @property --border-angle {
    syntax: '<angle>';
    initial-value: 0deg;
    inherits: false;
  }

  /* Bottom Input Bar */
  .zk-input-bar {
    width: 100%;
    max-width: 600px;
    padding: 12px 0 16px 0;
    background: transparent;
    margin: 0 16px;
  }

  /* Input Container with Animated Border */
  .zk-input-container {
    position: relative;
    background: #e5e7eb;
    border-radius: 24px;
    padding: 1.5px;
    isolation: isolate;
  }

  /* Subtle base border */
  .zk-input-container::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 24px;
    padding: 1.5px;
    background: conic-gradient(
      from var(--border-angle),
      transparent 0%,
      transparent 6%,
      #3b82f6 8%,
      #06b6d4 10%,
      #84cc16 12%,
      #eab308 14%,
      transparent 16%,
      transparent 100%
    );
    -webkit-mask:
      linear-gradient(#fff 0 0) content-box,
      linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask:
      linear-gradient(#fff 0 0) content-box,
      linear-gradient(#fff 0 0);
    mask-composite: exclude;
    animation: rotate-border 4s linear infinite;
  }

  /* Glow effect - follows the spark */
  .zk-input-container::after {
    content: '';
    position: absolute;
    inset: -2px;
    border-radius: 26px;
    background: conic-gradient(
      from var(--border-angle),
      transparent 0%,
      transparent 6%,
      #3b82f6 8%,
      #06b6d4 10%,
      #84cc16 12%,
      #eab308 14%,
      transparent 16%,
      transparent 100%
    );
    filter: blur(6px);
    opacity: 0.5;
    z-index: -1;
    animation: rotate-border 4s linear infinite;
  }

  @keyframes rotate-border {
    0% {
      --border-angle: 0deg;
    }
    100% {
      --border-angle: 360deg;
    }
  }

  .zk-input-inner {
    position: relative;
    background: white;
    border-radius: 22px;
    padding: 12px 16px;
    min-height: 48px;
    display: flex;
    align-items: flex-end;
  }

  .zk-input {
    flex: 1;
    border: none;
    font-size: 15px;
    outline: none;
    background: transparent;
    resize: none;
    line-height: 24px;
    color: #1f2937;
    min-height: 24px;
    max-height: 216px;
    overflow-y: auto;
    font-family: inherit;
    padding: 0;
    padding-right: 8px;
    margin: 0;
    margin-right: 48px;
  }

  /* Custom scrollbar styling */
  .zk-input::-webkit-scrollbar {
    width: 6px;
  }

  .zk-input::-webkit-scrollbar-track {
    background: transparent;
    margin: 4px 0;
  }

  .zk-input::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;
  }

  .zk-input::-webkit-scrollbar-thumb:hover {
    background: #9ca3af;
  }

  /* Firefox scrollbar */
  .zk-input {
    scrollbar-width: thin;
    scrollbar-color: #d1d5db transparent;
  }

  .zk-input::placeholder {
    color: #9ca3af;
  }

  .zk-input:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .zk-send {
    position: absolute;
    bottom: 8px;
    right: 12px;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #f3f4f6;
    color: #374151;
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s, transform 0.15s, color 0.15s;
    flex-shrink: 0;
  }

  .zk-send:hover:not(:disabled) {
    background: #e5e7eb;
    transform: scale(1.05);
  }

  .zk-send:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .zk-powered-by {
    text-align: center;
    font-size: 11px;
    color: #9ca3af;
    margin-top: 8px;
  }

  .zk-powered-by a {
    color: ${primaryColor};
    text-decoration: none;
  }

  .zk-powered-by a:hover {
    text-decoration: underline;
  }

  /* When chat panel is shown, input overlaps it */
  .zk-chat-panel + .zk-input-bar {
    margin-top: -20px;
    padding-top: 0;
    position: relative;
    z-index: 2;
  }

  .zk-preview-icon {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: ${primaryColor}20;
    color: ${primaryColor};
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .zk-preview-text {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #374151;
    font-size: 14px;
    line-height: 1.4;
  }

  /* Mobile Responsive */
  @media (max-width: 640px) {
    .zk-chat-panel {
      margin: 0 12px;
      border-radius: 16px 16px 0 0;
      max-width: calc(100% - 24px);
    }

    .zk-chat-expanded .zk-messages-wrapper {
      max-height: 50vh;
    }

    .zk-input-bar {
      margin: 0 12px;
      padding: 12px 0 16px 0;
      max-width: calc(100% - 24px);
    }

    .zk-chat-panel + .zk-input-bar {
      margin-top: -20px;
    }

    .zk-messages {
      max-height: calc(50vh - 60px);
    }
  }
`
