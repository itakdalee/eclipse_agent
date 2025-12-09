/**
 * API клиент для взаимодействия с backend.
 */

// URL API сервера (относительный путь через nginx)
const API_BASE_URL = '/api';

/**
 * Отправляет сообщение в чат и получает ответ от AI.
 * @param {string} message - Сообщение пользователя
 * @param {Array<Object>} conversationHistory - История разговора
 * @returns {Promise<Object>} Ответ от сервера с полями response и is_secret_revealed
 */
export async function sendMessage(message, conversationHistory = []) {
    const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            conversation_history: conversationHistory,
        }),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

/**
 * Проверяет статус сервера.
 * @returns {Promise<Object>} Статус сервера
 */
export async function checkHealth() {
    const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET',
    });

    if (!response.ok) {
        throw new Error('Сервер недоступен');
    }

    return await response.json();
}
