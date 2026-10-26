/* DeckStation.id — shared site behaviour */
(function () {
    'use strict';

    var WA_LINK = 'https://wa.me/6285602897420';

    function ready(fn) {
        if (document.readyState !== 'loading') fn();
        else document.addEventListener('DOMContentLoaded', fn);
    }

    function renderIcons() {
        if (window.lucide && typeof window.lucide.createIcons === 'function') {
            window.lucide.createIcons();
        }
    }

    /* ===== MOBILE NAVIGATION ===== */
    function initNav() {
        var toggle = document.getElementById('navToggle');
        var nav = document.getElementById('siteNav');
        if (!toggle || !nav) return;

        toggle.addEventListener('click', function () {
            var open = nav.classList.toggle('open');
            toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
            toggle.innerHTML = '<i data-lucide="' + (open ? 'x' : 'menu') + '"></i>';
            renderIcons();
        });

        nav.addEventListener('click', function (e) {
            if (e.target.closest('a')) {
                nav.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.innerHTML = '<i data-lucide="menu"></i>';
                renderIcons();
            }
        });

        window.addEventListener('resize', function () {
            if (window.innerWidth > 992 && nav.classList.contains('open')) {
                nav.classList.remove('open');
                toggle.setAttribute('aria-expanded', 'false');
                toggle.innerHTML = '<i data-lucide="menu"></i>';
                renderIcons();
            }
        });
    }

    /* ===== HEADER STATE ON SCROLL ===== */
    function initHeaderScroll() {
        var header = document.getElementById('siteHeader');
        if (!header) return;

        var onScroll = function () {
            if (window.scrollY > 20) header.classList.add('is-scrolled');
            else header.classList.remove('is-scrolled');
        };

        onScroll();
        window.addEventListener('scroll', onScroll, { passive: true });
    }

    /* ===== FADE IN ON SCROLL ===== */
    function initFadeIn() {
        var els = Array.prototype.slice.call(document.querySelectorAll('.fade-in'));
        if (!els.length) return;

        function reveal(el) { el.classList.add('visible'); }

        if (!('IntersectionObserver' in window)) {
            els.forEach(reveal);
            return;
        }

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    reveal(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -20px 0px' });

        els.forEach(function (el) { observer.observe(el); });

        /* Reveal whatever is already on screen — never hide content behind a stalled observer */
        window.requestAnimationFrame(function () {
            els.forEach(function (el) {
                var rect = el.getBoundingClientRect();
                if (rect.top < window.innerHeight && rect.bottom > 0) {
                    reveal(el);
                    observer.unobserve(el);
                }
            });
        });

        /* Safety net: if the observer never fires, show everything */
        window.setTimeout(function () { els.forEach(reveal); }, 4000);
    }

    /* ===== FAQ ACCORDION ===== */
    function initFaq() {
        document.querySelectorAll('.faq-question').forEach(function (q) {
            q.addEventListener('click', function () {
                this.classList.toggle('active');
                var answer = this.nextElementSibling;
                if (answer) answer.classList.toggle('open');
            });
        });
    }

    /* ===== FAQ SEARCH ===== */
    function initFaqSearch() {
        var input = document.getElementById('faqSearch');
        if (!input) return;

        var items = Array.prototype.slice.call(document.querySelectorAll('.faq-item'));
        var groups = Array.prototype.slice.call(document.querySelectorAll('.faq-group-title'));
        var empty = document.getElementById('faqEmpty');

        input.addEventListener('input', function () {
            var q = this.value.trim().toLowerCase();
            var visible = 0;

            items.forEach(function (item) {
                var match = !q || item.textContent.toLowerCase().indexOf(q) !== -1;
                item.classList.toggle('hidden', !match);
                if (match) visible++;
            });

            groups.forEach(function (group) {
                var next = group.nextElementSibling;
                var any = false;
                while (next && !next.classList.contains('faq-group-title')) {
                    if (next.classList.contains('faq-item') && !next.classList.contains('hidden')) any = true;
                    next = next.nextElementSibling;
                }
                group.style.display = any ? '' : 'none';
            });

            if (empty) empty.style.display = visible ? 'none' : 'block';
        });
    }

    /* ===== SERVICE FILTER ===== */
    function initServiceFilter() {
        var chips = Array.prototype.slice.call(document.querySelectorAll('[data-filter-chip]'));
        var cards = Array.prototype.slice.call(document.querySelectorAll('[data-category]'));
        if (!chips.length || !cards.length) return;

        chips.forEach(function (chip) {
            chip.addEventListener('click', function () {
                var target = chip.getAttribute('data-filter-chip');
                chips.forEach(function (c) { c.classList.remove('active'); });
                chip.classList.add('active');

                cards.forEach(function (card) {
                    var cat = card.getAttribute('data-category') || '';
                    var show = target === 'all' || cat.indexOf(target) !== -1;
                    card.style.display = show ? '' : 'none';
                });
            });
        });
    }

    /* ===== SUCCESS PAGE DETAILS ===== */
    function initSuccessPage() {
        var params = new URLSearchParams(window.location.search);
        var nama = params.get('nama');
        var layanan = params.get('layanan');
        var tanggal = params.get('tanggal');

        var setText = function (id, value, fallback) {
            var el = document.getElementById(id);
            if (el) el.textContent = value || fallback;
        };

        setText('nama', nama, 'you');
        setText('layanan', layanan, '—');
        setText('tanggal', tanggal, '—');

        var waBtn = document.getElementById('successWa');
        if (waBtn && layanan) {
            var msg = encodeURIComponent(
                'Halo DeckStation, saya sudah booking via website.\n\n' +
                'Nama: ' + (nama || '-') + '\n' +
                'Layanan: ' + layanan + '\n' +
                'Tanggal: ' + (tanggal || '-')
            );
            waBtn.setAttribute('href', WA_LINK + '?text=' + msg);
        }
    }

    /* ===== BOOKING FORM SUBJECT ===== */
    function initBookingForm() {
        var form = document.querySelector('.booking-form form');
        if (!form) return;

        form.addEventListener('submit', function () {
            var layanan = form.layanan ? (form.layanan.value || 'Service') : 'Service';
            var nama = form.nama ? (form.nama.value || 'N/A') : 'N/A';
            if (form._subject) form._subject.value = '[New Booking] ' + layanan + ' - ' + nama;
        });
    }

    /* ===== PRE-FILLED SERVICE BOOKING ===== */
    function initServicePrefill() {
        var params = new URLSearchParams(window.location.search);
        var service = params.get('service');
        if (!service) return;

        var select = document.getElementById('layanan');
        if (!select) return;

        Array.prototype.forEach.call(select.options, function (option) {
            if (option.value === service || option.textContent.indexOf(service) !== -1) {
                select.value = option.value;
            }
        });
    }

    ready(function () {
        renderIcons();
        initNav();
        initHeaderScroll();
        initFadeIn();
        initFaq();
        initFaqSearch();
        initServiceFilter();
        initSuccessPage();
        initBookingForm();
        initServicePrefill();
    });
})();
