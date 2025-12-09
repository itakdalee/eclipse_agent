/**
 * Модуль для работы с LocalStorage.
 * Управляет сохранением и загрузкой истории чата.
 */

const STORAGE_KEY = 'eclipse_agent_history';

/**
 * Сохраняет сообщение в историю.
 * @param {Object} message - Сообщение для сохранения
 * @param {string} message.role - Роль (user или assistant)
 * @param {string} message.content - Содержимое сообщения
 */
export function saveMessage(message) {
    const history = loadHistory();
    history.push(message);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

/**
 * Загружает историю сообщений из LocalStorage.
 * @returns {Array<Object>} Массив сообщений
 */
export function loadHistory() {
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        if (!data) {
            return [];
        }
        const history = JSON.parse(data);
        // Валидация структуры
        if (!Array.isArray(history)) {
            return [];
        }
        return history.filter(msg => 
            msg && 
            typeof msg.role === 'string' && 
            typeof msg.content === 'string'
        );
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
        return [];
    }
}

/**
 * Очищает историю сообщений.
 */
export function clearHistory() {
    localStorage.removeItem(STORAGE_KEY);
}

/**
 * Проверяет, есть ли сохранённая история.
 * @returns {boolean}
 */
export function hasHistory() {
    return loadHistory().length > 0;
}
