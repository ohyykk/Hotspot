function animateSquareFeet(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const currentValue = Math.floor(start + (end - start) * progress);
        element.textContent = currentValue + 'M';
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

document.addEventListener('DOMContentLoaded', () => {
    const squareFeetValue = document.querySelector('#fullpage > .section:nth-child(3) .slide:nth-child(3) .percentage');
    if (squareFeetValue) {
        // Set initial value
        squareFeetValue.textContent = '0M';
        
        // Start animation after a short delay
        setTimeout(() => {
            animateSquareFeet(squareFeetValue, 0, 62, 2000);
        }, 300);
    }
}); 