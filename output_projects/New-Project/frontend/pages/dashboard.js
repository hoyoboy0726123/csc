import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { getToken, logout } from '../lib/auth';
import { api } from '../lib/api';
import AudioRecorder from '../components/AudioRecorder';
import FileDropzone from '../components/FileDropzone';
import PRDPreview from '../components/PRDPreview';
import StackSelector from '../components/StackSelector';
import ZipDownload from '../components/ZipDownload';
import ChatPanel from '../components/ChatPanel';
import KeyManager from '../components/KeyManager';
import QuotaBanner from '../components/QuotaBanner';
import ErrorReport from '../components/ErrorReport';

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const [prdMd, setPrdMd] = useState('');
  const [prdTitle, setPrdTitle] = useState('');
  const [frozen, setFrozen] = useState(false);
  const [stack, setStack] = useState('');
  const [zipPath, setZipPath] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('input'); // input, prd, code, fix
  const [fixInput, setFixInput] = useState('');
  const [fixOutput, setFixOutput] = useState('');

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push('/login');
      return;
    }
    fetchUser();
    fetchHistory();
  }, []);

  const fetchUser = async () => {
    try {
      const data = await api.get('/auth/me');
      setUser(data);
    } catch (err) {
      console.error(err);
      logout();
      router.push('/login');
    }
  };

  const fetchHistory = async () => {
    try {
      const data = await api.get('/prd/history');
      setHistory(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleAudioUpload = async (blob) => {
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', blob, 'audio.webm');
    try {
      const { task_id } = await api.post('/upload/audio', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setTaskId(task_id);
      pollTask(task_id);
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFileDrop = async (file) => {
    setLoading(true);
    setError('');
    const formData = new FormData();
    formData.append('file', file);
    try {
      const { task_id } = await api.post('/upload/audio', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setTaskId(task_id);
      pollTask(task_id);
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const pollTask = async (tid) => {
    const interval = setInterval(async () => {
      try {
        const data = await api.get(`/prd/${tid}`);
        if (data.status === 'completed') {
          setPrdMd(data.prd_md);
          setPrdTitle(data.title);
          setFrozen(data.frozen);
          setTaskId(tid);
          clearInterval(interval);
        }
      } catch (err) {
        clearInterval(interval);
        setError(err.message || 'Polling failed');
      }
    }, 2000);
  };

  const handlePrdUpdate = async (instruction) => {
    if (!taskId) return;
    setLoading(true);
    try {
      const data = await api.patch(`/prd/${taskId}`, { instruction });
      setPrdMd(data.prd_md);
    } catch (err) {
      setError(err.message || 'Update failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFreeze = async () => {
    if (!taskId) return;
    setLoading(true);
    try {
      await api.post(`/prd/${taskId}/freeze`);
      setFrozen(true);
    } catch (err) {
      setError(err.message || 'Freeze failed');
    } finally {
      setLoading(false);
    }
  };

  const handleStackSelect = async (selectedStack) => {
    if (!taskId) return;
    setStack(selectedStack);
    setLoading(true);
    try {
      const data = await api.post('/code/generate', { prd_id: taskId, stack: selectedStack });
      setZipPath(data.zip_path);
      setActiveTab('code');
    } catch (err) {
      setError(err.message || 'Code generation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleFix = async () => {
    if (!taskId || !fixInput) return;
    setLoading(true);
    try {
      const data = await api.post('/fix', { prd_id: taskId, error: fixInput });
      setFixOutput(data.suggestion);
    } catch (err) {
      setError(err.message || 'Fix failed');
    } finally {
      setLoading(false);
    }
  };

  const handleHistorySelect = async (id) => {
    setLoading(true);
    try {
      const data = await api.get(`/prd/${id}`);
      setTaskId(id);
      setPrdMd(data.prd_md);
      setPrdTitle(data.title);
      setFrozen(data.frozen);
      setActiveTab('prd');
    } catch (err) {
      setError(err.message || 'Load history failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <QuotaBanner user={user} />
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <h1 className="text-xl font-bold text-gray-900">Voice-to-Code Dashboard</h1>
          <div className="flex items-center space-x-4">
            <KeyManager />
            <button
              onClick={handleLogout}
              className="text-sm text-gray-700 hover:text-gray-900"
            >
              登出
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">{error}</div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <aside className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded shadow p-4">
              <h2 className="font-semibold mb-2">歷史專案</h2>
              <ul className="space-y-2 max-h-64 overflow-auto">
                {history.map((h) => (
                  <li
                    key={h.id}
                    onClick={() => handleHistorySelect(h.id)}
                    className="cursor-pointer text-blue-600 hover:underline text-sm"
                  >
                    {h.title}
                  </li>
                ))}
              </ul>
            </div>
          </aside>

          <section className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded shadow">
              <nav className="flex border-b">
                {['input', 'prd', 'code', 'fix'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-2 text-sm font-medium ${
                      activeTab === tab
                        ? 'border-b-2 border-blue-500 text-blue-600'
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    {tab === 'input' && '輸入需求'}
                    {tab === 'prd' && 'PRD 預覽'}
                    {tab === 'code' && '生成代碼'}
                    {tab === 'fix' && '錯誤修復'}
                  </button>
                ))}
              </nav>

              <div className="p-4">
                {activeTab === 'input' && (
                  <div className="space-y-4">
                    <AudioRecorder onUpload={handleAudioUpload} disabled={loading} />
                    <FileDropzone onDrop={handleFileDrop} disabled={loading} />
                  </div>
                )}

                {activeTab === 'prd' && (
                  <div>
                    <PRDPreview
                      prdMd={prdMd}
                      prdTitle={prdTitle}
                      frozen={frozen}
                      onUpdate={handlePrdUpdate}
                      onFreeze={handleFreeze}
                      loading={loading}
                    />
                    <ChatPanel
                      taskId={taskId}
                      onSend={handlePrdUpdate}
                      disabled={frozen || loading}
                    />
                  </div>
                )}

                {activeTab === 'code' && (
                  <div>
                    <StackSelector
                      selected={stack}
                      onSelect={handleStackSelect}
                      disabled={!frozen || loading}
                    />
                    {zipPath && <ZipDownload zipPath={zipPath} />}
                  </div>
                )}

                {activeTab === 'fix' && (
                  <ErrorReport
                    value={fixInput}
                    onChange={setFixInput}
                    onSubmit={handleFix}
                    output={fixOutput}
                    loading={loading}
                  />
                )}
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}