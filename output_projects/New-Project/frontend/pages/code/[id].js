import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { getCodeVersions, generateCode, fixCode, downloadZip } from '../../lib/api';
import { useAuth } from '../../lib/auth';
import StackSelector from '../../components/StackSelector';
import ZipDownload from '../../components/ZipDownload';
import ChatPanel from '../../components/ChatPanel';
import ErrorReport from '../../components/ErrorReport';
import MonacoEditor from '../../components/MonacoEditor';

const MonacoEditorNoSSR = dynamic(() => import('../../components/MonacoEditor'), { ssr: false });

export default function CodePage() {
  const router = useRouter();
  const { id: prdId } = router.query;
  const { user } = useAuth();
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [selectedStack, setSelectedStack] = useState('python');
  const [generating, setGenerating] = useState(false);
  const [fixing, setFixing] = useState(false);
  const [error, setError] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [showErrorReport, setShowErrorReport] = useState(false);
  const [currentFile, setCurrentFile] = useState('main.py');
  const [fileTree, setFileTree] = useState([]);
  const [fileContents, setFileContents] = useState({});

  useEffect(() => {
    if (!prdId) return;
    fetchVersions();
  }, [prdId]);

  useEffect(() => {
    if (selectedVersion) {
      loadVersionFiles(selectedVersion);
    }
  }, [selectedVersion]);

  const fetchVersions = async () => {
    try {
      const data = await getCodeVersions(prdId);
      setVersions(data);
      if (data.length > 0) {
        setSelectedVersion(data[0]);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const loadVersionFiles = async (version) => {
    try {
      const response = await fetch(`/api/v1/code/${version.id}/files`);
      const data = await response.json();
      setFileTree(data.tree);
      setFileContents(data.contents);
      setCurrentFile(data.tree[0]?.path || 'main.py');
    } catch (err) {
      setError('Failed to load version files');
    }
  };

  const handleGenerateCode = async () => {
    setGenerating(true);
    setError(null);
    try {
      const newVersion = await generateCode(prdId, selectedStack);
      setVersions([newVersion, ...versions]);
      setSelectedVersion(newVersion);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleFixCode = async (errorMessage, instruction) => {
    setFixing(true);
    setError(null);
    try {
      const fixedVersion = await fixCode(selectedVersion.id, errorMessage, instruction);
      setVersions([fixedVersion, ...versions]);
      setSelectedVersion(fixedVersion);
      setShowErrorReport(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setFixing(false);
    }
  };

  const handleChatMessage = async (message) => {
    const userMessage = { role: 'user', content: message };
    setChatMessages([...chatMessages, userMessage]);
    
    try {
      const response = await fetch(`/api/v1/code/${selectedVersion.id}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, history: chatMessages })
      });
      const data = await response.json();
      const aiMessage = { role: 'assistant', content: data.reply };
      setChatMessages([...chatMessages, userMessage, aiMessage]);
    } catch (err) {
      setError('Chat service unavailable');
    }
  };

  const handleFileSelect = (filePath) => {
    setCurrentFile(filePath);
  };

  const handleFileChange = (filePath, newContent) => {
    setFileContents(prev => ({ ...prev, [filePath]: newContent }));
  };

  const handleDownload = async () => {
    try {
      await downloadZip(selectedVersion.id);
    } catch (err) {
      setError('Download failed');
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Please login to continue</h1>
          <button
            onClick={() => router.push('/login')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Code Generation</h1>
          <p className="text-gray-600">PRD ID: {prdId}</p>
        </div>

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Panel - Controls */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-3">Technology Stack</h2>
              <StackSelector
                selected={selectedStack}
                onChange={setSelectedStack}
                disabled={generating}
              />
              <button
                onClick={handleGenerateCode}
                disabled={generating}
                className="w-full mt-3 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {generating ? 'Generating...' : 'Generate Code'}
              </button>
            </div>

            <div className="bg-white rounded-lg shadow p-4">
              <h2 className="text-lg font-semibold mb-3">Versions</h2>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {versions.map((version) => (
                  <div
                    key={version.id}
                    onClick={() => setSelectedVersion(version)}
                    className={`p-3 rounded cursor-pointer ${
                      selectedVersion?.id === version.id
                        ? 'bg-blue-100 border-blue-500 border'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                  >
                    <div className="font-medium">v{version.version}</div>
                    <div className="text-sm text-gray-600">{version.stack}</div>
                    <div className="text-xs text-gray-500">
                      {new Date(version.created_at).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {selectedVersion && (
              <div className="bg-white rounded-lg shadow p-4">
                <h2 className="text-lg font-semibold mb-3">Actions</h2>
                <button
                  onClick={handleDownload}
                  className="w-full mb-2 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                >
                  Download ZIP
                </button>
                <button
                  onClick={() => setShowErrorReport(true)}
                  className="w-full px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700"
                >
                  Report Error
                </button>
              </div>
            )}
          </div>

          {/* Center - Code Editor */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="border-b px-4 py-2 flex items-center justify-between">
                <div className="flex space-x-2">
                  {Object.keys(fileContents).map((file) => (
                    <button
                      key={file}
                      onClick={() => handleFileSelect(file)}
                      className={`px-3 py-1 text-sm rounded ${
                        currentFile === file
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-100'
                      }`}
                    >
                      {file.split('/').pop()}
                    </button>
                  ))}
                </div>
              </div>
              <div className="h-96">
                <MonacoEditorNoSSR
                  language={selectedStack === 'python' ? 'python' : 'javascript'}
                  value={fileContents[currentFile] || ''}
                  onChange={(value) => handleFileChange(currentFile, value)}
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Right Panel - Chat */}
          <div className="lg:col-span-1">
            <ChatPanel
              messages={chatMessages}
              onSendMessage={handleChatMessage}
              placeholder="Ask about the code..."
            />
          </div>
        </div>
      </div>

      {showErrorReport && (
        <ErrorReport
          onSubmit={handleFixCode}
          onClose={() => setShowErrorReport(false)}
          loading={fixing}
        />
      )}
    </div>
  );
}