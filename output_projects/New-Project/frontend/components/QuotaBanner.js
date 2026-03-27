import { useEffect, useState } from 'react';
import { getQuota } from '../lib/api';

export default function QuotaBanner() {
  const [quota, setQuota] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchQuota = async () => {
      try {
        const data = await getQuota();
        setQuota(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchQuota();
    const interval = setInterval(fetchQuota, 86400000); // 每日檢查一次
    return () => clearInterval(interval);
  }, []);

  if (loading) return null;
  if (error) return null;

  const { usage, limit, percentage } = quota;
  const isLow = percentage < 10;

  if (!isLow) return null;

  return (
    <div className="w-full bg-yellow-400 text-yellow-900 px-4 py-2 text-sm font-medium flex items-center justify-center">
      <span className="mr-2">⚠️</span>
      配額即將用盡：已使用 {usage} / {limit}（剩餘 {100 - percentage}%）
    </div>
  );
}