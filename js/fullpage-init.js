document.addEventListener('DOMContentLoaded', function() {
    new fullpage('#fullpage', {
        // Navigation
        menu: '#menu',
        lockAnchors: false,
        anchors:['firstPage', 'secondPage', 'thirdPage', 'fourthPage', 'fifthPage', 'sixthPage'],
        navigation: true,
        navigationPosition: 'right',
        navigationTooltips: ['Intro', 'Analysis', 'Urban', 'Suburban', 'Data', 'Case Studies'],
        showActiveTooltip: false,
        slidesNavigation: true,
        slidesNavPosition: 'bottom',

        // Scrolling
        css3: true,
        scrollingSpeed: 700,
        autoScrolling: true,
        fitToSection: true,
        fitToSectionDelay: 1000,
        scrollBar: false,
        easing: 'easeInOutCubic',
        easingcss3: 'ease',
        loopBottom: false,
        loopTop: false,
        loopHorizontal: true,
        continuousVertical: false,
        continuousHorizontal: false,
        scrollHorizontally: false,
        interlockedSlides: false,
        dragAndMove: false,
        offsetSections: false,
        resetSliders: false,
        fadingEffect: false,
        normalScrollElements: '#element1, .element2',
        scrollOverflow: false,
        scrollOverflowReset: false,
        scrollOverflowOptions: null,
        touchSensitivity: 15,
        bigSectionsDestination: null,

        // Accessibility
        keyboardScrolling: true,
        animateAnchor: true,
        recordHistory: true,

        // Design
        controlArrows: true,
        verticalCentered: true,
        sectionsColor : ['#fff', '#fff', '#fff', '#fff', '#fff', '#fff'],
        paddingTop: '0',
        paddingBottom: '0',
        fixedElements: '#header, .footer',
        responsiveWidth: 0,
        responsiveHeight: 0,
        responsiveSlides: false,
        parallax: false,
        parallaxOptions: {type: 'reveal', percentage: 62, property: 'translate'},

        // Custom selectors
        sectionSelector: '.section',
        slideSelector: '.slide',

        lazyLoading: true,

        // Events
        onLeave: function(origin, destination, direction) {
            // Remove the section-based animation trigger
        },
        afterLoad: function(origin, destination, direction){
            // Add tooltip styling after page load
            const tooltips = document.querySelectorAll('#fp-nav ul li .fp-tooltip');
            tooltips.forEach(tooltip => {
                tooltip.style.color = '#E65100';
                tooltip.style.background = 'rgba(255, 255, 255, 0.8)';
                tooltip.style.borderRadius = '4px';
                tooltip.style.padding = '4px 8px';
                tooltip.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
            });
        },
        afterRender: function(){},
        afterResize: function(width, height){},
        afterResponsive: function(isResponsive){},
        afterSlideLoad: function(section, origin, destination, direction) {
            // Animation is now handled by CSS
        },
        onSlideLeave: function(section, origin, destination, direction){}
    });
}); 