import { useState, useEffect, useRef } from 'react'
import { PaperAirplaneIcon } from '@heroicons/react/24/solid'

export default function ChatPanel({ taskId, onPRDUpdate, onError }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg = input.trim()
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/api/v1/prd/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ instruction: userMsg })
      })
      if (!res.ok) throw new Error('Network error')
      const data = await res.json()
      const assistantMsg = data.prd_md || '已更新 PRD'
      setMessages(prev => [...prev, { role: 'assistant', content: assistantMsg }])
      onPRDUpdate(data.prd_md)
    } catch (err) {
      onError(err.message || '更新失敗')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-xl shadow">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700">對話修正</h3>
      </div>
      <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-sm text-gray-500">例如：「幫我把價格改為新台幣」</div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`text-sm ${m.role === 'user' ? 'text-right' : 'text-left'}`}>
            <div
              className={`inline-block px-3 py-2 rounded-lg max-w-xl ${
                m.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-sm text-gray-500">思考中…</div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="px-4 py-3 border-t border-gray-200 flex items-center space-x-2">
        <textarea
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="輸入修正指令…"
          className="flex-1 resize-none rounded-lg border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          rows={2}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50"
        >
          <PaperAirplaneIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}