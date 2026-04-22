/**
 * 导航交互功能
 */

(function() {
    'use strict';

    // DOM 元素
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebarLeft = document.querySelector('.sidebar-left');
    const backToTop = document.getElementById('back-to-top');
    
    // 创建遮罩层
    let overlay = document.querySelector('.overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'overlay';
        document.body.appendChild(overlay);
    }
    
    // 侧边栏状态
    let sidebarOpen = false;
    
    // 打开侧边栏
    function openSidebar() {
        sidebarLeft?.classList.add('open');
        overlay?.classList.add('active');
        sidebarOpen = true;
        document.body.style.overflow = 'hidden';
    }
    
    // 关闭侧边栏
    function closeSidebar() {
        sidebarLeft?.classList.remove('open');
        overlay?.classList.remove('active');
        sidebarOpen = false;
        document.body.style.overflow = '';
    }
    
    // 切换侧边栏
    function toggleSidebar() {
        if (sidebarOpen) {
            closeSidebar();
        } else {
            openSidebar();
        }
    }
    
    // 回到顶部
    function scrollToTop() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    }
    
    // 更新回到顶部按钮显示状态
    function updateBackToTop() {
        if (!backToTop) return;
        
        if (window.scrollY > 300) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    }
    
    // 高亮当前页面导航
    function highlightCurrentNav() {
        const currentPath = window.location.pathname;
        const tocItems = document.querySelectorAll('.toc-item');
        
        tocItems.forEach(item => {
            item.classList.remove('active');
            
            const href = item.getAttribute('href');
            if (href) {
                // 提取路径部分进行比较
                const itemPath = href.replace('/the-book-of-secret-knowledge-zh/', '').replace(/\/$/, '');
                const current = currentPath.replace('/the-book-of-secret-knowledge-zh/', '').replace(/\/$/, '');
                
                if (itemPath === current || (current === '' && itemPath === '')) {
                    item.classList.add('active');
                }
            }
        });
    }
    
    // 更新大纲高亮
    function updateOutlineHighlight() {
        const outlineLinks = document.querySelectorAll('.page-outline a');
        if (outlineLinks.length === 0) return;
        
        const headings = document.querySelectorAll('.markdown-body h2[id], .markdown-body h3[id]');
        
        // 找到当前可见的标题
        let currentHeading = null;
        const scrollY = window.scrollY + 100; // 偏移量
        
        headings.forEach(heading => {
            if (heading.offsetTop <= scrollY) {
                currentHeading = heading;
            }
        });
        
        // 更新大纲高亮
        outlineLinks.forEach(link => {
            link.classList.remove('active');
            if (currentHeading) {
                const href = link.getAttribute('href');
                if (href === `#${currentHeading.id}`) {
                    link.classList.add('active');
                }
            }
        });
    }
    
    // 平滑滚动到锚点
    function smoothScrollToAnchor(e) {
        const target = e.target.closest('a');
        if (!target) return;
        
        const href = target.getAttribute('href');
        if (!href || !href.startsWith('#')) return;
        
        const targetId = href.slice(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            e.preventDefault();
            
            // 计算偏移量，考虑固定头部
            const offset = 100;
            const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - offset;
            
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
            
            // 更新 URL
            history.pushState(null, '', href);
        }
    }
    
    // 点击大纲链接
    function handleOutlineClick(e) {
        const target = e.target.closest('a');
        if (!target || !target.closest('.page-outline')) return;
        smoothScrollToAnchor(e);
    }
    
    // 点击内容中的锚点链接
    function handleContentClick(e) {
        const target = e.target.closest('a');
        if (!target || !target.closest('.markdown-body')) return;
        
        const href = target.getAttribute('href');
        // 只处理页内锚点，不是外部链接
        if (href && href.startsWith('#')) {
            smoothScrollToAnchor(e);
        }
    }
    
    // 窗口大小改变时
    function handleResize() {
        if (window.innerWidth > 900 && sidebarOpen) {
            closeSidebar();
        }
    }
    
    // 初始化
    function init() {
        // 菜单切换
        if (menuToggle) {
            menuToggle.addEventListener('click', toggleSidebar);
        }
        
        // 遮罩层点击
        if (overlay) {
            overlay.addEventListener('click', closeSidebar);
        }
        
        // 回到顶部
        if (backToTop) {
            backToTop.addEventListener('click', scrollToTop);
        }
        
        // 滚动事件
        let ticking = false;
        window.addEventListener('scroll', () => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    updateBackToTop();
                    updateOutlineHighlight();
                    ticking = false;
                });
                ticking = true;
            }
        }, { passive: true });
        
        // 大纲点击
        document.addEventListener('click', handleOutlineClick);
        
        // 内容区域点击
        document.addEventListener('click', handleContentClick);
        
        // 窗口大小改变
        window.addEventListener('resize', handleResize);
        
        // 高亮当前导航
        highlightCurrentNav();
        
        // 初始状态更新
        updateBackToTop();
        updateOutlineHighlight();
        
        // 处理页面加载时的锚点
        if (window.location.hash) {
            setTimeout(() => {
                const targetId = window.location.hash.slice(1);
                const targetElement = document.getElementById(targetId);
                if (targetElement) {
                    const offset = 100;
                    const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - offset;
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'auto'
                    });
                }
            }, 100);
        }
    }
    
    // DOM 加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // 暴露 API
    window.NavManager = {
        openSidebar,
        closeSidebar,
        toggleSidebar,
        scrollToTop
    };
})();
