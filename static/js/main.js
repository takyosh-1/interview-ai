document.addEventListener('DOMContentLoaded', function() {
    console.log('従業員フィードバックシステムが読み込まれました');
    
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.style.backgroundColor = 'rgba(255,255,255,0.2)';
        }
    });
});
