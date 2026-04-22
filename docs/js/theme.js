/**
 * 主题切换功能
 */

(function() {
    'use strict';

    const STORAGE_KEY = 'tsk-theme';
    const THEME_DARK = 'dark';
    const THEME_LIGHT = 'light';
    
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle?.querySelector('.theme-icon');
    
    // 获取当前主题
    function getTheme() {
        // 优先从本地存储获取
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored === THEME_LIGHT || stored === THEME_DARK) {
            return stored;
        }
        
        // 检测系统偏好
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            return THEME_LIGHT;
        }
        
        return THEME_DARK;
    }
    
    // 设置主题
    function setTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem(STORAGE_KEY, theme);
        updateIcon(theme);
        
        // 触发主题变更事件
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
    }
    
    // 切换主题
    function toggleTheme() {
        const current = getTheme();
        const next = current === THEME_DARK ? THEME_LIGHT : THEME_DARK;
        setTheme(next);
    }
    
    // 更新图标
    function updateIcon(theme) {
        if (!themeIcon) return;
        
        if (theme === THEME_DARK) {
            themeIcon.textContent = '🌙';
            themeToggle.setAttribute('aria-label', '切换到浅色主题');
        } else {
            themeIcon.textContent = '☀️';
            themeToggle.setAttribute('aria-label', '切换到深色主题');
        }
    }
    
    // 初始化
    function init() {
        // 应用初始主题
        const theme = getTheme();
        setTheme(theme);
        
        // 绑定切换事件
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);
        }
        
        // 监听系统主题变化
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: light)');
            mediaQuery.addEventListener('change', (e) => {
                // 只在用户没有手动设置过主题时跟随系统
                if (!localStorage.getItem(STORAGE_KEY)) {
                    setTheme(e.matches ? THEME_LIGHT : THEME_DARK);
                }
            });
        }
    }
    
    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // 暴露全局 API
    window.ThemeManager = {
        get: getTheme,
        set: setTheme,
        toggle: toggleTheme
    };
})();
