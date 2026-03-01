import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useLocalProfile } from '../hooks/useLocalProfile';
import type { MoodOption, AnalyzeResult } from '../types';

const MOOD_OPTIONS: { value: MoodOption; emoji: string; label: string }[] = [
  { value: '均衡', emoji: '⚖️', label: '均衡' },
  { value: '更饱', emoji: '🍚', label: '更饱' },
  { value: '更便宜', emoji: '💰', label: '省钱' },
  { value: '更清淡', emoji: '🥗', label: '清淡' },
  { value: '更好吃', emoji: '😋', label: '好吃' },
];

export default function HomePage() {
  const navigate = useNavigate();
  const { profile, userId } = useLocalProfile();
  const fileRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [mood, setMood] = useState<MoodOption>('均衡');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleFile = (f: File) => {
    setFile(f);
    const reader = new FileReader();
    reader.onload = e => setPreview(e.target?.result as string);
    reader.readAsDataURL(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f && f.type.startsWith('image/')) handleFile(f);
  };

  const handleAnalyze = async () => {
    if (!file || !userId) return;
    setLoading(true);
    setError('');
    try {
      const result: AnalyzeResult = await api.analyzeMenu(file, userId, mood);
      navigate('/result', { state: { result } });
    } catch (err: any) {
      setError(err.message || '分析失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const goalColors: Record<string, string> = {
    '减脂': 'bg-orange-100 text-orange-700',
    '增肌': 'bg-blue-100 text-blue-700',
    '维持': 'bg-green-100 text-green-700',
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-xs font-bold">MF</span>
            </div>
            <span className="font-bold text-gray-900">MenuFit</span>
          </div>
          <div className="flex items-center gap-2">
            {profile && (
              <span className={`tag ${goalColors[profile.goal] || 'bg-gray-100 text-gray-600'}`}>
                {profile.goal}
              </span>
            )}
            <button
              onClick={() => navigate('/profile')}
              className="text-gray-400 hover:text-gray-600 text-sm"
            >
              编辑
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-md mx-auto px-4 py-6 space-y-5">
        {/* 今日偏好 */}
        <div className="card">
          <p className="text-sm font-semibold text-gray-700 mb-3">今天更想要…</p>
          <div className="grid grid-cols-5 gap-2">
            {MOOD_OPTIONS.map(opt => (
              <button
                key={opt.value}
                onClick={() => setMood(opt.value)}
                className={`flex flex-col items-center py-2.5 rounded-xl transition-all ${
                  mood === opt.value
                    ? 'bg-brand-600 text-white scale-105 shadow-md'
                    : 'bg-gray-100 text-gray-600'
                }`}
              >
                <span className="text-lg">{opt.emoji}</span>
                <span className="text-xs mt-0.5">{opt.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* 上传区域 */}
        <div
          className={`card border-2 border-dashed transition-colors cursor-pointer ${
            preview ? 'border-brand-300' : 'border-gray-200 hover:border-brand-300'
          }`}
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          onClick={() => !preview && fileRef.current?.click()}
        >
          {preview ? (
            <div className="relative">
              <img src={preview} alt="菜单预览" className="w-full rounded-xl object-contain max-h-64" />
              <button
                onClick={e => { e.stopPropagation(); setPreview(null); setFile(null); }}
                className="absolute top-2 right-2 bg-black/50 text-white rounded-full w-7 h-7 flex items-center justify-center text-sm"
              >
                ✕
              </button>
            </div>
          ) : (
            <div className="text-center py-10">
              <div className="text-4xl mb-3">📷</div>
              <p className="font-semibold text-gray-700">上传菜单照片</p>
              <p className="text-sm text-gray-400 mt-1">点击选择或拖拽图片到此处</p>
              <p className="text-xs text-gray-300 mt-2">支持 JPG / PNG / HEIC</p>
            </div>
          )}
        </div>

        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f); }}
        />

        {/* 拍照按钮 */}
        {!preview && (
          <button
            onClick={() => fileRef.current?.click()}
            className="w-full py-3 bg-gray-100 text-gray-700 rounded-xl font-medium text-sm"
          >
            📱 拍照上传菜单
          </button>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600">
            {error}
          </div>
        )}

        {/* 分析按钮 */}
        <button
          onClick={handleAnalyze}
          disabled={!file || loading}
          className="btn-primary"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⏳</span> AI 正在分析菜单...
            </span>
          ) : (
            '🍽️ 帮我选菜'
          )}
        </button>

        {/* 历史记录入口 */}
        <button
          onClick={() => navigate('/history')}
          className="w-full text-center text-sm text-gray-400 py-2"
        >
          查看历史记录 →
        </button>
      </div>
    </div>
  );
}
