import { useState } from 'react';
import { downloadZip } from '../lib/api';

export default function ZipDownload({ prdId, stack, version = 1 }) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);

  const handleDownload = async () => {
    setDownloading(true);
    setError(null);
    try {
      const blob = await downloadZip(prdId, stack, version);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `v2c_${stack}_v${version}.zip`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || '下載失敗');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="flex flex-col items-center space-y-2">
      <button
        onClick={handleDownload}
        disabled={downloading}
        className={`px-4 py-2 rounded-md text-white font-medium ${
          downloading
            ? 'bg-gray-400 cursor-not-allowed'
            : 'bg-indigo-600 hover:bg-indigo-700'
        }`}
      >
        {downloading ? '打包中…' : '下載 ZIP'}
      </button>
      {error && (
        <p className="text-sm text-red-600">{error}</p>
      )}
    </div>
  );
}