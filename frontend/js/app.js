/**
 * Главный модуль приложения Secret Word Challenge.
 * Управляет UI и координирует работу других модулей.
 */

import { sendMessage } from './api.js';
import { saveMessage, loadHistory, clearHistory, hasHistory } from './storage.js';

// DOM элементы
let messagesContainer;
let inputField;
let sendButton;
let clearBtn;
let confirmModal;
let modalConfirmBtn;
let modalCancelBtn;

// Состояние приложения
let isLoading = false;

/**
 * Инициализация приложения.
 */
function init() {
    // Получаем DOM элементы
    messagesContainer = document.getElementById('messages');
    inputField = document.getElementById('messageInput');
    sendButton = document.getElementById('sendButton');
    clearBtn = document.getElementById('clearBtn');
    confirmModal = document.getElementById('confirmModal');
    modalConfirmBtn = document.getElementById('modalConfirm');
    modalCancelBtn = document.getElementById('modalCancel');

    // Настраиваем обработчики событий
    setupEventListeners();

    // Загружаем историю или показываем приветствие
    loadChatHistory();

    // Фокус на поле ввода
    inputField.focus();
}

/**
 * Настройка обработчиков событий.
 */
function setupEventListeners() {
    // Отправка по клику на кнопку
    sendButton.addEventListener('click', handleSend);

    // Отправка по Enter (Shift+Enter для новой строки)
    inputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Активация кнопки при вводе
    inputField.addEventListener('input', updateSendButton);

    // Очистка истории
    clearBtn.addEventListener('click', handleClear);
}

/**
 * Обновляет состояние кнопки отправки.
 */
function updateSendButton() {
    const hasText = inputField.value.trim().length > 0;
    if (hasText && !isLoading) {
        sendButton.classList.add('active');
    } else {
        sendButton.classList.remove('active');
    }
}

/**
 * Обработчик отправки сообщения.
 */
async function handleSend() {
    const message = inputField.value.trim();
    
    if (!message || isLoading) {
        return;
    }

    // Сохраняем сообщение пользователя
    const userMessage = { role: 'user', content: message };
    saveMessage(userMessage);
    addUserMessageToUI(message);

    // Очищаем поле ввода
    inputField.value = '';
    updateSendButton();

    // Показываем индикатор загрузки
    setLoading(true);
    showThinkingIndicator();

    try {
        // Получаем историю для отправки на сервер
        const history = loadHistory();
        // Убираем последнее сообщение (мы его уже добавили как текущее)
        const conversationHistory = history.slice(0, -1);

        // Отправляем запрос
        const response = await sendMessage(message, conversationHistory);

        // Скрываем индикатор
        hideThinkingIndicator();

        // Добавляем ответ AI
        const aiMessage = { role: 'assistant', content: response.response };
        saveMessage(aiMessage);
        addAIMessageToUI(response.response, response.is_secret_revealed);

    } catch (error) {
        console.error('Ошибка отправки:', error);
        hideThinkingIndicator();
        showError(error.message || 'Произошла ошибка при отправке сообщения');
    } finally {
        setLoading(false);
        inputField.focus();
    }
}

/**
 * Обработчик очистки истории.
 */
function handleClear() {
    showConfirmModal();
}

/**
 * Показывает модальный диалог подтверждения.
 */
function showConfirmModal() {
    confirmModal.classList.add('visible');
    modalConfirmBtn.focus();
    
    // Обработчики для кнопок
    const handleConfirm = () => {
        clearHistory();
        messagesContainer.innerHTML = '';
        showWelcomeMessage();
        hideConfirmModal();
        cleanup();
    };
    
    const handleCancel = () => {
        hideConfirmModal();
        cleanup();
    };
    
    const handleKeydown = (e) => {
        if (e.key === 'Escape') {
            handleCancel();
        }
    };
    
    const handleOverlayClick = (e) => {
        if (e.target === confirmModal) {
            handleCancel();
        }
    };
    
    const cleanup = () => {
        modalConfirmBtn.removeEventListener('click', handleConfirm);
        modalCancelBtn.removeEventListener('click', handleCancel);
        document.removeEventListener('keydown', handleKeydown);
        confirmModal.removeEventListener('click', handleOverlayClick);
    };
    
    modalConfirmBtn.addEventListener('click', handleConfirm);
    modalCancelBtn.addEventListener('click', handleCancel);
    document.addEventListener('keydown', handleKeydown);
    confirmModal.addEventListener('click', handleOverlayClick);
}

