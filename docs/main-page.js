(() => {
  'use strict';

  const loading = document.getElementById('loading');
  const loadingText = document.getElementById('loading-text');
  const errorOverlay = document.getElementById('runtime-error');
  const errorBox = document.getElementById('error-box');
  const reloadBtn = document.getElementById('reload-btn');

  const RUNTIME_TIMEOUT = 90000;

  function showError(title, detail) {
    if (!errorOverlay.classList.contains('hidden')) return;
    errorBox.textContent = title + (detail ? '\n\n' + detail : '');
    errorOverlay.classList.remove('hidden');
    loading.classList.add('hidden');
  }

  function showLoading(text) {
    if (text) loadingText.textContent = text;
  }

  function hideLoading() {
    if (!loading.classList.contains('hidden')) loading.classList.add('hidden');
  }

  // Попытка fallback на локальную копию PyScript, если CDN недоступен.
  (function(){
    let triedLocal = false;
    window.onCoreLoadError = function () {
      if (!triedLocal) {
        triedLocal = true;
        // пытаемся загрузить локальную копию: ./vendor/pyscript/core.js
        const s = document.createElement('script');
        s.type = 'module';
        s.src = './vendor/pyscript/core.js';
        s.onload = () => {
          showLoading('Загружен локальный PyScript, запускаю...');
        };
        s.onerror = () => {
          showError(
            'RUNTIME ERROR',
            'Не удалось загрузить PyScript runtime (CDN и локальная копия недоступны).\n' +
            'Скачайте core.js в ./docs/vendor/pyscript/ или включите доступ к CDN и перезагрузите страницу.'
          );
        };
        document.head.appendChild(s);
        return;
      }
      showError(
        'RUNTIME ERROR',
        'Не удалось загрузить PyScript runtime с CDN (pyscript.net).\n' +
        'Проверьте подключение к интернету и перезагрузите страницу.'
      );
    };
  })();

  // интерпретатор готов — но терминал ещё может не появиться, только меняем текст
  window.addEventListener('py:ready', () => {
    showLoading('Запускаю игру…');
    // страховка: если терминал уже появился, прячем загрузку
    setTimeout(() => {
      if (document.querySelector('.py-terminal')) hideLoading();
    }, 800);
  }, true);

  // прогресс загрузки runtime (worker присылает свои события через мост)
  window.addEventListener('py:progress', (e) => {
    const d = e.detail;
    if (typeof d === 'string' && d) showLoading(d);
  }, true);

  // скрываем загрузку, когда терминал появился в DOM
  const observer = new MutationObserver(() => {
    if (document.querySelector('.py-terminal')) hideLoading();
  });
  observer.observe(document.body, { childList: true, subtree: true });

  // ошибки выполнения Python-скрипта
  window.addEventListener('py:error', (e) => {
    const detail = e.detail;
    const msg = (detail && (detail.message || detail.formatted || String(detail))) || 'неизвестная ошибка';
    showError('RUNTIME ERROR', msg);
  }, true);

  // watchdog: терминал не появился за время — показываем ошибку соединения
  setTimeout(() => {
    if (!document.querySelector('.py-terminal')) {
      showError(
        'RUNTIME ERROR',
        'PyScript runtime не загрузился за отведённое время.\n' +
        'Возможно, CDN недоступен или соединение слишком медленное.'
      );
    }
  }, RUNTIME_TIMEOUT);

  reloadBtn.addEventListener('click', () => location.reload());
})();
