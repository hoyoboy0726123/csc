import { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import AudioRecorder from '../components/AudioRecorder'
import FileDropzone from '../components/FileDropzone'
import { uploadAudio, createPRDFromText } from '../lib/api'
import { getToken } from '../lib/auth'

export default function Home() {
  const router = useRouter()
  const [inputMode, setInputMode] = useState('text')
  const [textInput, setTextInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!getToken()) {
      router.push('/login')
    }
  }, [router])

  const handleAudioUpload = async (blob) => {
    setLoading(true)
    setMessage('')
    try {
      const formData = new FormData()
      formData.append('file', blob, 'recording.webm')
      const { task_id } = await uploadAudio(formData)
      router.push(`/prd/${task_id}`)
    } catch (err) {
      setMessage(err.message || '上傳失敗')
    } finally {
      setLoading(false)
    }
  }

  const handleFileDrop = async (file) => {
    setLoading(true)
    setMessage('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const { task_id } = await uploadAudio(formData)
      router.push(`/prd/${task_id}`)
    } catch (err) {
      setMessage(err.message || '上傳失敗')
    } finally {
      setLoading(false)
    }
  }

  const handleTextSubmit = async () => {
    if (!textInput.trim()) return
    setLoading(true)
    setMessage('')
    try {
      const { task_id } = await createPRDFromText(textInput)
      router.push(`/prd/${task_id}`)
    } catch (err) {
      setMessage(err.message || '建立失敗')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-2xl bg-white rounded-xl shadow-md p-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2 text-center">Voice-to-Code Pipeline</h1>
        <p className="text-gray-600 text-center mb-8">將語音或文字轉化為可執行的專案代碼</p>

        <div className="flex justify-center mb-6">
          <div className="inline-flex rounded-md shadow-sm">
            <button
              onClick={() => setInputMode('text')}
              className={`px-4 py-2 text-sm font-medium rounded-l-lg border ${
                inputMode === 'text'
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              文字輸入
            </button>
            <button
              onClick={() => setInputMode('record')}
              className={`px-4 py-2 text-sm font-medium border-t border-b ${
                inputMode === 'record'
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              即時錄音
            </button>
            <button
              onClick={() => setInputMode('upload')}
              className={`px-4 py-2 text-sm font-medium rounded-r-lg border ${
                inputMode === 'upload'
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
              }`}
            >
              上傳音檔
            </button>
          </div>
        </div>

        {inputMode === 'text' && (
          <div>
            <textarea
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="請描述您的需求，例如：建立一個代辦事項網站，支援新增、刪除、標記完成..."
              className="w-full h-40 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <button
              onClick={handleTextSubmit}
              disabled={loading || !textInput.trim()}
              className="mt-4 w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? '處理中...' : '生成 PRD'}
            </button>
          </div>
        )}

        {inputMode === 'record' && (
          <div className="flex flex-col items-center">
            <AudioRecorder onStop={handleAudioUpload} disabled={loading} />
            <p className="text-sm text-gray-500 mt-4">錄音最長 10 分鐘，檔案最大 50 MB</p>
          </div>
        )}

        {inputMode === 'upload' && (
          <div>
            <FileDropzone onDrop={handleFileDrop} disabled={loading} accept="audio/*" />
            <p className="text-sm text-gray-500 mt-4">支援 MP3、WAV 格式，檔案最大 50 MB</p>
          </div>
        )}

        {message && (
          <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-lg text-sm">{message}</div>
        )}
      </div>
    </div>
  )
}