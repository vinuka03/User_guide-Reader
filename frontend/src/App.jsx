import React, { useState, useRef, useEffect } from 'react';
import UploadBox from './components/UploadBox';
import ChatBubble from './components/ChatBubble';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Hello! Welcome to ProductPal.' }
  ]);
  const [question, setQuestion] = useState('');
  const [pdfFile, setPdfFile] = useState(null);
  const [loadingState, setLoadingState] = useState('idle'); // 'idle' | 'thinking' | 'web'
  const chatEndRef = useRef(null);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSend = async () => {
    if (!question.trim()) return;

    if (!pdfFile) {
      setMessages(prev => [
        ...prev,
        { role: 'user', content: question },
        { role: 'bot', content: '📄 Please upload a product manual before asking questions.' }
      ]);
      setQuestion('');
      return;
    }

    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setLoadingState('thinking');
    setQuestion('');

    const formData = new FormData();
    formData.append('file', pdfFile);
    formData.append('question', question);
    formData.append('use_web_fallback', 'true');

    try {
      const res = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();

      // Check backend response type
      const source = data.source || 'pdf'; // fallback to 'pdf' if not provided
        if (source === 'web') {
          setLoadingState('web');
        } else {
          setLoadingState('thinking');
        }

        // Give the UI enough time to show the spinner
        setTimeout(() => {
          setMessages(prev => [...prev, { role: 'bot', content: data.answer }]);
          setLoadingState('idle');
        }, 2000); //  increase delay slightly to visualize transition

    } catch (err) {
      console.error("Fetch failed:", err);
      setMessages(prev => [...prev, { role: 'bot', content: "Something went wrong. Try again." }]);
      setLoadingState('idle');
    }
  };

  return (
    <div className="app-container">
      <h1 className="animated-heading">
        <span className="left">Product</span>
        <span className="right">Pal</span>
      </h1>

      <div className="layout">
        <UploadBox setPdfFile={setPdfFile} pdfFile={pdfFile} />

        <div className="chatbox">
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <ChatBubble key={i} content={msg.content} role={msg.role} />
            ))}

            {loadingState === 'thinking' && (
              <div className="loading-spinner">
                <div className="spinner" />
                <span> Thinking...</span>
              </div>
            )}

            {loadingState === 'web' && (
              <div className="loading-spinner">
                <div className="spinner" />
                <span>🔍 Searching the web...</span>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          <div className="chat-input">
            <input
              type="text"
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask a question..."
            />
            <button onClick={handleSend}>Send</button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
