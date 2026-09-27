/* Declutter Junk Removal — interactions & motion.
   Everything works without this file; it layers on polish. */
(() => {
  'use strict';

  const doc = document;
  const root = doc.documentElement;
  const $ = (s, c = doc) => c.querySelector(s);
  const $$ = (s, c = doc) => Array.from(c.querySelectorAll(s));
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const saveData = navigator.connection && navigator.connection.saveData;

  /* ---------- Header: scrolled state, hide on scroll down ---------- */
  const header = $('.site-header');
  const bar = $('.action-bar');
  let lastY = scrollY;
  let ticking = false;
  const onScroll = () => {
    const y = scrollY;
    header.classList.toggle('is-scrolled', y > 12);
    if (!doc.body.classList.contains('menu-open') && Math.abs(y - lastY) > 4) {
      header.classList.toggle('is-hidden', y > lastY && y > 520);
    }
    if (bar) bar.classList.toggle('is-visible', y > 360);
    lastY = y;
    ticking = false;
  };
  addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(onScroll); ticking = true; }
  }, { passive: true });
  header.addEventListener('focusin', () => header.classList.remove('is-hidden'));
  onScroll();

  /* ---------- Mobile menu ---------- */
  const menuBtn = $('.menu-btn');
  const menu = $('#mobile-menu');
  if (menuBtn && menu) {
    const setMenu = (open) => {
      menu.classList.toggle('is-open', open);
      menuBtn.setAttribute('aria-expanded', String(open));
      menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      doc.body.classList.toggle('menu-open', open);
      menu.inert = !open;
      if (open) header.classList.remove('is-hidden');
    };
    menuBtn.addEventListener('click', () => setMenu(menuBtn.getAttribute('aria-expanded') !== 'true'));
    addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && menu.classList.contains('is-open')) { setMenu(false); menuBtn.focus(); }
    });
    $$('a', menu).forEach((a) => a.addEventListener('click', () => setMenu(false)));
    matchMedia('(min-width: 1080px)').addEventListener('change', (e) => { if (e.matches) setMenu(false); });
  }

  /* ---------- Before / after sliders ---------- */
  $$('.ba').forEach((ba) => {
    const media = $('.ba-media', ba);
    const range = $('.ba-range', ba);
    const set = (v) => {
      v = Math.max(0, Math.min(100, v));
      ba.style.setProperty('--pos', v + '%');
      range.value = Math.round(v);
    };
    ba._set = set;
    range.addEventListener('input', () => { ba.dataset.touched = '1'; set(+range.value); });

    const pct = (e) => {
      const r = media.getBoundingClientRect();
      return ((e.clientX - r.left) / r.width) * 100;
    };
    let state = null; // null | 'pending' | 'drag'
    let sx = 0, sy = 0;
    media.addEventListener('pointerdown', (e) => {
      ba.dataset.touched = '1';
      if (e.pointerType === 'mouse') {
        state = 'drag';
        media.setPointerCapture(e.pointerId);
        set(pct(e));
      } else {
        state = 'pending'; sx = e.clientX; sy = e.clientY;
      }
    });
    media.addEventListener('pointermove', (e) => {
      if (state === 'pending') {
        const dx = Math.abs(e.clientX - sx), dy = Math.abs(e.clientY - sy);
        if (dx > 6 && dx > dy) { state = 'drag'; media.setPointerCapture(e.pointerId); }
        else if (dy > 8) { state = null; }
      }
      if (state === 'drag') set(pct(e));
    });
    const end = (e) => {
      if (state === 'pending' && e.type === 'pointerup') set(pct(e)); // tap to jump
      state = null;
    };
    media.addEventListener('pointerup', end);
    media.addEventListener('pointercancel', end);
  });

  /* ---------- Hero time-lapse video ---------- */
  const heroVideo = $('[data-hero-video]');
  if (heroVideo) {
    const card = heroVideo.closest('.video-card');
    const toggle = $('.video-toggle', card);
    const prog = $('.video-progress', card);
    const src = heroVideo.dataset.src;
    const canPlay = src && !reduceMotion && !saveData;

    const load = () => {
      heroVideo.src = src;
      heroVideo.load();
      heroVideo.play().catch(() => {});
    };
    if (canPlay) {
      if (doc.readyState === 'complete') load(); else addEventListener('load', load, { once: true });
    }
    // Pause when off-screen to save battery
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(([en]) => {
        if (!heroVideo.src || toggle.getAttribute('aria-pressed') === 'true') return;
        en.isIntersecting ? heroVideo.play().catch(() => {}) : heroVideo.pause();
      }, { threshold: 0.15 }).observe(card);
    }
    heroVideo.addEventListener('timeupdate', () => {
      if (heroVideo.duration) prog.style.setProperty('--p', (heroVideo.currentTime / heroVideo.duration).toFixed(3));
    });
    toggle.addEventListener('click', () => {
      if (!heroVideo.src) { load(); toggle.setAttribute('aria-pressed', 'false'); toggle.setAttribute('aria-label', 'Pause video'); return; }
      const paused = heroVideo.paused;
      paused ? heroVideo.play() : heroVideo.pause();
      toggle.setAttribute('aria-pressed', String(!paused));
      toggle.setAttribute('aria-label', paused ? 'Pause video' : 'Play video');
    });
    if (!canPlay) { toggle.setAttribute('aria-pressed', 'true'); toggle.setAttribute('aria-label', 'Play video'); }
  }

  /* ---------- FAQ: smooth open/close ---------- */
  $$('details.faq-item').forEach((d) => {
    const summary = $('summary', d);
    const body = $('.faq-a', d);
    let anim = null;
    summary.addEventListener('click', (e) => {
      if (reduceMotion || !body.animate) return;
      e.preventDefault();
      if (anim) anim.cancel();
      if (d.open) {
        anim = body.animate([{ height: body.offsetHeight + 'px', opacity: 1 }, { height: '0px', opacity: 0 }],
          { duration: 300, easing: 'cubic-bezier(.4,0,.2,1)' });
        anim.onfinish = () => { d.open = false; anim = null; };
      } else {
        d.open = true;
        anim = body.animate([{ height: '0px', opacity: 0 }, { height: body.offsetHeight + 'px', opacity: 1 }],
          { duration: 460, easing: 'cubic-bezier(.16,1,.3,1)' });
        anim.onfinish = () => { anim = null; };
      }
    });
  });

  /* ---------- Horizontal strips / carousels ---------- */
  $$('[data-scroller]').forEach((wrap) => {
    const track = $('[data-track]', wrap);
    const step = () => (track.firstElementChild ? track.firstElementChild.getBoundingClientRect().width + 16 : 300);
    $$('[data-dir]', wrap).forEach((b) => b.addEventListener('click', () => {
      track.scrollBy({ left: step() * +b.dataset.dir, behavior: reduceMotion ? 'auto' : 'smooth' });
    }));
  });

  /* ---------- Quote form ---------- */
  const form = $('#quote-form');
  if (form) initQuoteForm(form);

  function initQuoteForm(form) {
    const steps = $$('.qf-step', form);
    const count = $('.qf-count', form);
    const title = $('.qf-title', form);
    const progress = $('.qf-progress span', form);
    let i = 0;

    // Send people back to this site's thank-you page after the email service accepts the form
    const next = $('input[name="_next"]', form);
    if (next) next.value = location.origin + '/thanks/';

    const show = (n, focus) => {
      i = n;
      steps.forEach((s, k) => s.classList.toggle('is-active', k === i));
      count.textContent = `Step ${i + 1} of ${steps.length}`;
      title.textContent = steps[i].dataset.title;
      progress.style.setProperty('--w', ((i + 1) / steps.length) * 100 + '%');
      if (focus) {
        const first = $('input:not([type=hidden]), select, textarea', steps[i]);
        const top = form.getBoundingClientRect().top + scrollY - 110;
        if (scrollY > top) scrollTo({ top, behavior: reduceMotion ? 'auto' : 'smooth' });
        if (first) first.focus({ preventScroll: true });
      }
    };

    const validate = (step) => {
      let ok = true;
      $$('.field', step).forEach((f) => f.classList.remove('has-error'));
      const invalid = $$('input, select, textarea', step).filter((el) => !el.checkValidity());
      invalid.forEach((el) => { const f = el.closest('.field'); if (f) f.classList.add('has-error'); });
      if (invalid.length) { ok = false; invalid[0].focus(); }
      return ok;
    };

    $$('[data-next]', form).forEach((b) => b.addEventListener('click', () => {
      if (validate(steps[i])) show(i + 1, true);
    }));
    $$('[data-prev]', form).forEach((b) => b.addEventListener('click', () => show(i - 1, true)));
    $$('input, select, textarea', form).forEach((el) => el.addEventListener('input', () => {
      const f = el.closest('.field');
      if (f && el.checkValidity()) f.classList.remove('has-error');
    }));

    // Pre-select a service from ?service=
    const pre = new URLSearchParams(location.search).get('service');
    if (pre) {
      const r = $(`input[name="service"][data-key="${CSS.escape(pre)}"]`, form);
      if (r) r.checked = true;
    }

    // Photo slots: preview + shrink big photos so uploads stay fast
    $$('.drop input[type=file]', form).forEach((input) => {
      input.addEventListener('change', async () => {
        const slot = input.closest('.drop');
        const name = $('.drop-name', slot);
        let file = input.files && input.files[0];
        if (!file) { slot.classList.remove('has-file'); slot.style.removeProperty('--thumb'); return; }
        if (file.size > 1.2e6 && /image\/(jpeg|png|webp)/.test(file.type) && window.createImageBitmap && window.DataTransfer) {
          try {
            const small = await shrink(file);
            if (small && small.size < file.size) {
              const dt = new DataTransfer(); dt.items.add(small); input.files = dt.files; file = small;
            }
          } catch (_) { /* keep original */ }
        }
        slot.style.setProperty('--thumb', `url("${URL.createObjectURL(file)}")`);
        slot.classList.add('has-file');
        name.textContent = file.name;
      });
    });

    form.addEventListener('submit', (e) => {
      if (!validate(steps[i])) { e.preventDefault(); return; }
      const total = $$('input[type=file]', form).reduce((s, el) => s + (el.files[0] ? el.files[0].size : 0), 0);
      if (total > 7.5e6) {
        e.preventDefault();
        alert('Those photos are a bit large to send together. Please remove one, or text them to us instead.');
        return;
      }
      const btn = $('[type=submit]', form);
      btn.disabled = true;
      btn.querySelector('span').textContent = 'Sending…';
    });

    show(0, false);
  }

  async function shrink(file) {
    const bmp = await createImageBitmap(file);
    const scale = Math.min(1, 1800 / Math.max(bmp.width, bmp.height));
    const c = doc.createElement('canvas');
    c.width = Math.round(bmp.width * scale);
    c.height = Math.round(bmp.height * scale);
    c.getContext('2d').drawImage(bmp, 0, 0, c.width, c.height);
    const blob = await new Promise((r) => c.toBlob(r, 'image/jpeg', 0.82));
    return blob ? new File([blob], file.name.replace(/\.\w+$/, '') + '.jpg', { type: 'image/jpeg' }) : null;
  }

  /* ======================================================================
     Motion (GSAP). Skipped entirely for reduced motion or if GSAP failed.
     ====================================================================== */
  const gsap = window.gsap;
  const ST = window.ScrollTrigger;
  if (reduceMotion || !gsap || !ST || root.classList.contains('no-anim')) {
    root.classList.add('no-anim');
    $$('.step').forEach((s) => s.classList.add('is-on'));
    return;
  }
  gsap.registerPlugin(ST);
  root.classList.add('anim-ready');

  // Split headings into masked words
  const split = (el) => {
    const walk = (node) => {
      Array.from(node.childNodes).forEach((n) => {
        if (n.nodeType === 3) {
          const frag = doc.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach((part) => {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.appendChild(doc.createTextNode(' ')); return; }
            const w = doc.createElement('span'); w.className = 'split-w';
            const inner = doc.createElement('span'); inner.textContent = part;
            w.appendChild(inner); frag.appendChild(w);
          });
          n.replaceWith(frag);
        } else if (n.nodeType === 1 && n.tagName !== 'BR') {
          walk(n);
        }
      });
    };
    walk(el);
    return $$('.split-w > span', el);
  };

  $$('[data-split]').forEach((el) => {
    const words = split(el);
    gsap.set(words, { yPercent: 110 });
    el.style.visibility = 'visible';
    gsap.to(words, {
      yPercent: 0, duration: 1.15, ease: 'expo.out', stagger: 0.045,
      scrollTrigger: { trigger: el, start: 'top 90%', once: true },
    });
  });

  // Hero intro
  const hero = $('.hero');
  if (hero) {
    const tl = gsap.timeline({ defaults: { ease: 'expo.out' }, delay: 0.1 });
    tl.to('.hero h1 .line > span', { y: 0, yPercent: 0, duration: 1.3, stagger: 0.12 })
      .fromTo('[data-hero]', { opacity: 0, y: 22 }, { opacity: 1, y: 0, duration: 1, stagger: 0.08 }, 0.35)
      .fromTo('.hero .video-card',
        { clipPath: 'inset(10% 10% 10% 10% round 28px)', scale: 1.06 },
        { clipPath: 'inset(0% 0% 0% 0% round 28px)', scale: 1, duration: 1.6 }, 0.1)
      .fromTo('.chip-float', { opacity: 0, y: 18, scale: 0.96 }, { opacity: 1, y: 0, scale: 1, duration: 0.9, stagger: 0.15 }, 0.9);
  }

  // Generic reveals, batched so siblings stagger
  gsap.set('[data-reveal]', { y: 34 });
  ST.batch('[data-reveal]', {
    start: 'top 90%', once: true,
    onEnter: (els) => gsap.to(els, { opacity: 1, y: 0, duration: 1.1, ease: 'expo.out', stagger: 0.09, overwrite: true }),
  });

  // Slider hint: a single gentle sweep the first time each comes into view
  $$('.ba').forEach((ba) => {
    const p = { v: 50 };
    ST.create({
      trigger: ba, start: 'top 70%', once: true,
      onEnter: () => {
        if (ba.dataset.touched) return;
        gsap.timeline({ onUpdate: () => { if (!ba.dataset.touched) ba._set(p.v); } })
          .to(p, { v: 22, duration: 0.9, ease: 'power2.inOut' })
          .to(p, { v: 76, duration: 1.1, ease: 'power2.inOut' })
          .to(p, { v: 50, duration: 0.8, ease: 'power2.out' });
      },
    });
  });

  const mm = gsap.matchMedia();

  // Gentle image parallax on larger screens
  mm.add('(min-width: 900px)', () => {
    $$('[data-parallax]').forEach((wrap) => {
      const t = $('img', wrap) || $('video', wrap);
      if (!t) return;
      gsap.fromTo(t, { yPercent: -6, scale: 1.14 }, {
        yPercent: 6, scale: 1.14, ease: 'none',
        scrollTrigger: { trigger: wrap, start: 'top bottom', end: 'bottom top', scrub: true },
      });
    });
  });

  // Process line fills as you scroll; step numbers light up
  const line = $('.steps-line i');
  if (line) {
    gsap.fromTo(line, { scaleY: 0 }, {
      scaleY: 1, ease: 'none',
      scrollTrigger: { trigger: '.steps', start: 'top 65%', end: 'bottom 65%', scrub: 0.6 },
    });
    $$('.step').forEach((s) => ST.create({
      trigger: s, start: 'top 65%',
      onEnter: () => s.classList.add('is-on'),
      onLeaveBack: () => s.classList.remove('is-on'),
    }));
  }

  // Map: rings, roads and towns draw in
  const map = $('.map');
  if (map) {
    const tl = gsap.timeline({ scrollTrigger: { trigger: map, start: 'top 80%', once: true } });
    $$('.road, .river', map).forEach((p) => {
      const len = p.getTotalLength ? p.getTotalLength() : 800;
      gsap.set(p, { strokeDasharray: len, strokeDashoffset: len });
    });
    tl.from('.ring, .ring-fill', { scale: 0.6, opacity: 0, transformOrigin: '50% 50%', duration: 1.4, ease: 'expo.out', stagger: 0.1 })
      .to('.road, .river', { strokeDashoffset: 0, duration: 1.6, ease: 'power2.inOut', stagger: 0.08 }, 0.1)
      .from('.map-city', { opacity: 0, y: 10, duration: 0.7, ease: 'back.out(2)', stagger: 0.07 }, 0.5);
  }

  // Big CTA: letters fill in as it scrolls into view
  $$('.fill-text').forEach((el) => {
    gsap.fromTo($('.fill', el), { clipPath: 'inset(0 100% 0 0)' }, {
      clipPath: 'inset(0 0% 0 0)', ease: 'none',
      scrollTrigger: { trigger: el, start: 'top 85%', end: 'bottom 50%', scrub: 0.5 },
    });
  });

  // Film strip drifts slightly with scroll
  mm.add('(min-width: 760px)', () => {
    const strip = $('.strip');
    if (strip) {
      gsap.fromTo(strip, { x: 60 }, {
        x: -60, ease: 'none',
        scrollTrigger: { trigger: strip, start: 'top bottom', end: 'bottom top', scrub: true },
      });
    }
  });

  // Magnetic primary buttons (mouse only)
  if (finePointer) {
    $$('.btn-magnetic').forEach((b) => {
      const xTo = gsap.quickTo(b, 'x', { duration: 0.6, ease: 'power3' });
      const yTo = gsap.quickTo(b, 'y', { duration: 0.6, ease: 'power3' });
      b.addEventListener('pointermove', (e) => {
        const r = b.getBoundingClientRect();
        xTo((e.clientX - r.left - r.width / 2) * 0.22);
        yTo((e.clientY - r.top - r.height / 2) * 0.3);
      });
      b.addEventListener('pointerleave', () => { xTo(0); yTo(0); });
    });
  }

  addEventListener('load', () => ST.refresh());
})();
