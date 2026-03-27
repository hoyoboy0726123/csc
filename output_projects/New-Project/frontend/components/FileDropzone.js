import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadAudio } from '../lib/api';

export default function FileDropzone({ onUploaded, onError }) {
  const [uploading, setUploading] = useState(false);

  const onDrop = useCallback(async (acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    const maxSize = 50 * 1024 * 1024; // 50 MB
    if (file.size > maxSize) {
      onError('檔案超過 50 MB 限制');
      return;
    }

    const allowedTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-wav'];
    if (!allowedTypes.includes(file.type)) {
      onError('僅支援 MP3 或 WAV 格式');
      return;
    }

    setUploading(true);
    try {
      const { task_id } = await uploadAudio(file);
      onUploaded(task_id);
    } catch (err) {
      onError(err.message || '上傳失敗');
    } finally {
      setUploading(false);
    }
  }, [onUploaded, onError]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    maxFiles: 1,
    disabled: uploading,
  });

  return (
    <div
      {...getRootProps()}
      className={`
        w-full max-w-xl mx-auto border-2 border-dashed rounded-xl p-8 text-center cursor-pointer
        transition-colors duration-200
        ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}
        ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <input {...getInputProps()} />
      {uploading ? (
        <div className="flex flex-col items-center space-y-2">
          <svg className="animate-spin h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span className="text-gray-700">上傳中，請稍候...</span>
        </div>
      ) : (
        <>
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" stroke="currentColor" fill="none" viewBox="0 0 48 48">
            <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L40 32" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <p className="text-gray-700 font-medium">
            {isDragActive ? '放開以上傳' : '拖曳音檔至此，或點擊選擇'}
          </p>
          <p className="text-gray-500 text-sm mt-2">支援 MP3 / WAV，最大 50 MB，最長 10 分鐘</p>
        </>
      )}
    </div>
  );
}