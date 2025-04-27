function animateValue(element, start, end, duration, suffix = '%') {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const currentValue = start + (end - start) * progress;
        element.textContent = currentValue.toFixed(1) + suffix;
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Function to start animations
function startAnimations() {
    const firstPercentage = document.querySelector('#fullpage > .section:nth-child(3) .slide:nth-child(1) .data-card:nth-child(1) .percentage');
    const secondPercentage = document.querySelector('#fullpage > .section:nth-child(3) .slide:nth-child(1) .data-card:nth-child(2) .percentage');

    if (firstPercentage) {
        firstPercentage.textContent = '0.0%';
        setTimeout(() => {
            animateValue(firstPercentage, 0, 19.9, 2000);
        }, 500);
    }
    if (secondPercentage) {
        secondPercentage.textContent = '0.0%';
        setTimeout(() => {
            animateValue(secondPercentage, 0, 10.8, 2000);
        }, 800);
    }

    // Set the Tech Hub Impact percentage to 25% without animation
    const techHubPercentage = document.querySelector('#fullpage > .section:nth-child(3) .slide:nth-child(2) .percentage-text .highlight.percentage');
    if (techHubPercentage) {
        techHubPercentage.textContent = '25%';
        techHubPercentage.style.animation = 'none';
        techHubPercentage.style.opacity = '1';
    }
}

// Start animations when the page loads
document.addEventListener('DOMContentLoaded', startAnimations);

// Also start animations when navigating to section 3
document.addEventListener('click', function(e) {
    const navLink = e.target.closest('#fp-nav a, .fp-slidesNav a');
    if (navLink) {
        setTimeout(startAnimations, 1000); // Wait for slide transition
    }
}); 