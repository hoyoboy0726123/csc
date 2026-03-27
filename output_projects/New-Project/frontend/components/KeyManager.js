import { useState, useEffect } from 'react';
import { getUserKeys, updateUserKeys } from '../lib/api';

export default function KeyManager({ onClose }) {
  const [keys, setKeys] = useState({ gemini: '', groq: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchKeys();
  }, []);

  const fetchKeys = async () => {
    try {
      const data = await getUserKeys();
      setKeys({
        gemini: data.gemini_key_enc ? '********' : '',
        groq: data.groq_key_enc ? '********' : ''
      });
    } catch (err) {
      setMessage('無法載入金鑰');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage('');
    try {
      const payload = {};
      if (keys.gemini && !keys.gemini.includes('*')) payload.gemini_key = keys.gemini;
      if (keys.groq && !keys.groq.includes('*')) payload.groq_key = keys.groq;

      if (Object.keys(payload).length === 0) {
        setMessage('無需更新');
        setSaving(false);
        return;
      }

      await updateUserKeys(payload);
      setMessage('金鑰已更新');
      setTimeout(() => onClose(), 1000);
    } catch (err) {
      setMessage('更新失敗');
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setKeys(prev => ({ ...prev, [name]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="text-xl font-bold mb-4">API 金鑰管理</h2>

        {loading ? (
          <div className="text-center py-4">載入中…</div>
        ) : (
          <>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Gemini API Key</label>
              <input
                type="password"
                name="gemini"
                value={keys.gemini}
                onChange={handleChange}
                placeholder="輸入新的 Gemini API Key（留空保持原值）"
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">僅在需要時輸入，系統將加密儲存</p>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Groq API Key</label>
              <input
                type="password"
                name="groq"
                value={keys.groq}
                onChange={handleChange}
                placeholder="輸入新的 Groq API Key（留空保持原值）"
                className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">僅在需要時輸入，系統將加密儲存</p>
            </div>

            {message && (
              <div className="mb-4 text-sm text-green-600">{message}</div>
            )}

            <div className="flex justify-end space-x-2">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100"
              >
                取消
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? '儲存中…' : '儲存'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}