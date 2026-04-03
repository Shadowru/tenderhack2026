import { useState, useEffect } from 'react'
import { getLiveMetrics, getUserStats, getMetricHistory } from '../api.js'
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts'

const METRIC_CARDS = [
  { key: 'total_searches', label: 'Поисковых запросов', icon: 'search' },
  { key: 'total_clicks', label: 'Кликов по результатам', icon: 'click' },
  { key: 'total_purchases', label: 'Оформленных закупок', icon: 'cart' },
  { key: 'unique_users', label: 'Уникальных заказчиков', icon: 'users' },
]

const ICONS = {
  search: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
    </svg>
  ),
  click: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M15 15l-2 5L9 9l11 4-5 2z"/><path d="M22 22l-5-10"/>
    </svg>
  ),
  cart: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>
    </svg>
  ),
  users: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
}

const HISTORY_METRICS = [
  { key: 'ctr', label: 'CTR', color: '#0065DC', format: v => `${(v * 100).toFixed(1)}%` },
  { key: 'session_success_rate', label: 'Session Success Rate', color: '#7c3aed', format: v => `${(v * 100).toFixed(1)}%` },
  { key: 'avg_click_position', label: 'Средняя позиция', color: '#d97706', format: v => v?.toFixed(2) },
]

const METRIC_DESCRIPTIONS = [
  {
    name: 'CTR (Click-Through Rate)',
    desc: 'Доля поисковых запросов, которые привели к клику по результату. Показывает, насколько выдача релевантна запросам пользователей.',
    formula: 'клики / поисковые запросы',
    target: '> 30%',
    why: 'Прямой индикатор удовлетворённости результатами. Низкий CTR сигнализирует о нерелевантной выдаче.',
  },
  {
    name: 'MRR (Mean Reciprocal Rank)',
    desc: 'Средний обратный ранг первого релевантного результата. Показывает, как быстро пользователь находит нужный результат.',
    formula: 'mean(1 / позиция первого клика)',
    target: '> 0.5',
    why: 'Критично для поиска в госзакупках: заказчик должен найти СТЕ с первых позиций без прокрутки.',
  },
  {
    name: 'Качество ранжирования топ-10',
    desc: 'Оценивает, насколько хорошо упорядочены результаты в первой десятке: штрафует, если релевантные позиции оказались внизу списка.',
    formula: 'nDCG@10 = DCG / IDCG',
    target: '> 0.6',
    why: 'В отличие от MRR, оценивает всю выдачу целиком. Важен когда заказчик сравнивает несколько вариантов СТЕ.',
  },
  {
    name: 'Precision@K (K=5, 10, 20)',
    desc: 'Доля релевантных результатов в первых K. Простая и интерпретируемая: из 10 результатов сколько полезных?',
    formula: 'релевантных в топ-K / K',
    target: '> 40%',
    why: 'Позволяет выявить «шум» в выдаче — нерелевантные позиции, засоряющие результаты.',
  },
  {
    name: 'Средняя позиция клика',
    desc: 'Средняя позиция результата, на который кликает пользователь. Чем ближе к 1 — тем лучше ранжирование.',
    formula: 'mean(позиция при клике)',
    target: '< 3.0',
    why: 'Если заказчики систематически кликают на 5+ позицию, ранжирование неэффективно.',
  },
  {
    name: 'Zero-Result Rate',
    desc: 'Доля запросов, которые не вернули ни одного результата. Высокий показатель — пробелы в каталоге или словаре синонимов.',
    formula: 'запросов без результатов / всего',
    target: '< 5%',
    why: 'Каждый пустой ответ — потерянный заказчик. Помогает приоритизировать пополнение словаря синонимов.',
  },
  {
    name: 'Session Success Rate',
    desc: 'Доля поисковых сессий, завершившихся кликом или добавлением в закупку. Общий индикатор здоровья поиска.',
    formula: 'сессий с действием / всего сессий',
    target: '> 50%',
    why: 'Интегральная метрика: если поиск помогает заказчику найти нужное, сессия завершается действием.',
  },
  {
    name: 'Personalization Lift',
    desc: 'Насколько персонализация улучшает метрики по сравнению с обычным поиском. Ключевой показатель ценности системы.',
    formula: 'CTR_персонализ / CTR_базовый - 1',
    target: '> 10%',
    why: 'Обоснование инвестиций в персонализацию. Если lift низкий — персонализация не добавляет ценности.',
  },
]

