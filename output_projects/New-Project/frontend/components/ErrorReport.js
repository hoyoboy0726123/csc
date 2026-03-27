import { useState } from 'react';
import { XCircleIcon, CheckCircleIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

export default function ErrorReport({ error, onClose, onRetry }) {
  const [isMinimized, setIsMinimized] = useState(false);

  if (!error) return null;

  const getErrorIcon = () => {
    if (error.level === 'warning') return InformationCircleIcon;
    if (error.level === 'success') return CheckCircleIcon;
    return XCircleIcon;
  };

  const Icon = getErrorIcon();

  const getHeaderColor = () => {
    if (error.level === 'warning') return 'bg-yellow-50 border-yellow-200 text-yellow-800';
    if (error.level === 'success') return 'bg-green-50 border-green-200 text-green-800';
    return 'bg-red-50 border-red-200 text-red-800';
  };

  const getButtonColor = () => {
    if (error.level === 'warning') return 'bg-yellow-600 hover:bg-yellow-700';
    if (error.level === 'success') return 'bg-green-600 hover:bg-green-700';
    return 'bg-red-600 hover:bg-red-700';
  };

  return (
    <div className="fixed bottom-4 right-4 w-96 z-50 animate-slide-in-right">
      <div className={`rounded-lg border shadow-lg ${getHeaderColor()}`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-current border-opacity-20">
          <div className="flex items-center space-x-3">
            <Icon className="h-5 w-5" />
            <h3 className="font-semibold">{error.title || '系統訊息'}</h3>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsMinimized(!isMinimized)}
              className="p-1 rounded hover:bg-current hover:bg-opacity-10 transition-colors"
            >
              <svg
                className={`h-4 w-4 transform transition-transform ${isMinimized ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
              </svg>
            </button>
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-current hover:bg-opacity-10 transition-colors"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Body */}
        {!isMinimized && (
          <div className="p-4">
            <div className="text-sm mb-4 whitespace-pre-wrap">{error.message}</div>
            
            {error.details && (
              <details className="mb-4">
                <summary className="cursor-pointer text-sm font-medium hover:underline">
                  詳細資訊
                </summary>
                <pre className="mt-2 text-xs bg-black bg-opacity-5 p-3 rounded overflow-x-auto">
                  {error.details}
                </pre>
              </details>
            )}

            {error.suggestion && (
              <div className="mb-4 p-3 bg-white bg-opacity-50 rounded text-sm">
                <strong>建議：</strong> {error.suggestion}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end space-x-3">
              {onRetry && (
                <button
                  onClick={onRetry}
                  className={`px-4 py-2 text-white text-sm font-medium rounded ${getButtonColor()} transition-colors`}
                >
                  重試
                </button>
              )}
              <button
                onClick={onClose}
                className="px-4 py-2 border border-current border-opacity-30 text-sm font-medium rounded hover:bg-current hover:bg-opacity-5 transition-colors"
              >
                關閉
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}