import { useState, useEffect } from 'react'
import SearchPage from './pages/SearchPage.jsx'
import MetricsPage from './pages/MetricsPage.jsx'
import { getCart, addToCart, removeFromCart, clearCart, getFavorites, addFavorite, removeFavorite, clearFavorites } from './api.js'

const TABS = [
  { id: 'search', label: 'Поиск продукции' },
  { id: 'metrics', label: 'Аналитика и метрики' },
]

const DEMO_USERS = [
  { inn: '7734091519', name: 'ГБУ Здравоохранения — Больница', type: 'Медицина', icon: '🏥' },
  { inn: '7716237684', name: 'ГБ ПОУ — Колледж', type: 'Образование', icon: '🎓' },
  { inn: '7717038138', name: 'ГБУ Культуры — Библиотека', type: 'Культура', icon: '📚' },
  { inn: '5003021368', name: 'ГБ ОУ — Школа', type: 'Образование', icon: '🏫' },
  { inn: '7727656790', name: 'ГБУ — Центр соцобслуживания', type: 'Соцзащита', icon: '🤝' },
  { inn: '7714644959', name: 'ГБУ — Многопрофильный центр', type: 'Медицина', icon: '⚕️' },
  { inn: '7704022941', name: 'ГБУ Культуры и досуга', type: 'Культура', icon: '🎭' },
  { inn: '7705513734', name: 'ГБ ПОУ — Техникум', type: 'Образование', icon: '🔧' },
  { inn: '5902290473', name: 'ГБУ ЗО — Пермская больница', type: 'Медицина', icon: '🏥' },
  { inn: '7704054943', name: 'ГБУ ЗО — Лаборатория', type: 'Медицина', icon: '🔬' },
]

const STORAGE_KEY = 'tenderhack_selected_user_inn'

const TYPE_COLORS = {
  'Медицина':    'bg-red-50 text-red-700 border-red-200',
  'Образование': 'bg-blue-50 text-blue-700 border-blue-200',
  'Культура':    'bg-purple-50 text-purple-700 border-purple-200',
  'Соцзащита':   'bg-green-50 text-green-700 border-green-200',
}

function UserSelectorModal({ onSelect }) {
  return (
    <div className="modal-overlay">
      <div className="modal-panel">
        {/* Modal header */}
        <div className="px-8 pt-8 pb-6 border-b border-grayish-100">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded bg-gov-500 flex items-center justify-center flex-shrink-0">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gov-800">Выберите организацию</h2>
              <p className="text-sm text-grayish-400">
                Система персонализирует результаты поиска на основе истории закупок вашей организации
              </p>
            </div>
          </div>
        </div>

        {/* User grid */}
        <div className="p-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {DEMO_USERS.map(user => (
              <button
                key={user.inn}
                onClick={() => onSelect(user)}
                className="user-card text-left flex items-start gap-3 p-4 rounded border border-grayish-100 bg-white hover:border-gov-400 hover:bg-gov-50 transition-all group"
              >
                <span className="text-2xl leading-none mt-0.5 flex-shrink-0">{user.icon}</span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gov-800 group-hover:text-gov-500 transition-colors leading-snug mb-1">
                    {user.name}
                  </p>
                  <div className="flex items-center gap-2">
                    <span className={`inline-block px-1.5 py-0 text-[10px] font-medium rounded border ${TYPE_COLORS[user.type] || 'bg-grayish-50 text-grayish-500 border-grayish-200'}`}>
                      {user.type}
                    </span>
                    <span className="text-[10px] text-grayish-400 font-mono">ИНН {user.inn}</span>
                  </div>
                </div>
                <svg
                  width="16" height="16" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2"
                  className="flex-shrink-0 text-grayish-200 group-hover:text-gov-400 transition-colors mt-1"
                >
                  <path d="m9 18 6-6-6-6"/>
                </svg>
              </button>
            ))}
          </div>
        </div>

        <div className="px-8 pb-6 text-center">
          <p className="text-xs text-grayish-400">
            Это демонстрационный режим. Данные организаций взяты из открытых реестров госзакупок.
          </p>
        </div>
      </div>
    </div>
  )
}

