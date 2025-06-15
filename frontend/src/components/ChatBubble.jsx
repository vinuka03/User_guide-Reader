import React from 'react';
import './ChatBubble.css';

const ChatBubble = ({ content, role }) => {
  const isUser = role === 'user';

  return (
    <div className={`chat-row ${isUser ? 'user-row' : 'bot-row'}`}>
      {!isUser && <div className="chat-avatar bot-avatar"></div>}
      <div className={`chat-bubble ${isUser ? 'user-bubble' : 'bot-bubble'}`}>
        {content}
      </div>
      {isUser && <div className="chat-avatar user-avatar"></div>}
    </div>
  );
};

export default ChatBubble;
