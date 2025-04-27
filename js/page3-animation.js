// Function to animate a value
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        const value = start + (end - start) * progress;
        element.textContent = value.toFixed(1) + '%';
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// Function to start animations for page 3
function startPage3Animations() {
    // Get all percentage elements
    const percentages = document.querySelectorAll('#fullpage > .section:nth-of-type(3) .data-card .percentage');
    
    // Reset all percentages to 0
    percentages.forEach(percentage => {
        percentage.textContent = '0.0%';
    });
    
    // Animate each percentage with appropriate delay
    setTimeout(() => {
        animateValue(percentages[0], 0, 19.9, 2000);
    }, 300);
    
    setTimeout(() => {
        animateValue(percentages[1], 0, 10.8, 2000);
    }, 600);
}

// Initialize fullPage.js
new fullpage('#fullpage', {
    // ... other options ...
    afterLoad: function(origin, destination, direction) {
        // Start animations when section 3 is loaded
        if (destination.index === 2) {
            startPage3Animations();
        }
    },
    onLeave: function(origin, destination, direction) {
        // Reset animations when leaving section 3
        if (origin.index === 2) {
            const percentages = document.querySelectorAll('#fullpage > .section:nth-of-type(3) .data-card .percentage');
            percentages.forEach(percentage => {
                percentage.textContent = '0.0%';
            });
        }
    }
});

// Start animations on page load if we're already on section 3
if (document.querySelector('#fullpage > .section:nth-of-type(3).active')) {
    startPage3Animations();
}

// Set and lock the percentage for page 2
document.addEventListener('DOMContentLoaded', function() {
    const page2Percentage = document.querySelector('#fullpage > .section:nth-of-type(3) .slide:nth-of-type(2) .percentage-text .percentage');
    if (page2Percentage) {
        // Set the value
        page2Percentage.textContent = '25%';
        
        // Prevent any changes to this element
        Object.defineProperty(page2Percentage, 'textContent', {
            get: function() { return '25%'; },
            set: function() { return '25%'; }
        });
    }

    // Set and lock the percentage for page 3
    const page3Percentage = document.querySelector('#fullpage > .section:nth-of-type(3) .slide:nth-of-type(3) .percentage');
    if (page3Percentage) {
        // Set the value
        page3Percentage.textContent = '62M';
        
        // Prevent any changes to this element
        Object.defineProperty(page3Percentage, 'textContent', {
            get: function() { return '62M'; },
            set: function() { return '62M'; }
        });
    }
}); 