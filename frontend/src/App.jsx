import React, { useState } from 'react';
import UploadBox from './components/UploadBox';
import ChatBubble from './components/ChatBubble';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Welcome to ProductPal .Please upload a File to get started' }
  ]);
  const [question, setQuestion] = useState('');
  const [pdfFile, setPdfFile] = useState(null);

  const handleSend = async () => {
    if (!question.trim() || !pdfFile) return;

    setMessages(prev => [...prev, { role: 'user', content: question }]);

    const formData = new FormData();
    formData.append('file', pdfFile);
    formData.append('question', question);

    const res = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      body: formData
    });

    const data = await res.json();
    setMessages(prev => [...prev, { role: 'bot', content: data.answer }]);
    setQuestion('');
  };

  return (
    <div className="app-container">
      <h1>ProductPal</h1>
      <div className="layout">
        <UploadBox setPdfFile={setPdfFile} />
        <div className="chatbox">
          <div className="chat-messages">
          {messages.map((msg, i) => (
          <ChatBubble key={i} content={msg.content} role={msg.role} />
        ))}
        </div>
        <div className="chat-input">
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
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
