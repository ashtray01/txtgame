(() => {
  'use strict';

  const loading = document.getElementById('loading');
  const loadingText = document.getElementById('loading-text');
  const errorOverlay = document.getElementById('runtime-error');
  const errorBox = document.getElementById('error-box');
  const reloadBtn = document.getElementById('reload-btn');

  const RUNTIME_TIMEOUT = 180000;

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

  window.onCoreLoadError = function () {
    showError(
      'RUNTIME ERROR',
      'Не удалось загрузить PyScript runtime (cdn.jsdelivr.net).\n' +
      'Проверьте подключение к интернету и перезагрузите страницу.'
    );
  };

  // интерпретатор готов — но терминал ещё может не появиться, только меняем текст
  window.addEventListener('py:ready', () => {
    showLoading('Запускаю игру…');
    // страховка: если терминал уже появился, прячем загрузку
    setTimeout(() => {
      if (document.querySelector('py-terminal, .terminal')) hideLoading();
    }, 800);
  }, true);

  // прогресс загрузки runtime (worker присылает свои события через мост)
  window.addEventListener('py:progress', (e) => {
    const d = e.detail;
    if (typeof d === 'string' && d) showLoading(d);
  }, true);

  // скрываем загрузку, когда терминал появился в DOM
  const observer = new MutationObserver(() => {
    if (document.querySelector('py-terminal, .terminal')) hideLoading();
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
    if (!document.querySelector('py-terminal, .terminal')) {
      showError(
        'RUNTIME ERROR',
        'PyScript runtime не загрузился за отведённое время.\n' +
        'Возможно, CDN недоступен или соединение слишком медленное.'
      );
    }
  }, RUNTIME_TIMEOUT);

  reloadBtn.addEventListener('click', () => location.reload());

  // ---------- автопрокрутка терминала к последней строке ----------
  // В PyScript (main thread) xterm не всегда сам прокручивает viewport вниз
  // при программном выводе, поэтому последние строки (например "0. Выход")
  // остаются скрытыми. Компенсируем это: следим за изменением содержимого
  // терминала и прокручиваем его вниз, если пользователь не отмотал вверх.
  let termViewport = null;
  let termAtBottom = true;

  function bindTerminalScroll() {
    const vp = document.querySelector('.xterm-viewport');
    if (!vp || vp === termViewport) return;
    termViewport = vp;
    termAtBottom = true;
    vp.addEventListener('scroll', () => {
      termAtBottom = vp.scrollTop + vp.clientHeight >= vp.scrollHeight - 2;
    });
    const rows = document.querySelector('.xterm-rows');
    if (rows) {
      const onRowsChange = () => {
        if (termAtBottom && termViewport) {
          termViewport.scrollTop = termViewport.scrollHeight;
        }
      };
      const rowsObserver = new MutationObserver(onRowsChange);
      rowsObserver.observe(rows, { childList: true, subtree: true, characterData: true });
    }
  }

  // терминал может появиться позже — наблюдаем за появлением viewport
  const termObserver = new MutationObserver(bindTerminalScroll);
  termObserver.observe(document.body, { childList: true, subtree: true });
  bindTerminalScroll();
})();
