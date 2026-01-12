
    document.addEventListener('DOMContentLoaded', () => {
        
        // 1. Smooth Scroll with URL Hash Update
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);

                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                    // Optional: Updates URL without jumping
                    history.pushState(null, null, targetId);
                }
            });
        });

        // 2. Intersection Observer for Scroll Animations
        const observerOptions = {
            root: null, // use viewport
            threshold: 0.15, // trigger when 15% of section is visible
            rootMargin: "0px 0px -50px 0px" // trigger slightly before it hits the view
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in-visible');
                    // Un-observe if you only want the animation to happen once
                    observer.unobserve(entry.target); 
                }
            });
        }, observerOptions);

        // Apply starting state and observe each section
        document.querySelectorAll('section').forEach(section => {
            section.classList.add('fade-in-start');
            observer.observe(section);
        });
    });
