import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useLocalProfile } from '../hooks/useLocalProfile';
import type { HistoryRecord } from '../types';

export default function HistoryPage() {
  const navigate = useNavigate();
  const { userId } = useLocalProfile();
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getHistory(userId || undefined)
      .then(r => setRecords(r.history.reverse()))
      .catch(() => setRecords([]))
      .finally(() => setLoading(false));
  }, [userId]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center gap-3">
          <button onClick={() => navigate('/')} className="text-gray-400">← 返回</button>
          <span className="font-bold text-gray-900">历史记录</span>
        </div>
      </header>

      <div className="max-w-md mx-auto px-4 py-5">
        {loading ? (
          <div className="text-center py-12 text-gray-400">加载中...</div>
        ) : records.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-4xl mb-3">📋</p>
            <p className="text-gray-500">还没有分析记录</p>
            <button onClick={() => navigate('/')} className="btn-primary mt-4 w-auto px-6">
              去分析第一张菜单
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {records.map(r => (
              <div
                key={r.id}
                className="card cursor-pointer active:bg-gray-50"
                onClick={() => navigate('/result', { state: { result: r } })}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      {r.recommendations.slice(0, 3).map((d, i) => (
                        <span key={i} className="font-medium text-gray-900 text-sm">{d.name}</span>
                      ))}
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(r.timestamp).toLocaleDateString('zh-CN', {
                        month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
                      })}
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="tag bg-brand-100 text-brand-700 text-xs">{r.goal}</span>
                    <span className="text-xs text-gray-400">{r.dishes_count} 道菜</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
