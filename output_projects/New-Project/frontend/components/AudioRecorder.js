import { useState, useRef, useEffect } from 'react';
import { apiUploadAudio } from '../lib/api';

export default function AudioRecorder({ onTranscription }) {
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [duration, setDuration] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const startTimeRef = useRef(0);
  const pausedTimeRef = useRef(0);

  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
    };
  }, [audioUrl]);

  const startTimer = () => {
    startTimeRef.current = Date.now() - pausedTimeRef.current;
    timerRef.current = setInterval(() => {
      setDuration(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
  };

  const stopTimer = () => {
    clearInterval(timerRef.current);
    timerRef.current = null;
  };

  const resetTimer = () => {
    stopTimer();
    setDuration(0);
    pausedTimeRef.current = 0;
  };

  const startRecording = async () => {
    try {
      setError('');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
      };

      recorder.start();
      setIsRecording(true);
      startTimer();
    } catch (err) {
      setError('無法啟用麥克風，請檢查權限或更換瀏覽器。');
    }
  };

  const pauseRecording = () => {
    if (mediaRecorderRef.current && isRecording && !isPaused) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      pausedTimeRef.current = Date.now() - startTimeRef.current;
      stopTimer();
    }
  };

  const resumeRecording = () => {
    if (mediaRecorderRef.current && isRecording && isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      startTimer();
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      resetTimer();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
        streamRef.current = null;
      }
    }
  };

  const resetRecording = () => {
    stopRecording();
    setAudioBlob(null);
    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl('');
    }
    setError('');
  };

  const uploadAudio = async () => {
    if (!audioBlob) return;
    setUploading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.webm');
      const { task_id } = await apiUploadAudio(formData);
      onTranscription(task_id);
    } catch (err) {
      setError('上傳失敗，請重試。');
    } finally {
      setUploading(false);
    }
  };

  const formatTime = (sec) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full max-w-xl mx-auto bg-white rounded-xl shadow p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-800">語音輸入</h3>
        {isRecording && (
          <span className="text-sm text-gray-500">{formatTime(duration)}</span>
        )}
      </div>

      {!isRecording && !audioBlob && (
        <div className="flex flex-col items-center space-y-4">
          <button
            onClick={startRecording}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            開始錄音
          </button>
          <p className="text-sm text-gray-500">最長 10 分鐘，最大 50 MB</p>
        </div>
      )}

      {isRecording && (
        <div className="flex flex-col items-center space-y-4">
          <div className="flex items-center space-x-3">
            <span className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
            <span className="text-sm text-gray-700">錄音中...</span>
          </div>
          <div className="flex space-x-3">
            {isPaused ? (
              <button
                onClick={resumeRecording}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                繼續
              </button>
            ) : (
              <button
                onClick={pauseRecording}
                className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition"
              >
                暫停
              </button>
            )}
            <button
              onClick={stopRecording}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition"
            >
              停止
            </button>
          </div>
        </div>
      )}

      {audioBlob && (
        <div className="space-y-4">
          <audio src={audioUrl} controls className="w-full" />
          <div className="flex space-x-3">
            <button
              onClick={uploadAudio}
              disabled={uploading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
            >
              {uploading ? '上傳中...' : '轉換為 PRD'}
            </button>
            <button
              onClick={resetRecording}
              className="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition"
            >
              重新錄製
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded p-3">
          {error}
        </div>
      )}
    </div>
  );
}