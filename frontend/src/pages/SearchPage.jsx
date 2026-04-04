import { useState, useRef, useCallback, useEffect } from 'react'
import { searchProducts, searchBaseline, expandSearch, getSuggestions, trackEvent, getProduct, SESSION_ID } from '../api.js'

const REASON_ICONS = {
  text_match: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
    </svg>
  ),
  popularity: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
    </svg>
  ),
  personalization: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
    </svg>
  ),
}

const REASON_COLORS = {
  text_match: 'text-gov-600 bg-gov-50 border-gov-200',
  popularity: 'text-amber-700 bg-amber-50 border-amber-200',
  personalization: 'text-purple-700 bg-purple-50 border-purple-200',
}

function ReasonBar({ reasons }) {
  if (!reasons?.length) return null

  const maxScore = Math.max(...reasons.filter(r => r.score > 0).map(r => r.score), 1)

  return (
    <div className="space-y-1.5">
      {reasons.map((r, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className={`flex items-center gap-1.5 text-xs font-medium whitespace-nowrap ${
            REASON_COLORS[r.type]?.split(' ')[0] || 'text-grayish-500'
          }`}>
            {REASON_ICONS[r.type]}
            {r.label}
          </span>
          {r.score != null && r.score > 0 && (
            <div className="flex-1 flex items-center gap-2 min-w-0">
              <div className="flex-1 h-1.5 bg-grayish-100 rounded-full overflow-hidden max-w-[120px]">
                <div
                  className={`h-full rounded-full transition-all ${
                    r.type === 'popularity' ? 'bg-amber-400' :
                    r.type === 'personalization' ? 'bg-purple-400' : 'bg-gov-400'
                  }`}
                  style={{ width: `${Math.min(100, (r.score / maxScore) * 100)}%` }}
                />
              </div>
              <span className="text-[10px] text-grayish-300 font-mono tabular-nums">{r.score}</span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function Toast({ message, visible }) {
  return (
    <div className={`toast-notification ${visible ? 'toast-visible' : 'toast-hidden'}`}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0 text-gov-300">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
      </svg>
      {message}
    </div>
  )
}

function ProductCardModal({ product, onClose, onAddToCart, onToggleFavorite, favoriteIds, userId }) {
  const [addedToCart, setAddedToCart] = useState(false)

  if (!product) return null

  const productId = product.id || product.product_id
  const isFavorited = favoriteIds ? favoriteIds.has(productId) : false

  // Parse specifications: may be a plain string "key: value\nkey: value" or an object
  const parseSpecs = (specs) => {
    if (!specs) return []
    if (typeof specs === 'object' && !Array.isArray(specs)) {
      return Object.entries(specs)
    }
    if (typeof specs === 'string') {
      return specs
        .split(/\n|;/)
        .map(line => line.trim())
        .filter(Boolean)
        .map(line => {
          const colonIdx = line.indexOf(':')
          if (colonIdx > 0) {
            return [line.slice(0, colonIdx).trim(), line.slice(colonIdx + 1).trim()]
          }
          return [line, '']
        })
    }
    return []
  }

  const specRows = parseSpecs(product.specifications)

  const handleAddToCart = () => {
    if (onAddToCart) {
      onAddToCart(product)
      setAddedToCart(true)
    }
  }

  const handleToggleFavorite = () => {
    if (onToggleFavorite) {
      onToggleFavorite(product)
    }
  }

  // Close on overlay click
  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div className="modal-overlay" onClick={handleOverlayClick} style={{ zIndex: 55 }}>
      <div className="modal-panel" style={{ maxWidth: '700px' }}>
        {/* Header */}
        <div className="flex items-start justify-between gap-4 px-7 pt-6 pb-4 border-b border-grayish-100">
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-2">
              {product.category && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-gov-50 text-gov-600 border border-gov-200">
                  {product.category}
                </span>
              )}
              {product.purchase_count > 0 && (
                <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                  </svg>
                  {product.purchase_count} закупок
                </span>
              )}
              {product.popularity_score > 0 && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-grayish-50 text-grayish-500 border border-grayish-200">
                  Популярность: {product.popularity_score}
                </span>
              )}
            </div>
            <h2 className="text-base font-semibold text-gov-800 leading-snug">
              {product.name}
            </h2>
            {product.subject && (
              <p className="mt-1.5 text-sm text-grayish-500">{product.subject}</p>
            )}
            {product.unit && (
              <p className="mt-1 text-xs text-grayish-400">
                Единица измерения: <span className="font-medium text-gov-800">{product.unit}</span>
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Закрыть"
            className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded text-grayish-400 hover:text-gov-800 hover:bg-grayish-50 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Specifications table */}
        {specRows.length > 0 && (
          <div className="px-7 py-5">
            <p className="text-[10px] text-grayish-400 uppercase tracking-wider font-semibold mb-3">
              Характеристики
            </p>
            <div className="rounded border border-grayish-100 overflow-hidden">
              <table className="w-full text-xs border-collapse">
                <tbody>
                  {specRows.map(([key, value], i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-grayish-50'}>
                      <td className="py-2 px-3 font-medium text-gov-800 w-2/5 border-r border-grayish-100 align-top leading-relaxed">
                        {key}
                      </td>
                      <td className="py-2 px-3 text-grayish-500 leading-relaxed">
                        {value || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Footer actions */}
        <div className="flex items-center justify-between gap-4 px-7 py-4 bg-grayish-50 border-t border-grayish-100 rounded-b-lg">
          {product.id && (
            <span className="text-[10px] text-grayish-400 font-mono">ID: {product.id}</span>
          )}
          <div className="flex items-center gap-3 ml-auto">
            <button
              type="button"
              onClick={onClose}
              className="gov-btn-outline px-4 py-2 text-sm"
            >
              Закрыть
            </button>
            {onToggleFavorite && (
              <button
                type="button"
                onClick={handleToggleFavorite}
                aria-label={isFavorited ? 'Убрать из избранного' : 'Добавить в избранное'}
                className="flex items-center justify-center w-9 h-9 rounded border transition-colors"
                style={{
                  borderColor: isFavorited ? '#ef4444' : '#d1d5db',
                  backgroundColor: isFavorited ? '#fef2f2' : 'transparent',
                  color: isFavorited ? '#ef4444' : '#8c96ad',
                }}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill={isFavorited ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
                  <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
              </button>
            )}
            {onAddToCart && (
              <button
                type="button"
                onClick={handleAddToCart}
                disabled={addedToCart}
                className={`gov-btn px-5 py-2 text-sm flex items-center gap-2 ${addedToCart ? 'opacity-75' : ''}`}
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
                  <line x1="3" y1="6" x2="21" y2="6"/>
                  <path d="M16 10a4 4 0 0 1-8 0"/>
                </svg>
                {addedToCart ? 'Добавлено' : 'Добавить в корзину'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function ResultCard({ item, idx, onClickItem, query, userId }) {
  const [expanded, setExpanded] = useState(false)

  const hasReasons = item.reasons?.length > 0
  const hasSpecs = item.specifications && item.specifications.length > 5

  const toggleExpand = (e) => {
    e.stopPropagation()
    setExpanded(!expanded)
  }

  return (
    <div className="gov-card hover:border-gov-300 transition-all group">
      {/* Main row — clickable to open product modal */}
      <button
        type="button"
        onClick={() => onClickItem(item, idx + 1)}
        className="cursor-pointer w-full text-left"
      >
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs text-grayish-400 font-mono">#{idx + 1}</span>
              {item.purchase_count > 0 && (
                <span className="text-[10px] text-amber-600 bg-amber-50 border border-amber-200 rounded px-1.5 py-0">
                  {item.purchase_count} закупок
                </span>
              )}
              {item.reasons?.some(r => r.type === 'personalization') && (
                <span className="text-[10px] text-purple-600 bg-purple-50 border border-purple-200 rounded px-1.5 py-0">
                  персональное
                </span>
              )}
            </div>
            <h3
              className="text-sm font-medium text-gov-800 group-hover:text-gov-500 transition-colors leading-snug"
              dangerouslySetInnerHTML={{
                __html: item.highlight?.name?.[0] || item.name
              }}
            />
            {item.category && (
              <span className="inline-block mt-2 px-2 py-0.5 bg-grayish-50 text-grayish-400 text-xs rounded border border-grayish-100">
                {item.category}
              </span>
            )}
          </div>
          <div className="flex flex-col items-end gap-1 flex-shrink-0 pt-1">
            {item.unit && (
              <span className="text-xs text-grayish-400 border border-grayish-100 rounded px-2 py-0.5">
                {item.unit}
              </span>
            )}
            <span className="text-xs text-grayish-300 font-mono">
              {item.score?.toFixed(2)}
            </span>
          </div>
        </div>
      </button>

      {/* Accordion toggle */}
      {(hasReasons || hasSpecs) && (
        <button
          onClick={toggleExpand}
          className="mt-2.5 flex items-center gap-1.5 text-xs text-grayish-400 hover:text-gov-500 transition-colors w-full"
        >
          <svg
            width="12" height="12" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2"
            className={`transition-transform ${expanded ? 'rotate-90' : ''}`}
          >
            <path d="m9 18 6-6-6-6"/>
          </svg>
          {expanded ? 'Скрыть подробности' : 'Почему этот результат выше'}
        </button>
      )}

      {/* Expanded content */}
      {expanded && (
        <div className="mt-3 pt-3 border-t border-grayish-100 space-y-3 animate-in">
          {/* Ranking reasons */}
          {hasReasons && (
            <div>
              <p className="text-[10px] text-grayish-400 uppercase tracking-wider font-semibold mb-2">
                Факторы ранжирования
              </p>
              <ReasonBar reasons={item.reasons} />
            </div>
          )}

          {/* Specifications */}
          {hasSpecs && (
            <div>
              <p className="text-[10px] text-grayish-400 uppercase tracking-wider font-semibold mb-1.5">
                Характеристики
              </p>
              <p className="text-xs text-grayish-500 leading-relaxed">
                {item.specifications}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function AiExpansionBlock({ aiLoading, aiResults, onClickItem, onSearchQuery }) {
  const [collapsed, setCollapsed] = useState(false)

  const hasResults = aiResults?.expansions?.length > 0
  const itemCount = aiResults?.items?.length || 0

  if (!aiLoading && !aiResults) return null

  return (
    <div className="sticky top-4 bg-white rounded border border-purple-200 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => hasResults && setCollapsed(!collapsed)}
        className="w-full flex items-center gap-2 px-3 py-2.5 bg-purple-50 border-b border-purple-100 text-left hover:bg-purple-100 transition-colors"
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="2.5" className="flex-shrink-0">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
        <span className="text-xs font-semibold text-purple-800 leading-tight">AI-поиск</span>

        {aiLoading && (
          <svg className="animate-spin h-3 w-3 text-purple-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
        )}

        {hasResults && !aiLoading && (
          <span className="text-[10px] text-purple-600 font-medium">{itemCount}</span>
        )}

        <div className="flex-1" />

        {hasResults && (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="2"
            className={`flex-shrink-0 transition-transform ${collapsed ? '' : 'rotate-180'}`}>
            <path d="m6 9 6 6 6-6"/>
          </svg>
        )}
      </button>

      {/* Loading */}
      {aiLoading && !aiResults && (
        <div className="px-3 py-4 text-center text-xs text-purple-500">
          Подбираю товары...
        </div>
      )}

      {/* Content */}
      {!collapsed && hasResults && (
        <div className="p-2.5">
          {/* Category chips */}
          <div className="flex flex-wrap gap-1 mb-2">
            {aiResults.expansions.map((exp, i) => (
              <button
                key={i}
                onClick={() => onSearchQuery(exp.query)}
                className="px-2 py-0.5 bg-purple-50 text-purple-700 text-[10px] font-medium rounded border border-purple-200 hover:bg-purple-100 transition-colors leading-tight"
              >
                {exp.query}
              </button>
            ))}
          </div>

          {/* Items */}
          <div className="space-y-0.5">
            {aiResults.items?.slice(0, 5).map((item, idx) => (
              <button
                type="button"
                key={`ai-${item.id || idx}`}
                onClick={() => onClickItem(item, idx + 1)}
                className="w-full text-left px-2 py-1.5 rounded hover:bg-purple-50 transition-all cursor-pointer group"
              >
                <p className="text-xs text-gov-800 group-hover:text-purple-700 transition-colors leading-snug line-clamp-2">
                  {item.name}
                </p>
                <p className="text-[10px] text-grayish-400 mt-0.5 truncate">
                  {item.found_in_category || item.category}
                </p>
              </button>
            ))}
          </div>
        </div>
      )}

      {aiResults && !hasResults && !aiLoading && (
        <div className="px-3 py-3 text-[10px] text-grayish-400 text-center italic">
          Нет дополнительных результатов
        </div>
      )}
    </div>
  )
}

const PAGE_SIZE = 20

export default function SearchPage({ userId, onAddToCart, onToggleFavorite, favoriteIds }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [activeCategory, setActiveCategory] = useState(null)
  const [offset, setOffset] = useState(0)
  const [toastVisible, setToastVisible] = useState(false)
  const [toastMsg] = useState('Ваш профиль обновлён — следующий поиск учтёт это действие')

  // AI expansion state
  const [aiResults, setAiResults] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)

  // Product card modal state
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [productLoading, setProductLoading] = useState(false)
  const [productViewStart, setProductViewStart] = useState(null)

  // Reset results when user switches organization
  const prevUserId = useRef(userId)
  useEffect(() => {
    if (prevUserId.current !== userId) {
      prevUserId.current = userId
      setResults(null)
      setAiResults(null)
      setSuggestions([])
      setActiveCategory(null)
      setOffset(0)
      // Re-run search if there's a query
      if (query.trim()) {
        // small delay to let state settle
        setTimeout(() => {
          searchProducts(query, { userId, size: PAGE_SIZE, offset: 0, sessionId: SESSION_ID })
            .then(data => setResults(data))
        }, 100)
      }
    }
  }, [userId, query])

  const suggestTimer = useRef(null)
  const toastTimer = useRef(null)

  // Show toast for 3 seconds then hide
  const showToast = useCallback(() => {
    setToastVisible(true)
    clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToastVisible(false), 3000)
  }, [])

  const doSearch = useCallback(async (q, category = null, newOffset = 0) => {
    if (!q.trim()) return

    if (newOffset === 0) {
      setLoading(true)
      setAiResults(null)
    } else {
      setLoadingMore(true)
    }
    setShowSuggestions(false)

    // Launch AI expansion in parallel (only for first page of multi-word queries)
    if (newOffset === 0 && q.trim().split(/\s+/).length >= 2) {
      setAiLoading(true)
      expandSearch(q, { userId }).then(data => {
        setAiResults(data)
      }).catch(() => {}).finally(() => setAiLoading(false))
    }

    try {
      const data = await searchProducts(q, { userId, category, size: PAGE_SIZE, offset: newOffset, sessionId: SESSION_ID })
      if (newOffset === 0) {
        setResults(data)
        setOffset(0)
      } else {
        setResults(prev => ({
          ...prev,
          items: [...(prev?.items || []), ...(data.items || [])],
        }))
        setOffset(newOffset)
      }
      setActiveCategory(category)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }, [userId])

  const handleLoadMore = () => {
    const nextOffset = offset + PAGE_SIZE
    doSearch(query, activeCategory, nextOffset)
  }

  const handleInput = (value) => {
    setQuery(value)
    clearTimeout(suggestTimer.current)
    if (value.length >= 2) {
      suggestTimer.current = setTimeout(async () => {
        const data = await getSuggestions(value, userId)
        setSuggestions(data.suggestions || [])
        setShowSuggestions(true)
      }, 200)
    } else {
      setShowSuggestions(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    doSearch(query)
  }

  const handleCategoryClick = (category) => {
    trackEvent({
      userId,
      eventType: 'category_filter',
      category: category || '',
      query,
      position: null,
      sessionId: SESSION_ID,
    })
    doSearch(query, category)
  }

  const handleProductClick = async (item, position) => {
    trackEvent({
      userId,
      eventType: 'click',
      productId: item.id,
      category: item.category,
      query,
      position,
      sessionId: SESSION_ID,
    })
    setProductLoading(true)
    setProductViewStart(Date.now())
    try {
      const product = await getProduct(item.id, userId)
      setSelectedProduct(product)
    } catch {
      // If product detail fetch fails, show item data directly
      setSelectedProduct(item)
    } finally {
      setProductLoading(false)
    }
    showToast()
  }

  const handleCloseProduct = () => {
    if (productViewStart) {
      const dwellMs = Date.now() - productViewStart
      if (dwellMs < 3000) {
        trackEvent({
          userId,
          eventType: 'quick_return',
          productId: selectedProduct?.id,
          query,
          sessionId: SESSION_ID,
        })
      }
    }
    setSelectedProduct(null)
    setProductViewStart(null)
  }

  const hasPersonalization = results?.items?.some(
    item => item.reasons?.some(r => r.type === 'personalization')
  )

  const handleShowBaseline = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const data = await searchBaseline(query, { category: activeCategory, size: PAGE_SIZE, offset: 0 })
      setResults(data)
      setOffset(0)
    } finally {
      setLoading(false)
    }
  }

  // Determine if more results could exist
  const canLoadMore = results && results.items?.length > 0 && results.items.length < results.total

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Toast notification */}
      <Toast message={toastMsg} visible={toastVisible} />

      {/* Product card modal */}
      {productLoading && (
        <div className="modal-overlay" style={{ zIndex: 55 }}>
          <div className="flex items-center gap-3 bg-white rounded-lg px-6 py-4 shadow-xl border border-grayish-100">
            <svg className="animate-spin h-5 w-5 text-gov-500" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            <span className="text-sm text-gov-800">Загрузка карточки товара...</span>
          </div>
        </div>
      )}

      {selectedProduct && (
        <ProductCardModal
          product={selectedProduct}
          onClose={handleCloseProduct}
          onAddToCart={onAddToCart}
          onToggleFavorite={onToggleFavorite}
          favoriteIds={favoriteIds}
          userId={userId}
        />
      )}

      {/* Search bar */}
      <div className="gov-card mb-6">
        <form onSubmit={handleSubmit} className="relative">
          <div className="flex">
            <div className="relative flex-1">
              <input
                type="text"
                value={query}
                onChange={e => handleInput(e.target.value)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder="Введите наименование товара, работы или услуги..."
                className="gov-input rounded-r-none border-r-0 h-12 pl-4 pr-10 text-base"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => { setQuery(''); setResults(null); setSuggestions([]) }}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-grayish-400 hover:text-grayish-700 transition-colors"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                  </svg>
                </button>
              )}
            </div>
            <button
              type="submit"
              disabled={loading}
              className="gov-btn rounded-l-none h-12 px-8 text-base rounded-r"
            >
              {loading ? (
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="mr-2">
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                  </svg>
                  Найти
                </>
              )}
            </button>
          </div>

          {/* Suggestions dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute z-20 w-full mt-1 bg-white border border-grayish-200 rounded shadow-lg overflow-hidden">
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  type="button"
                  className="w-full text-left px-4 py-2.5 text-sm text-gov-800 hover:bg-gov-50 border-b border-grayish-50 last:border-0 transition-colors flex items-center gap-2"
                  onMouseDown={() => { setQuery(s); doSearch(s) }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#8c96ad" strokeWidth="2" className="flex-shrink-0">
                    <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                  </svg>
                  {s}
                </button>
              ))}
            </div>
          )}
        </form>
      </div>

      {/* Correction notice — more prominent */}
      {results?.correction && (
        <div className="mb-4 px-4 py-3 bg-amber-50 border border-amber-300 rounded text-sm text-gov-800 flex items-center gap-3">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#d97706" strokeWidth="2" className="flex-shrink-0">
            <path d="M12 9v4M12 17h.01"/><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          </svg>
          <span>
            Возможно, вы имели в виду:{' '}
            <button
              className="text-gov-500 font-semibold hover:underline"
              onClick={() => { setQuery(results.correction); doSearch(results.correction) }}
            >
              {results.correction}
            </button>
          </span>
          {/* Synonyms badge — shown when correction was applied */}
          <span className="ml-auto inline-flex items-center gap-1 px-2 py-0.5 bg-amber-100 text-amber-700 text-[10px] font-semibold rounded border border-amber-300 whitespace-nowrap">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            Учтены синонимы
          </span>
        </div>
      )}

      {/* Layout fix notice */}
      {results?.layout_fixed && (
        <div className="mb-4 px-4 py-3 bg-gov-50 border border-gov-200 rounded text-sm text-gov-800">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="inline mr-1.5 -mt-0.5">
            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
          </svg>
          Раскладка клавиатуры исправлена автоматически
        </div>
      )}

      {/* Results layout */}
      {results && (
        <div className="flex gap-6 items-start">
          {/* Sidebar: categories */}
          {results.categories?.length > 0 && (
            <aside className="w-60 flex-shrink-0 gov-card">
              <h3 className="text-xs font-semibold text-grayish-400 uppercase tracking-wider mb-3">Категории</h3>
              <div className="space-y-0.5">
                <button
                  onClick={() => handleCategoryClick(null)}
                  className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                    !activeCategory
                      ? 'bg-gov-50 text-gov-500 font-medium border-l-[3px] border-gov-500'
                      : 'text-gov-800 hover:bg-grayish-50'
                  }`}
                >
                  Все результаты
                  <span className="text-grayish-400 ml-1 text-xs">({results.total})</span>
                </button>
                {results.categories.map(cat => (
                  <button
                    key={cat.name}
                    onClick={() => handleCategoryClick(cat.name)}
                    className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                      activeCategory === cat.name
                        ? 'bg-gov-50 text-gov-500 font-medium border-l-[3px] border-gov-500'
                        : 'text-gov-800 hover:bg-grayish-50'
                    }`}
                  >
                    {cat.name}
                    <span className="text-grayish-400 ml-1 text-xs">({cat.count})</span>
                  </button>
                ))}
              </div>
            </aside>
          )}

          {/* Main results */}
          <div className="flex-1 min-w-0">
            {/* Results header */}
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm text-grayish-400">
                Найдено результатов: <span className="font-semibold text-gov-800">{results.total}</span>
              </p>
            </div>

            {/* Personalization banner */}
            {hasPersonalization && userId !== 'anonymous' && (
              <div className="mb-4 px-4 py-2.5 bg-purple-50 border border-purple-200 rounded flex items-center gap-3 text-sm">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="2" className="flex-shrink-0">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                </svg>
                <span className="text-purple-800 flex-1">
                  Результаты персонализированы на основе вашей истории закупок.
                </span>
                <button
                  onClick={handleShowBaseline}
                  className="text-purple-600 hover:text-purple-800 font-medium underline underline-offset-2 whitespace-nowrap text-xs transition-colors"
                >
                  Показать без персонализации
                </button>
              </div>
            )}

            {/* Empty state */}
            {results.items.length === 0 && (
              <div className="gov-card text-center py-16">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#8c96ad" strokeWidth="1.5" className="mx-auto mb-4">
                  <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M8 11h6"/>
                </svg>
                <p className="text-base text-gov-800">По вашему запросу ничего не найдено</p>
                <p className="text-sm text-grayish-400 mt-1">Попробуйте изменить параметры поиска</p>
              </div>
            )}

            {/* Result cards */}
            <div className="space-y-2">
              {results.items.map((item, idx) => (
                <ResultCard
                  key={item.id || idx}
                  item={item}
                  idx={idx}
                  onClickItem={handleProductClick}
                  query={query}
                  userId={userId}
                />
              ))}
            </div>

            {/* Load more button */}
            {canLoadMore && (
              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleLoadMore}
                  disabled={loadingMore}
                  className="gov-btn-outline px-8 py-2.5 flex items-center gap-2"
                >
                  {loadingMore ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      Загрузка...
                    </>
                  ) : (
                    <>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M12 5v14M5 12l7 7 7-7"/>
                      </svg>
                      Загрузить ещё
                      <span className="text-xs text-grayish-400 ml-1">
                        ({results.items.length} из {results.total})
                      </span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* AI expansion — right sidebar */}
          {(aiLoading || aiResults) && (
            <aside className="w-72 flex-shrink-0">
              <AiExpansionBlock
                aiLoading={aiLoading}
                aiResults={aiResults}
                onClickItem={handleProductClick}
                onSearchQuery={(q) => { setQuery(q); doSearch(q) }}
              />
            </aside>
          )}
        </div>
      )}

      {/* Initial empty state */}
      {!results && !loading && (
        <div className="text-center py-20">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#8c96ad" strokeWidth="1" className="mx-auto mb-6 opacity-50">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
          <p className="text-lg text-gov-800 font-medium">Поиск по каталогу продукции</p>
          <p className="text-sm text-grayish-400 mt-2 max-w-md mx-auto">
            Введите наименование товара, работы или услуги в строку поиска.
            Система учитывает синонимы, опечатки и вашу историю закупок.
          </p>
        </div>
      )}
    </div>
  )
}
