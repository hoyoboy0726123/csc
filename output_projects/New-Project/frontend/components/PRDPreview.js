import { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronUpIcon, PencilIcon, CheckIcon, XIcon } from '@heroicons/react/24/outline';

export default function PRDPreview({ prdId, onFrozen }) {
  const [prd, setPrd] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState('');
  const [collapsedSections, setCollapsedSections] = useState({});
  const [chatInput, setChatInput] = useState('');
  const [chatting, setChatting] = useState(false);
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    if (prdId) fetchPRD();
  }, [prdId]);

  const fetchPRD = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/prd/${prdId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (!res.ok) throw new Error('Failed to fetch PRD');
      const data = await res.json();
      setPrd(data);
      setEditContent(data.prd_md);
      setMessages([{ role: 'assistant', content: data.prd_md }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleSection = (idx) => {
    setCollapsedSections((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const handleSave = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/prd/${prdId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ prd_md: editContent }),
      });
      if (!res.ok) throw new Error('Failed to update PRD');
      const updated = await res.json();
      setPrd(updated);
      setMessages((m) => [...m, { role: 'assistant', content: updated.prd_md }]);
      setEditing(false);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim()) return;
    const userMsg = { role: 'user', content: chatInput };
    setMessages((m) => [...m, userMsg]);
    setChatInput('');
    setChatting(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/prd/${prdId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ instruction: chatInput }),
      });
      if (!res.ok) throw new Error('Failed to revise PRD');
      const updated = await res.json();
      setPrd(updated);
      setMessages((m) => [...m, { role: 'assistant', content: updated.prd_md }]);
    } catch (err) {
      alert(err.message);
    } finally {
      setChatting(false);
    }
  };

  const handleFreeze = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/prd/${prdId}/freeze`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      });
      if (!res.ok) throw new Error('Failed to freeze PRD');
      const frozen = await res.json();
      setPrd(frozen);
      onFrozen?.(frozen);
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return <div className="p-4 text-gray-500">Loading PRD…</div>;
  if (error) return <div className="p-4 text-red-600">Error: {error}</div>;
  if (!prd) return null;

  const lines = prd.prd_md.split('\n');
  const sections = [];
  let current = [];
  lines.forEach((l) => {
    if (/^#{1,6} /.test(l)) {
      if (current.length) sections.push(current);
      current = [l];
    } else {
      current.push(l);
    }
  });
  if (current.length) sections.push(current);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h2 className="text-lg font-semibold text-gray-800">PRD Preview</h2>
        <div className="flex items-center gap-2">
          {!prd.frozen && (
            <>
              <button
                onClick={() => setEditing(!editing)}
                className="px-3 py-1.5 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700"
              >
                {editing ? <XIcon className="w-4 h-4 inline" /> : <PencilIcon className="w-4 h-4 inline" />}
                {editing ? ' Cancel' : ' Edit'}
              </button>
              {editing && (
                <button
                  onClick={handleSave}
                  className="px-3 py-1.5 text-sm rounded-md bg-green-600 text-white hover:bg-green-700"
                >
                  <CheckIcon className="w-4 h-4 inline" /> Save
                </button>
              )}
              <button
                onClick={handleFreeze}
                className="px-3 py-1.5 text-sm rounded-md bg-gray-800 text-white hover:bg-gray-900"
              >
                Freeze PRD
              </button>
            </>
          )}
          {prd.frozen && <span className="px-2 py-1 text-xs rounded-full bg-gray-200 text-gray-700">Frozen</span>}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {editing ? (
          <textarea
            className="w-full h-full font-mono text-sm border rounded-md p-3 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
          />
        ) : (
          <div className="prose prose-sm max-w-none">
            {sections.map((sec, idx) => {
              const header = sec[0];
              const level = header.match(/^#{1,6}/)[0].length;
              const title = header.replace(/^#{1,6} /, '');
              const body = sec.slice(1).join('\n');
              const collapsed = collapsedSections[idx];
              return (
                <div key={idx} className="mb-3">
                  <div
                    className="flex items-center justify-between cursor-pointer hover:bg-gray-50 rounded px-2 py-1"
                    onClick={() => toggleSection(idx)}
                  >
                    <h3 className={`m-0 text-base font-semibold text-gray-800`} style={{ paddingLeft: `${level * 12}px` }}>
                      {title}
                    </h3>
                    {collapsed ? <ChevronDownIcon className="w-4 h-4 text-gray-500" /> : <ChevronUpIcon className="w-4 h-4 text-gray-500" />}
                  </div>
                  {!collapsed && body && (
                    <div className="whitespace-pre-wrap text-gray-700 px-2 py-1" style={{ paddingLeft: `${level * 12 + 8}px` }}>
                      {body}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {!prd.frozen && (
        <div className="border-t p-4">
          <div className="flex items-center gap-2">
            <input
              className="flex-1 px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Tell AI how to adjust the PRD…"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !chatting && handleChat()}
            />
            <button
              onClick={handleChat}
              disabled={chatting}
              className="px-4 py-2 text-sm rounded-md bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {chatting ? 'Revising…' : 'Revise'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}