// Nexus MCP Server Documentation JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle functionality
    const themeToggle = document.querySelector('.theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeToggle(currentTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeToggle(newTheme);
        });
    }
    
    function updateThemeToggle(theme) {
        if (themeToggle) {
            themeToggle.innerHTML = theme === 'dark' ? '☀️' : '🌙';
            themeToggle.title = `Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`;
        }
    }
    
    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
        
        // Close sidebar when clicking outside
        document.addEventListener('click', function(e) {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
    
    // Scroll to top button
    const scrollTopBtn = document.querySelector('.scroll-top');
    
    if (scrollTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                scrollTopBtn.classList.add('visible');
            } else {
                scrollTopBtn.classList.remove('visible');
            }
        });
        
        scrollTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Search functionality
    const searchInput = document.querySelector('.search-input');
    let searchIndex = [];
    
    if (searchInput) {
        // Build search index
        buildSearchIndex();
        
        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase().trim();
            if (query.length > 2) {
                performSearch(query);
            } else {
                hideSearchResults();
            }
        });
        
        // Hide search results when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.search-container')) {
                hideSearchResults();
            }
        });
    }
    
    function buildSearchIndex() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        const paragraphs = document.querySelectorAll('p');
        const codeBlocks = document.querySelectorAll('code, pre');
        
        // Index headings
        headings.forEach(heading => {
            if (heading.id) {
                searchIndex.push({
                    title: heading.textContent,
                    content: heading.textContent,
                    url: `#${heading.id}`,
                    type: 'heading'
                });
            }
        });
        
        // Index paragraphs
        paragraphs.forEach(p => {
            const nearestHeading = findNearestHeading(p);
            searchIndex.push({
                title: nearestHeading ? nearestHeading.textContent : 'Content',
                content: p.textContent,
                url: nearestHeading && nearestHeading.id ? `#${nearestHeading.id}` : '#',
                type: 'content'
            });
        });
        
        // Index code blocks
        codeBlocks.forEach(code => {
            const nearestHeading = findNearestHeading(code);
            searchIndex.push({
                title: nearestHeading ? nearestHeading.textContent : 'Code',
                content: code.textContent,
                url: nearestHeading && nearestHeading.id ? `#${nearestHeading.id}` : '#',
                type: 'code'
            });
        });
    }
    
    function findNearestHeading(element) {
        let current = element;
        while (current && current !== document.body) {
            const heading = current.querySelector('h1, h2, h3, h4, h5, h6');
            if (heading) return heading;
            
            const prev = current.previousElementSibling;
            if (prev && prev.matches('h1, h2, h3, h4, h5, h6')) {
                return prev;
            }
            
            current = current.parentElement;
        }
        return null;
    }
    
    function performSearch(query) {
        const results = searchIndex.filter(item => 
            item.title.toLowerCase().includes(query) || 
            item.content.toLowerCase().includes(query)
        ).slice(0, 10);
        
        showSearchResults(results, query);
    }
    
    function showSearchResults(results, query) {
        let resultsContainer = document.querySelector('.search-results');
        
        if (!resultsContainer) {
            resultsContainer = document.createElement('div');
            resultsContainer.className = 'search-results';
            resultsContainer.style.cssText = `
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: var(--bg-primary);
                border: 1px solid var(--border-color);
                border-radius: 0.5rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                max-height: 400px;
                overflow-y: auto;
                z-index: 1000;
                margin-top: 0.25rem;
            `;
            document.querySelector('.search-container').appendChild(resultsContainer);
        }
        
        if (results.length === 0) {
            resultsContainer.innerHTML = '<div style="padding: 1rem; color: var(--text-secondary);">No results found</div>';
        } else {
            resultsContainer.innerHTML = results.map(result => {
                const highlightedTitle = highlightText(result.title, query);
                const highlightedContent = highlightText(
                    result.content.substring(0, 150) + (result.content.length > 150 ? '...' : ''),
                    query
                );
                
                return `
                    <a href="${result.url}" class="search-result-item" style="
                        display: block;
                        padding: 0.75rem 1rem;
                        text-decoration: none;
                        border-bottom: 1px solid var(--border-color);
                        transition: background 0.2s ease;
                    " onmouseover="this.style.background='var(--bg-secondary)'" 
                       onmouseout="this.style.background='transparent'">
                        <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem;">
                            ${highlightedTitle}
                        </div>
                        <div style="font-size: 0.875rem; color: var(--text-secondary);">
                            ${highlightedContent}
                        </div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">
                            ${result.type}
                        </div>
                    </a>
                `;
            }).join('');
        }
        
        resultsContainer.style.display = 'block';
    }
    
    function hideSearchResults() {
        const resultsContainer = document.querySelector('.search-results');
        if (resultsContainer) {
            resultsContainer.style.display = 'none';
        }
    }
    
    function highlightText(text, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark style="background: yellow; padding: 0.125rem;">$1</mark>');
    }
    
    // Active navigation highlighting
    function updateActiveNavigation() {
        const sections = document.querySelectorAll('h1[id], h2[id], h3[id]');
        const navLinks = document.querySelectorAll('.sidebar-nav a');
        
        let current = '';
        
        sections.forEach(section => {
            const rect = section.getBoundingClientRect();
            if (rect.top <= 100) {
                current = section.id;
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    }
    
    // Update navigation on scroll
    window.addEventListener('scroll', updateActiveNavigation);
    updateActiveNavigation();
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Copy code block functionality
    document.querySelectorAll('pre code').forEach(block => {
        const button = document.createElement('button');
        button.textContent = 'Copy';
        button.style.cssText = `
            position: absolute;
            top: 0.5rem;
            right: 0.5rem;
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 0.25rem;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s ease;
        `;
        
        const container = block.parentElement;
        container.style.position = 'relative';
        container.appendChild(button);
        
        container.addEventListener('mouseenter', () => {
            button.style.opacity = '1';
        });
        
        container.addEventListener('mouseleave', () => {
            button.style.opacity = '0';
        });
        
        button.addEventListener('click', () => {
            navigator.clipboard.writeText(block.textContent).then(() => {
                button.textContent = 'Copied!';
                setTimeout(() => {
                    button.textContent = 'Copy';
                }, 2000);
            });
        });
    });
    
    // Auto-generate table of contents
    function generateTableOfContents() {
        const tocContainer = document.querySelector('.toc-placeholder');
        if (!tocContainer) return;
        
        const headings = document.querySelectorAll('h2, h3, h4');
        if (headings.length === 0) return;
        
        let tocHTML = '<div class="toc"><h4>📑 Table of Contents</h4><ul>';
        
        headings.forEach(heading => {
            const level = parseInt(heading.tagName.charAt(1));
            const indent = (level - 2) * 1;
            const id = heading.id || heading.textContent.toLowerCase().replace(/[^a-z0-9]+/g, '-');
            
            if (!heading.id) {
                heading.id = id;
            }
            
            tocHTML += `
                <li style="margin-left: ${indent}rem;">
                    <a href="#${id}">${heading.textContent}</a>
                </li>
            `;
        });
        
        tocHTML += '</ul></div>';
        tocContainer.innerHTML = tocHTML;
    }
    
    generateTableOfContents();
});

// Utility functions
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}