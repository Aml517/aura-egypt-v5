import { useState, useRef, useEffect } from 'react'

export default function CleopatraChat({ tripData }) {
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'I am Cleopatra. What movie haunts your dreams, my traveler?' }
  ])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  const sendMessage = async () => {
    const userMsg = { role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    
    const res = await fetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message: input, context: tripData })
    })
    const { response } = await res.json()
    
    setMessages(prev => [...prev, { role: 'ai', content: response }])
    setInput('')
  }

  return (
    <div className="fixed bottom-8 right-8 w-96 h-96 bg-gradient-to-t from-black/80 to-transparent backdrop-blur-xl rounded-3xl p-6 shadow-2xl border border-yellow-500/50">
      <div className="h-72 overflow-y-auto space-y-4 mb-4 pr-2">
        {messages.map((msg, i) => (
          <div key={i} className={`p-3 rounded-2xl ${msg.role === 'ai' ? 'bg-gradient-to-r from-yellow-500/20' : 'bg-white/10 ml-auto'}`}>
            {msg.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && sendMessage()}
          className="flex-1 bg-white/10 p-3 rounded-xl outline-none"
          placeholder="Speak to Cleopatra..."
        />
        <button onClick={sendMessage} className="bg-yellow-500 text-black px-4 py-3 rounded-xl font-bold">
          →
        </button>
      </div>
    </div>
  )
}