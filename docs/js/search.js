/**
 * 搜索功能
 */

(function() {
    'use strict';

    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    
    let searchIndex = [];
    let selectedIndex = -1;
    
    // 加载搜索索引
    async function loadSearchIndex() {
        try {
            const response = await fetch('/the-book-of-secret-knowledge-zh/search-index.json');
            if (!response.ok) {
                // 尝试相对路径
                const response2 = await fetch('search-index.json');
                searchIndex = await response2.json();
                return;
            }
            searchIndex = await response.json();
        } catch (error) {
            console.warn('无法加载搜索索引:', error);
        }
    }
    
    // 执行搜索
    function performSearch(query) {
        if (!query.trim() || searchIndex.length === 0) {
            searchResults.classList.remove('active');
            return;
        }
        
        const normalizedQuery = query.toLowerCase().trim();
        const results = searchIndex
            .filter(item => {
                const title = (item.title || '').toLowerCase();
                const category = (item.category || '').toLowerCase();
                return title.includes(normalizedQuery) || 
                       category.includes(normalizedQuery);
            })
            .slice(0, 10);
        
        renderResults(results, query);
    }
    
    // 渲染搜索结果
    function renderResults(results, query) {
        searchResults.innerHTML = '';
        selectedIndex = -1;
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-result-empty">未找到匹配的结果</div>';
            searchResults.classList.add('active');
            return;
        }
        
        results.forEach((item, index) => {
            const div = document.createElement('a');
            div.className = 'search-result-item';
            div.href = getItemUrl(item);
            div.innerHTML = `
                <div class="search-result-title">${highlightText(item.title, query)}</div>
                <div class="search-result-category">${item.category || '文档'}</div>
            `;
            div.dataset.index = index;
            
            div.addEventListener('click', () => {
                searchResults.classList.remove('active');
            });
            
            searchResults.appendChild(div);
        });
        
        searchResults.classList.add('active');
    }
    
    // 获取项目 URL
    function getItemUrl(item) {
        const basePath = '/the-book-of-secret-knowledge-zh';
        
        if (item.url && item.url.startsWith('http')) {
            return item.url;
        }
        
        if (item.path) {
            return `${basePath}${item.path}`;
        }
        
        return `${basePath}/`;
    }
    
    // 高亮匹配文本
    function highlightText(text, query) {
        const regex = new RegExp(`(${escapeRegex(query)})`, 'gi');
        return text.replace(regex, '<mark style="background:rgba(233,69,96,0.3);color:inherit;padding:0 2px;border-radius:2px;">$1</mark>');
    }
    
    // 转义正则特殊字符
    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    // 键盘导航
    function handleKeyNavigation(e) {
        const items = searchResults.querySelectorAll('.search-result-item');
        
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedIndex = Math.min(selectedIndex + 1, items.length - 1);
            updateSelection(items);
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedIndex = Math.max(selectedIndex - 1, -1);
            updateSelection(items);
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedIndex >= 0 && items[selectedIndex]) {
                items[selectedIndex].click();
            } else if (items.length > 0) {
                items[0].click();
            }
        } else if (e.key === 'Escape') {
            searchResults.classList.remove('active');
            searchInput.blur();
        }
    }
    
    // 更新选中状态
    function updateSelection(items) {
        items.forEach((item, index) => {
            if (index === selectedIndex) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest' });
            } else {
                item.classList.remove('selected');
            }
        });
    }
    
    // 全局快捷键
    function handleGlobalShortcut(e) {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
            searchInput.select();
        }
    }
    
    // 初始化
    function init() {
        if (!searchInput || !searchResults) return;
        
        loadSearchIndex();
        
        // 输入事件
        let debounceTimer;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                performSearch(e.target.value);
            }, 150);
        });
        
        // 键盘导航
        searchInput.addEventListener('keydown', handleKeyNavigation);
        
        // 全局快捷键
        document.addEventListener('keydown', handleGlobalShortcut);
        
        // 点击外部关闭
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.remove('active');
            }
        });
        
        // 获得焦点时如果有内容则显示结果
        searchInput.addEventListener('focus', () => {
            if (searchInput.value.trim()) {
                performSearch(searchInput.value);
            }
        });
    }
    
    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
