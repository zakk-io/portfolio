document.addEventListener('DOMContentLoaded', () => {

  // ── 1. CUSTOM CURSOR ────────────────────────────────────────────
  const cursor = document.getElementById('cursor');
  const trail  = document.getElementById('cursorTrail');
  let mx = 0, my = 0, tx = 0, ty = 0;

  document.addEventListener('mousemove', e => {
    mx = e.clientX; my = e.clientY;
    cursor.style.left = mx + 'px';
    cursor.style.top  = my + 'px';
  });

  // Smooth trail
  function animateTrail() {
    tx += (mx - tx) * 0.12;
    ty += (my - ty) * 0.12;
    trail.style.left = tx + 'px';
    trail.style.top  = ty + 'px';
    requestAnimationFrame(animateTrail);
  }
  animateTrail();

  // Cursor grow on interactive elements
  document.querySelectorAll('a, button, .project-card, .skill-pills span').forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.style.transform = 'translate(-50%,-50%) scale(2.5)';
      trail.style.opacity = '0.4';
    });
    el.addEventListener('mouseleave', () => {
      cursor.style.transform = 'translate(-50%,-50%) scale(1)';
      trail.style.opacity = '1';
    });
  });


  // ── 2. NAVBAR SCROLL STATE ──────────────────────────────────────
  const navbar = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });


  // ── 3. HAMBURGER MENU ───────────────────────────────────────────
  const hamburger = document.getElementById('hamburger');
  hamburger.addEventListener('click', () => {
    navbar.classList.toggle('open');
  });
  // Close on link click
  document.querySelectorAll('.nav-links a').forEach(a => {
    a.addEventListener('click', () => navbar.classList.remove('open'));
  });


  // ── 4. SMOOTH SCROLL ────────────────────────────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        history.pushState(null, null, targetId);
      }
    });
  });


  // ── 5. INTERSECTION OBSERVER (scroll animations) ────────────────
  const observerOptions = {
    root: null,
    threshold: 0.1,
    rootMargin: '0px 0px -60px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        // Stagger child elements if they exist
        const children = entry.target.querySelectorAll(
          '.project-card, .info-card, .cert-card, .skill-group, .timeline-item'
        );
        if (children.length) {
          children.forEach((child, idx) => {
            child.style.transitionDelay = `${idx * 80}ms`;
            child.classList.add('fade-in-start');
            setTimeout(() => child.classList.add('fade-in-visible'), 50);
          });
        }
        entry.target.classList.add('fade-in-visible');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.fade-in-start').forEach(el => observer.observe(el));


  // ── 6. ACTIVE NAV LINK on scroll ────────────────────────────────
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a');

  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => {
          link.style.color = '';
          if (link.getAttribute('href') === '#' + entry.target.id) {
            link.style.color = 'var(--accent)';
          }
        });
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(s => sectionObserver.observe(s));


  // ── 7. TERMINAL TYPEWRITER ANIMATION ────────────────────────────
  const terminalEl = document.getElementById('terminalBody');
  if (!terminalEl) return;

  const lines = [
    { type: 'cmd',  prompt: '$',  text: 'whoami' },
    { type: 'out',  cls: 'acc',   text: 'Mohamed Zakaria — Software Engineer' },
    { type: 'cmd',  prompt: '$',  text: 'cat skills.txt' },
    { type: 'out',  cls: 'grn',   text: '→ Python, Node.js, FastAPI, Vue.js' },
    { type: 'out',  cls: 'grn',   text: '→ LLMs, RAG, ChromaDB, Gemini API' },
    { type: 'out',  cls: 'grn',   text: '→ AWS, GCP, Docker, GitHub Actions' },
    { type: 'cmd',  prompt: '$',  text: 'ls ./projects/' },
    { type: 'out',  cls: '',      text: 'ai-recruitment/   collab-editor/' },
    { type: 'out',  cls: '',      text: 'pr-review-bot/    vision-assistive/' },
    { type: 'cmd',  prompt: '$',  text: 'echo $STATUS' },
    { type: 'out',  cls: 'grn',   text: '✓ Available for opportunities' },
    { type: 'cmd',  prompt: '$',  text: '_' },
  ];

  let lineIdx = 0;
  let charIdx = 0;
  let currentEl = null;

  function typeLine() {
    if (lineIdx >= lines.length) return;
    const line = lines[lineIdx];

    if (charIdx === 0) {
      const div = document.createElement('div');
      div.className = 't-line';

      if (line.type === 'cmd') {
        div.innerHTML = `<span class="t-prompt">${line.prompt}</span><span class="t-cmd"></span>`;
        terminalEl.appendChild(div);
        currentEl = div.querySelector('.t-cmd');
      } else {
        div.innerHTML = `<span class="t-out ${line.cls}"></span>`;
        terminalEl.appendChild(div);
        currentEl = div.querySelector('.t-out');
      }
    }

    if (charIdx < line.text.length) {
      currentEl.textContent += line.text[charIdx];
      charIdx++;
      terminalEl.scrollTop = terminalEl.scrollHeight;
      const delay = line.type === 'cmd' ? 55 + Math.random() * 40 : 18;
      setTimeout(typeLine, delay);
    } else {
      lineIdx++;
      charIdx = 0;
      currentEl = null;
      const pause = line.type === 'cmd' ? 300 : 60;
      setTimeout(typeLine, pause);
    }
  }

  // Start terminal after a short delay (after hero appears)
  setTimeout(typeLine, 1200);


  // ── 8. HERO TITLE ROTATOR ───────────────────────────────────────
  const titles = [
    'AI-powered systems',
    'RAG pipelines',
    'real-time APIs',
    'cloud-native apps',
    'accessible AI tools',
  ];
  const rotateEl = document.getElementById('titleRotate');
  if (!rotateEl) return;

  let titleIdx = 0;
  function rotateTitle() {
    rotateEl.style.opacity = '0';
    rotateEl.style.transform = 'translateY(-8px)';
    setTimeout(() => {
      titleIdx = (titleIdx + 1) % titles.length;
      rotateEl.textContent = titles[titleIdx];
      rotateEl.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      rotateEl.style.opacity = '1';
      rotateEl.style.transform = 'translateY(0)';
    }, 300);
  }
  rotateEl.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
  setInterval(rotateTitle, 2800);

});