function MetricHistoryChart({ metricKey, label, color, format }) {
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(7)

  useEffect(() => {
    setLoading(true)
    getMetricHistory(metricKey, days)
      .then(data => setHistory(data))
      .catch(() => setHistory(null))
      .finally(() => setLoading(false))
  }, [metricKey, days])

  // Normalize: API may return array of {date, value} or an object with a data key
  const chartData = Array.isArray(history)
    ? history
    : history?.data ?? history?.history ?? null

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <svg className="animate-spin h-5 w-5 text-gov-500" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      </div>
    )
  }

  if (!chartData || chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-sm text-grayish-400">
        Нет данных за выбранный период
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="inline-block w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
          <span className="text-sm font-medium text-gov-800">{label}</span>
        </div>
        <div className="flex border border-grayish-200 rounded overflow-hidden">
          {[
            { d: 3, label: '3д' },
            { d: 7, label: '7д' },
            { d: 14, label: '14д' },
          ].map(p => (
            <button
              key={p.d}
              onClick={() => setDays(p.d)}
              className={`px-2.5 py-1 text-xs font-medium transition-colors border-r border-grayish-200 last:border-r-0 ${
                days === p.d
                  ? 'bg-gov-500 text-white'
                  : 'bg-white text-grayish-500 hover:bg-grayish-50'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={chartData} margin={{ left: 0, right: 8, top: 4, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eaeaef" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 10, fill: '#8c96ad' }}
            axisLine={{ stroke: '#eaeaef' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 10, fill: '#8c96ad' }}
            axisLine={false}
            tickLine={false}
            tickFormatter={format}
            width={48}
          />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 4, border: '1px solid #eaeaef' }}
            labelStyle={{ color: '#334059', fontWeight: 600 }}
            formatter={(v) => [format(v), label]}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={{ r: 3, fill: color, strokeWidth: 0 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function MetricsPage({ userId }) {
  const [metrics, setMetrics] = useState(null)
  const [userStats, setUserStats] = useState(null)
  const [hours, setHours] = useState(24)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      getLiveMetrics(hours),
      userId !== 'anonymous' ? getUserStats(userId) : Promise.resolve(null),
    ]).then(([m, u]) => {
      setMetrics(m)
      setUserStats(u)
    }).finally(() => setLoading(false))
  }, [hours, userId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <svg className="animate-spin h-8 w-8 text-gov-500" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      </div>
    )
  }

  const chartData = userStats?.top_categories?.map(c => ({
    name: c.name?.length > 20 ? c.name.slice(0, 20) + '...' : c.name,
    score: c.score,
  })) || []

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gov-800">Аналитика и метрики качества поиска</h2>
          <p className="text-sm text-grayish-400 mt-0.5">Мониторинг поисковой системы и эффективности персонализации</p>
        </div>
        <div className="flex border border-grayish-200 rounded overflow-hidden">
          {[
            { h: 1, label: '1 час' },
            { h: 6, label: '6 часов' },
            { h: 24, label: '24 часа' },
            { h: 72, label: '3 дня' },
            { h: 168, label: '7 дней' },
          ].map(p => (
            <button
              key={p.h}
              onClick={() => setHours(p.h)}
              className={`px-3 py-1.5 text-xs font-medium transition-colors border-r border-grayish-200 last:border-r-0 ${
                hours === p.h
                  ? 'bg-gov-500 text-white'
                  : 'bg-white text-grayish-500 hover:bg-grayish-50'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      {metrics && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {METRIC_CARDS.map(card => (
            <div key={card.key} className="gov-card">
              <div className="flex items-center justify-between mb-3">
                <span className="text-grayish-400">{ICONS[card.icon]}</span>
              </div>
              <p className="text-2xl font-bold text-gov-800">
                {metrics[card.key]?.toLocaleString() ?? '—'}
              </p>
              <p className="text-xs text-grayish-400 mt-1">{card.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Key gauges */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
          <GovGauge
            label="CTR"
            value={metrics.ctr}
            format={v => `${(v * 100).toFixed(1)}%`}
            pct={metrics.ctr * 100}
            target={30}
          />
          <GovGauge
            label="Средняя позиция клика"
            value={metrics.avg_click_position}
            format={v => v != null ? v.toFixed(1) : '—'}
            pct={metrics.avg_click_position != null ? Math.max(0, 100 - (metrics.avg_click_position - 1) * 10) : 0}
            target={70}
          />
          <GovGauge
            label="Session Success Rate"
            value={metrics.session_success_rate}
            format={v => `${(v * 100).toFixed(1)}%`}
            pct={metrics.session_success_rate * 100}
            target={50}
          />
        </div>
      )}

      {/* Metric history line charts */}
      <div className="gov-card mb-6">
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gov-800">Динамика ключевых метрик</h3>
          <p className="text-xs text-grayish-400 mt-0.5">Исторические тренды основных показателей качества поиска</p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 divide-y lg:divide-y-0 lg:divide-x divide-grayish-100">
          {HISTORY_METRICS.map(m => (
            <div key={m.key} className="pt-4 lg:pt-0 first:pt-0 lg:px-4 first:pl-0 last:pr-0">
              <MetricHistoryChart
                metricKey={m.key}
                label={m.label}
                color={m.color}
                format={m.format}
              />
            </div>
          ))}
        </div>
      </div>

      {/* User profile + chart */}
      {userStats && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
          <div className="gov-card">
            <h3 className="text-sm font-semibold text-gov-800 mb-4">
              Профиль персонализации
              <span className="ml-2 px-2 py-0.5 bg-gov-50 text-gov-500 text-xs rounded">{userId}</span>
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-grayish-50">
                <span className="text-sm text-grayish-500">Всего событий</span>
                <span className="text-sm font-semibold text-gov-800">{userStats.total_events}</span>
              </div>
              {userStats.top_categories?.map((cat, i) => (
                <div key={i} className="flex items-center justify-between py-2 border-b border-grayish-50 last:border-0">
                  <span className="text-sm text-grayish-500">{cat.name}</span>
                  <span className="text-sm font-semibold text-gov-800">{cat.score.toFixed(1)}</span>
                </div>
              ))}
              {(!userStats.top_categories || userStats.top_categories.length === 0) && (
                <p className="text-sm text-grayish-400 py-4 text-center">Нет данных о категориях</p>
              )}
            </div>
          </div>

          {chartData.length > 0 && (
            <div className="gov-card">
              <h3 className="text-sm font-semibold text-gov-800 mb-4">Топ категорий по активности</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 16, top: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eaeaef" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11, fill: '#8c96ad' }} axisLine={{ stroke: '#eaeaef' }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#334059' }} width={140} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 4, border: '1px solid #eaeaef' }}
                    labelStyle={{ color: '#334059', fontWeight: 600 }}
                  />
                  <Bar dataKey="score" fill="#0065DC" radius={[0, 3, 3, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Metrics reference table */}
      <div className="gov-card">
        <h3 className="text-sm font-semibold text-gov-800 mb-1">Справочник метрик качества поиска</h3>
        <p className="text-xs text-grayish-400 mb-4">Обоснование выбора метрик для оценки и мониторинга системы</p>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-grayish-100">
                <th className="text-left py-2.5 px-3 text-xs font-semibold text-grayish-400 uppercase tracking-wider">Метрика</th>
                <th className="text-left py-2.5 px-3 text-xs font-semibold text-grayish-400 uppercase tracking-wider">Описание</th>
                <th className="text-left py-2.5 px-3 text-xs font-semibold text-grayish-400 uppercase tracking-wider w-36">Формула</th>
                <th className="text-left py-2.5 px-3 text-xs font-semibold text-grayish-400 uppercase tracking-wider w-20">Цель</th>
                <th className="text-left py-2.5 px-3 text-xs font-semibold text-grayish-400 uppercase tracking-wider">Обоснование</th>
              </tr>
            </thead>
            <tbody>
              {METRIC_DESCRIPTIONS.map((m, i) => (
                <tr key={i} className="border-b border-grayish-50 hover:bg-grayish-50 transition-colors">
                  <td className="py-3 px-3 font-medium text-gov-800 whitespace-nowrap">{m.name}</td>
                  <td className="py-3 px-3 text-grayish-500 text-xs leading-relaxed">{m.desc}</td>
                  <td className="py-3 px-3 text-xs font-mono text-grayish-400">{m.formula}</td>
                  <td className="py-3 px-3">
                    <span className="inline-block px-2 py-0.5 bg-green-50 text-green-700 text-xs rounded border border-green-200 font-medium">
                      {m.target}
                    </span>
                  </td>
                  <td className="py-3 px-3 text-grayish-500 text-xs leading-relaxed">{m.why}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function GovGauge({ label, value, format, pct, target }) {
  const displayValue = format(value)
  const isGood = pct >= target
  const isWarn = pct >= target * 0.5 && pct < target
  const barColor = isGood ? 'bg-green-500' : isWarn ? 'bg-amber-500' : 'bg-red-400'
  const textColor = isGood ? 'text-green-700' : isWarn ? 'text-amber-700' : 'text-red-600'

  return (
    <div className="gov-card">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-grayish-400 font-medium">{label}</span>
        <span className={`text-xs font-medium ${isGood ? 'text-green-600' : 'text-grayish-400'}`}>
          {isGood ? 'В норме' : 'Требует внимания'}
        </span>
      </div>
      <p className={`text-2xl font-bold ${textColor} mb-3`}>{displayValue}</p>
      <div className="h-1.5 bg-grayish-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${Math.min(100, Math.max(2, pct))}%` }}
        />
      </div>
      <div className="flex justify-end mt-1">
        <span className="text-[10px] text-grayish-300">цель: {target}%</span>
      </div>
    </div>
  )
}