function CartPanel({ items, onRemove, onClear, onClose }) {
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/20"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Slide-out panel */}
      <div className="cart-panel" role="dialog" aria-label="Корзина">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-grayish-100 sticky top-0 bg-white z-10">
          <div className="flex items-center gap-2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#334059" strokeWidth="2">
              <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
              <line x1="3" y1="6" x2="21" y2="6"/>
              <path d="M16 10a4 4 0 0 1-8 0"/>
            </svg>
            <h2 className="text-sm font-semibold text-gov-800">Корзина</h2>
            {items.length > 0 && (
              <span className="cart-badge">{items.length}</span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Закрыть корзину"
            className="w-8 h-8 flex items-center justify-center rounded text-grayish-400 hover:text-gov-800 hover:bg-grayish-50 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Items */}
        <div className="flex-1 px-4 py-3">
          {items.length === 0 ? (
            <div className="py-16 text-center">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#8c96ad" strokeWidth="1.5" className="mx-auto mb-3 opacity-50">
                <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
                <line x1="3" y1="6" x2="21" y2="6"/>
                <path d="M16 10a4 4 0 0 1-8 0"/>
              </svg>
              <p className="text-sm text-grayish-400">Корзина пуста</p>
              <p className="text-xs text-grayish-300 mt-1">Добавьте товары из результатов поиска</p>
            </div>
          ) : (
            <div className="space-y-1">
              {items.map((item, i) => (
                <div
                  key={item.product_id || item.id || i}
                  className="flex items-start gap-3 py-3 border-b border-grayish-50 last:border-0"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gov-800 leading-snug line-clamp-2">
                      {item.product_name || item.name || item.product_id}
                    </p>
                    {item.category && (
                      <p className="text-[11px] text-grayish-400 mt-0.5">{item.category}</p>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => onRemove(item.product_id || item.id)}
                    aria-label="Удалить из корзины"
                    className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded text-grayish-300 hover:text-red-500 hover:bg-red-50 transition-colors mt-0.5"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="px-4 py-4 border-t border-grayish-100 sticky bottom-0 bg-white">
            <button
              type="button"
              onClick={onClear}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-600 border border-red-200 rounded hover:bg-red-50 transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
              </svg>
              Очистить корзину
            </button>
          </div>
        )}
      </div>
    </>
  )
}

function FavoritesPanel({ items, onRemove, onClear, onClose }) {
  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/20"
        onClick={onClose}
        aria-hidden="true"
      />
      {/* Slide-out panel */}
      <div className="cart-panel" role="dialog" aria-label="Избранное">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-grayish-100 sticky top-0 bg-white z-10">
          <div className="flex items-center gap-2">
            <svg width="18" height="18" viewBox="0 0 24 24" fill={items.length > 0 ? '#ef4444' : 'none'} stroke={items.length > 0 ? '#ef4444' : '#334059'} strokeWidth="2">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            <h2 className="text-sm font-semibold text-gov-800">Избранное</h2>
            {items.length > 0 && (
              <span className="cart-badge" style={{ backgroundColor: '#ef4444' }}>{items.length}</span>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Закрыть избранное"
            className="w-8 h-8 flex items-center justify-center rounded text-grayish-400 hover:text-gov-800 hover:bg-grayish-50 transition-colors"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        {/* Items */}
        <div className="flex-1 px-4 py-3">
          {items.length === 0 ? (
            <div className="py-16 text-center">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#8c96ad" strokeWidth="1.5" className="mx-auto mb-3 opacity-50">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              <p className="text-sm text-grayish-400">Избранное пусто</p>
              <p className="text-xs text-grayish-300 mt-1">Сохраняйте товары, нажимая на сердечко в карточке</p>
            </div>
          ) : (
            <div className="space-y-1">
              {items.map((item, i) => (
                <div
                  key={item.product_id || i}
                  className="flex items-start gap-3 py-3 border-b border-grayish-50 last:border-0"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gov-800 leading-snug line-clamp-2">
                      {item.product_name || item.product_id}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => onRemove(item.product_id)}
                    aria-label="Убрать из избранного"
                    className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded text-red-300 hover:text-red-500 hover:bg-red-50 transition-colors mt-0.5"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
                      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {items.length > 0 && (
          <div className="px-4 py-4 border-t border-grayish-100 sticky bottom-0 bg-white">
            <button
              type="button"
              onClick={onClear}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm text-red-600 border border-red-200 rounded hover:bg-red-50 transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              Очистить избранное
            </button>
          </div>
        )}
      </div>
    </>
  )
}

export default function App() {
  const [tab, setTab] = useState('search')
  const [selectedUser, setSelectedUser] = useState(null)
  const [showModal, setShowModal] = useState(false)

  // Cart state
  const [cartItems, setCartItems] = useState([])
  const [showCart, setShowCart] = useState(false)

  // Favorites state
  const [favoriteItems, setFavoriteItems] = useState([])
  const [showFavorites, setShowFavorites] = useState(false)

  // Restore from localStorage on first render
  useEffect(() => {
    const savedInn = localStorage.getItem(STORAGE_KEY)
    if (savedInn) {
      const found = DEMO_USERS.find(u => u.inn === savedInn)
      if (found) {
        setSelectedUser(found)
        return
      }
    }
    setShowModal(true)
  }, [])

  const userId = selectedUser?.inn ?? 'anonymous'

  // Load cart when userId changes
  useEffect(() => {
    if (userId !== 'anonymous') {
      getCart(userId)
        .then(data => setCartItems(data.items || []))
        .catch(() => setCartItems([]))
    } else {
      setCartItems([])
    }
  }, [userId])

  // Load favorites when userId changes
  useEffect(() => {
    if (userId !== 'anonymous') {
      getFavorites(userId)
        .then(data => setFavoriteItems(data.items || []))
        .catch(() => setFavoriteItems([]))
    } else {
      setFavoriteItems([])
    }
  }, [userId])

  const handleSelectUser = (user) => {
    // Clear previous user's cart/favorites from UI
    setCartItems([])
    setFavoriteItems([])
    setSelectedUser(user)
    localStorage.setItem(STORAGE_KEY, user.inn)
    setShowModal(false)
  }

  const refreshCart = async () => {
    try {
      const data = await getCart(userId)
      setCartItems(data.items || [])
    } catch { /* ignore */ }
  }

  const refreshFavorites = async () => {
    try {
      const data = await getFavorites(userId)
      setFavoriteItems(data.items || [])
    } catch { /* ignore */ }
  }

  const handleAddToCart = async (product) => {
    const productId = product.id || product.product_id
    const productName = product.name || product.product_name || ''
    const category = product.category || ''
    try {
      await addToCart(userId, productId, productName, category)
      await refreshCart()
      setShowCart(true)
    } catch {
      // Optimistic update on failure
      setCartItems(prev => [...prev, { product_id: productId, product_name: productName, quantity: 1 }])
      setShowCart(true)
    }
  }

  const handleRemoveFromCart = async (productId) => {
    try {
      await removeFromCart(userId, productId)
      await refreshCart()
    } catch {
      setCartItems(prev => prev.filter(i => i.product_id !== productId))
    }
  }

  const handleClearCart = async () => {
    try {
      await clearCart(userId)
    } catch {
      // ignore
    }
    setCartItems([])
  }

  const handleToggleFavorite = async (product) => {
    const productId = product.id || product.product_id
    const productName = product.name || product.product_name || ''
    const category = product.category || ''
    const isFav = favoriteItems.some(f => f.product_id === productId)
    try {
      if (isFav) {
        await removeFavorite(userId, productId)
      } else {
        await addFavorite(userId, productId, productName, category)
      }
      await refreshFavorites()
    } catch {
      // Optimistic update on failure
      if (isFav) {
        setFavoriteItems(prev => prev.filter(f => f.product_id !== productId))
      } else {
        setFavoriteItems(prev => [...prev, { product_id: productId, product_name: productName }])
      }
    }
  }

  const handleRemoveFromFavorites = async (productId) => {
    try {
      await removeFavorite(userId, productId)
      await refreshFavorites()
    } catch {
      setFavoriteItems(prev => prev.filter(f => f.product_id !== productId))
    }
  }

  const handleClearFavorites = async () => {
    try {
      await clearFavorites(userId)
    } catch {
      // ignore
    }
    setFavoriteItems([])
  }

  const cartCount = cartItems.length
  const favCount = favoriteItems.length
  const favoriteIds = new Set(favoriteItems.map(f => f.product_id))

  return (
    <div className="min-h-screen flex flex-col bg-grayish-50">
      {/* User selector modal */}
      {showModal && <UserSelectorModal onSelect={handleSelectUser} />}

      {/* Cart panel */}
      {showCart && (
        <CartPanel
          items={cartItems}
          onRemove={handleRemoveFromCart}
          onClear={handleClearCart}
          onClose={() => setShowCart(false)}
        />
      )}

      {/* Favorites panel */}
      {showFavorites && (
        <FavoritesPanel
          items={favoriteItems}
          onRemove={handleRemoveFromFavorites}
          onClear={handleClearFavorites}
          onClose={() => setShowFavorites(false)}
        />
      )}

      {/* Top bar */}
      <div className="bg-gov-800 text-white text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-8">
          <span className="text-grayish-300">Единая информационная система в сфере закупок</span>
          <div className="flex items-center gap-3">
            {selectedUser ? (
              <>
                <span className="text-grayish-300">
                  {selectedUser.icon} {selectedUser.name}
                </span>
                <span className="text-grayish-500">·</span>
                <span className="font-mono text-grayish-400">ИНН {selectedUser.inn}</span>
                <button
                  onClick={() => setShowModal(true)}
                  className="text-gov-300 hover:text-white transition-colors underline underline-offset-2"
                >
                  сменить
                </button>
              </>
            ) : (
              <button
                onClick={() => setShowModal(true)}
                className="text-gov-300 hover:text-white transition-colors underline underline-offset-2"
              >
                Выбрать организацию
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main header */}
      <header className="bg-white border-b border-grayish-100 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16 gap-6">
            {/* Logo */}
            <div className="flex items-center gap-3 flex-shrink-0">
              <svg width="36" height="36" viewBox="0 0 36 36" fill="none" className="flex-shrink-0">
                <rect width="36" height="36" rx="4" fill="#0065DC"/>
                <path d="M8 18h6v-6h4v6h6v4h-6v6h-4v-6H8v-4z" fill="white"/>
              </svg>
              <div>
                <div className="text-base font-semibold text-gov-800 leading-tight">Портал поставщиков</div>
                <div className="text-xs text-grayish-400 leading-tight">Умный поиск продукции</div>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex items-center h-full ml-4">
              {TABS.map(t => (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className={`relative h-full px-5 text-sm font-medium transition-colors ${
                    tab === t.id
                      ? 'text-gov-500'
                      : 'text-grayish-400 hover:text-gov-800'
                  }`}
                >
                  {t.label}
                  {tab === t.id && (
                    <span className="absolute bottom-0 left-0 right-0 h-[3px] bg-gov-500 rounded-t" />
                  )}
                </button>
              ))}
            </nav>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Favorites icon button */}
            <button
              type="button"
              onClick={() => {
                setShowFavorites(prev => !prev)
                setShowCart(false)
              }}
              aria-label={`Избранное, ${favCount} товаров`}
              className="relative flex items-center justify-center w-10 h-10 rounded transition-colors"
              style={{ color: favCount > 0 ? '#ef4444' : '#8c96ad' }}
              onMouseEnter={e => { if (favCount === 0) e.currentTarget.style.color = '#334059' }}
              onMouseLeave={e => { if (favCount === 0) e.currentTarget.style.color = '#8c96ad' }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill={favCount > 0 ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="1.75">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              {favCount > 0 && (
                <span className="cart-badge absolute -top-1 -right-1" style={{ backgroundColor: '#ef4444' }}>
                  {favCount > 99 ? '99+' : favCount}
                </span>
              )}
            </button>

            {/* Cart icon button */}
            <button
              type="button"
              onClick={() => {
                setShowCart(prev => !prev)
                setShowFavorites(false)
              }}
              aria-label={`Корзина, ${cartCount} товаров`}
              className="relative flex items-center justify-center w-10 h-10 rounded text-grayish-400 hover:text-gov-800 hover:bg-grayish-50 transition-colors"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                <path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/>
                <line x1="3" y1="6" x2="21" y2="6"/>
                <path d="M16 10a4 4 0 0 1-8 0"/>
              </svg>
              {cartCount > 0 && (
                <span className="cart-badge absolute -top-1 -right-1">
                  {cartCount > 99 ? '99+' : cartCount}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1">
        {tab === 'search' && (
          <SearchPage
            userId={userId}
            onAddToCart={userId !== 'anonymous' ? handleAddToCart : null}
            onToggleFavorite={userId !== 'anonymous' ? handleToggleFavorite : null}
            favoriteIds={favoriteIds}
          />
        )}
        {tab === 'metrics' && <MetricsPage userId={userId} />}
      </main>

      {/* Footer */}
      <footer className="bg-gov-800 text-grayish-300 text-xs py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
          <span>Портал поставщиков — zakupki.mos.ru</span>
          <span>TenderHack 2026</span>
        </div>
      </footer>
    </div>
  )
}
