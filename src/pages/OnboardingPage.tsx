import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import { useLocalProfile } from '../hooks/useLocalProfile';
import type { UserProfile } from '../types';

const DIET_OPTIONS = ['不吃辣', '不吃牛肉', '清真', '素食', '乳糖不耐', '不吃海鲜'];

export default function OnboardingPage() {
  const navigate = useNavigate();
  const { saveProfile } = useLocalProfile();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [form, setForm] = useState<UserProfile>({
    gender: 'male',
    age: 28,
    height: 170,
    weight: 65,
    goal: '减脂',
    diet_prefs: [],
    activity_level: '中',
    allergies: [],
  });

  const toggle = (key: 'diet_prefs' | 'allergies', val: string) => {
    setForm(f => ({
      ...f,
      [key]: f[key].includes(val) ? f[key].filter(x => x !== val) : [...f[key], val],
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await api.saveProfile(form);
      saveProfile(form, res.user_id);
      navigate('/');
    } catch (err: any) {
      setError(err.message || '保存失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-50 to-white">
      <div className="max-w-md mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-brand-600 rounded-2xl flex items-center justify-center mx-auto mb-3">
            <span className="text-white text-2xl font-bold">MF</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">欢迎使用 MenuFit</h1>
          <p className="text-gray-500 mt-1 text-sm">填写你的身体信息，获取专属点单建议</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* 性别 */}
          <div className="card">
            <label className="block text-sm font-semibold text-gray-700 mb-3">性别</label>
            <div className="grid grid-cols-2 gap-3">
              {(['male', 'female'] as const).map(g => (
                <button
                  key={g}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, gender: g }))}
                  className={`py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    form.gender === g
                      ? 'bg-brand-600 text-white'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {g === 'male' ? '男' : '女'}
                </button>
              ))}
            </div>
          </div>

          {/* 基本信息 */}
          <div className="card space-y-4">
            <label className="block text-sm font-semibold text-gray-700">基本信息</label>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: '年龄', key: 'age', unit: '岁', min: 10, max: 100 },
                { label: '身高', key: 'height', unit: 'cm', min: 100, max: 250 },
                { label: '体重', key: 'weight', unit: 'kg', min: 30, max: 300 },
              ].map(({ label, key, unit, min, max }) => (
                <div key={key}>
                  <label className="block text-xs text-gray-500 mb-1">{label}</label>
                  <div className="relative">
                    <input
                      type="number"
                      value={form[key as keyof UserProfile] as number}
                      onChange={e => setForm(f => ({ ...f, [key]: Number(e.target.value) }))}
                      min={min}
                      max={max}
                      className="input-field pr-8 text-center"
                    />
                    <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-400">{unit}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 目标 */}
          <div className="card">
            <label className="block text-sm font-semibold text-gray-700 mb-3">我的目标</label>
            <div className="grid grid-cols-3 gap-2">
              {(['减脂', '增肌', '维持'] as const).map(g => (
                <button
                  key={g}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, goal: g }))}
                  className={`py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    form.goal === g ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {g}
                </button>
              ))}
            </div>
          </div>

          {/* 活动强度 */}
          <div className="card">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              今日活动强度
              <span className="text-xs font-normal text-gray-400 ml-2">影响热量计算</span>
            </label>
            <div className="grid grid-cols-3 gap-2">
              {(['低', '中', '高'] as const).map(level => (
                <button
                  key={level}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, activity_level: level }))}
                  className={`py-2.5 rounded-xl text-sm font-medium transition-colors ${
                    form.activity_level === level ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {level === '低' ? '低（久坐）' : level === '中' ? '中（日常）' : '高（运动）'}
                </button>
              ))}
            </div>
          </div>

          {/* 饮食偏好 */}
          <div className="card">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              饮食偏好
              <span className="text-xs font-normal text-gray-400 ml-2">可多选</span>
            </label>
            <div className="flex flex-wrap gap-2">
              {DIET_OPTIONS.map(opt => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => toggle('diet_prefs', opt)}
                  className={`tag py-1.5 px-3 text-sm transition-colors ${
                    form.diet_prefs.includes(opt)
                      ? 'bg-brand-100 text-brand-700 border border-brand-300'
                      : 'bg-gray-100 text-gray-600 border border-transparent'
                  }`}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? '保存中...' : '开始使用 MenuFit →'}
          </button>
        </form>
      </div>
    </div>
  );
}