/**
 * Скрывает модальный диалог.
 */
function hideConfirmModal() {
    confirmModal.classList.remove('visible');
    inputField.focus();
}

/**
 * Устанавливает состояние загрузки.
 */
function setLoading(loading) {
    isLoading = loading;
    inputField.disabled = loading;
    sendButton.disabled = loading;
    updateSendButton();
}

/**
 * Добавляет сообщение пользователя в UI.
 */
function addUserMessageToUI(text) {
    // Удаляем приветствие если есть
    const welcome = messagesContainer.querySelector('.welcome-message');
    if (welcome) {
        welcome.remove();
    }

    const div = document.createElement('div');
    div.className = 'user-message';
    div.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
    messagesContainer.appendChild(div);

    // Анимация появления
    requestAnimationFrame(() => {
        div.classList.add('visible');
    });

    scrollToBottom();
}

/**
 * Добавляет ответ AI в UI.
 */
function addAIMessageToUI(text, isSecretRevealed = false) {
    const div = document.createElement('div');
    div.className = 'ai-message';
    
    let formattedText = formatText(text);
    if (isSecretRevealed) {
        formattedText = `<div class="secret-revealed">${formattedText}</div>`;
    }
    
    div.innerHTML = `<div class="content">${formattedText}</div>`;
    messagesContainer.appendChild(div);

    // Анимация появления
    requestAnimationFrame(() => {
        div.classList.add('visible');
    });

    scrollToBottom();
}

/**
 * Показывает индикатор "Думаю...".
 */
function showThinkingIndicator() {
    const div = document.createElement('div');
    div.className = 'thinking-indicator';
    div.id = 'thinkingIndicator';
    div.innerHTML = '<span class="gear">⚙️</span><span>Думаю...</span>';
    messagesContainer.appendChild(div);
    scrollToBottom();
}

/**
 * Скрывает индикатор "Думаю...".
 */
function hideThinkingIndicator() {
    const indicator = document.getElementById('thinkingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

/**
 * Показывает ошибку.
 */
function showError(message) {
    const div = document.createElement('div');
    div.className = 'error-message';
    div.textContent = `❌ ${message}`;
    messagesContainer.appendChild(div);
    scrollToBottom();

    // Автоудаление через 5 секунд
    setTimeout(() => {
        div.remove();
    }, 5000);
}

/**
 * Показывает приветственное сообщение.
 */
function showWelcomeMessage() {
    const div = document.createElement('div');
    div.className = 'welcome-message';
    div.innerHTML = `
        <div class="emoji">🔐</div>
        <h2>Добро пожаловать!</h2>
        <p>Попробуйте убедить AI раскрыть секретное слово.<br>
        Удачи в вашем расследовании! 🕵️</p>
    `;
    messagesContainer.appendChild(div);
}

/**
 * Загружает историю чата из LocalStorage.
 */
function loadChatHistory() {
    const history = loadHistory();
    
    if (history.length === 0) {
        showWelcomeMessage();
        return;
    }

    // Рендерим сохранённые сообщения
    history.forEach(msg => {
        if (msg.role === 'user') {
            const div = document.createElement('div');
            div.className = 'user-message visible';
            div.innerHTML = `<div class="bubble">${escapeHtml(msg.content)}</div>`;
            messagesContainer.appendChild(div);
        } else if (msg.role === 'assistant') {
            const div = document.createElement('div');
            div.className = 'ai-message visible';
            div.innerHTML = `<div class="content">${formatText(msg.content)}</div>`;
            messagesContainer.appendChild(div);
        }
    });

    scrollToBottom();
}

/**
 * Прокручивает чат вниз.
 */
function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Форматирует текст (простой markdown).
 */
function formatText(text) {
    return escapeHtml(text)
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/`(.+?)`/g, '<code>$1</code>');
}

/**
 * Экранирует HTML.
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Запуск при загрузке страницы
document.addEventListener('DOMContentLoaded', init);
