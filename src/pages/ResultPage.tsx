import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import type { AnalyzeResult, MoodOption } from '../types';

const MOOD_OPTIONS: { value: MoodOption; emoji: string; label: string }[] = [
  { value: '均衡', emoji: '⚖️', label: '均衡' },
  { value: '更饱', emoji: '🍚', label: '更饱' },
  { value: '更便宜', emoji: '💰', label: '省钱' },
  { value: '更清淡', emoji: '🥗', label: '清淡' },
  { value: '更好吃', emoji: '😋', label: '好吃' },
];

const CATEGORY_COLORS: Record<string, string> = {
  '蛋白质': 'bg-blue-100 text-blue-700',
  '蔬菜': 'bg-green-100 text-green-700',
  '主食': 'bg-yellow-100 text-yellow-700',
  '其他': 'bg-gray-100 text-gray-600',
};

export default function ResultPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const result = location.state?.result as AnalyzeResult | undefined;
  const [copied, setCopied] = useState(false);
  const [showAll, setShowAll] = useState(false);

  if (!result) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">没有分析结果</p>
          <button onClick={() => navigate('/')} className="btn-primary w-auto px-6">
            返回首页
          </button>
        </div>
      </div>
    );
  }

  const copyNotes = async () => {
    const text = result.order_notes.join('\n');
    await navigator.clipboard.writeText(text).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const currentMood = MOOD_OPTIONS.find(m => m.value === result.mood);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center gap-3">
          <button onClick={() => navigate('/')} className="text-gray-400 hover:text-gray-600">
            ← 返回
          </button>
          <span className="font-bold text-gray-900">点单建议</span>
          {currentMood && (
            <span className="ml-auto tag bg-brand-100 text-brand-700">
              {currentMood.emoji} {currentMood.label}
            </span>
          )}
        </div>
      </header>

      <div className="max-w-md mx-auto px-4 py-5 space-y-4">
        {/* 偏好调整开关 */}
        <div className="card">
          <p className="text-xs text-gray-500 mb-2">调整今日偏好，重新分析</p>
          <div className="grid grid-cols-5 gap-1.5">
            {MOOD_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => navigate('/', { state: { mood: opt.value } })}
                className={`flex flex-col items-center py-2 rounded-xl transition-all text-xs ${
                  result.mood === opt.value
                    ? 'bg-brand-600 text-white'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                <span className="text-base">{opt.emoji}</span>
                <span className="mt-0.5">{opt.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 推荐组合 */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-gray-900">🍽️ 最佳点单组合</h2>
            <span className="tag bg-brand-100 text-brand-700 text-xs">{result.goal}</span>
          </div>
          <div className="space-y-3">
            {result.recommendations.map((dish, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl">
                <div className="w-7 h-7 bg-brand-600 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-white text-xs font-bold">{i + 1}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-gray-900">{dish.name}</span>
                    <span className={`tag text-xs ${CATEGORY_COLORS[dish.category] || CATEGORY_COLORS['其他']}`}>
                      {dish.category}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">{dish.reason}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 下单备注 */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-gray-900">📝 下单备注</h2>
            <button
              onClick={copyNotes}
              className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
                copied ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-600'
              }`}
            >
              {copied ? '✓ 已复制' : '复制全部'}
            </button>
          </div>
          <div className="space-y-2">
            {result.order_notes.map((note, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-gray-700">
                <span className="text-brand-600">•</span>
                <span>{note}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 替代方案 */}
        {result.alternatives.length > 0 && (
          <div className="card">
            <button
              onClick={() => setShowAll(!showAll)}
              className="flex items-center justify-between w-full"
            >
              <h2 className="font-bold text-gray-900">🔄 备选菜品</h2>
              <span className="text-xs text-gray-400">{showAll ? '收起' : '展开'}</span>
            </button>
            {showAll && (
              <div className="mt-3 flex flex-wrap gap-2">
                {result.alternatives.map((dish, i) => (
                  <span key={i} className="tag bg-gray-100 text-gray-600 py-1.5 px-3 text-sm">
                    {dish}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 识别到的菜单 */}
        <div className="card">
          <button
            onClick={() => setShowAll(!showAll)}
            className="flex items-center justify-between w-full"
          >
            <h2 className="text-sm font-semibold text-gray-600">
              识别到 {result.dishes.length} 道菜
            </h2>
            <span className="text-xs text-gray-400">
              {result.ocr_source === 'mock' ? '示例数据' : 'AI 识别'}
            </span>
          </button>
        </div>

        {/* 免责声明 */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3">
          <p className="text-xs text-amber-700">{result.disclaimer}</p>
        </div>

        {/* 再分析一次 */}
        <button onClick={() => navigate('/')} className="btn-primary">
          📷 再分析一家餐厅
        </button>
      </div>
    </div>
  );
}
