/* Pearl Beauty 'n' Spa — μικρά, χωρίς εξαρτήσεις. */
(function () {
  'use strict';

  /* ---------------------------------------------- header σε κύλιση ------ */
  var head = document.querySelector('.head');
  if (head) {
    var stuck = false;
    var onScroll = function () {
      var now = window.scrollY > 24;
      if (now !== stuck) {
        stuck = now;
        head.classList.toggle('head--stuck', stuck);
      }
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---------------------------------------------- μενού σε κινητό ------- */
  var burger = document.querySelector('.burger');
  var nav = document.getElementById('nav');
  if (burger && nav) {
    var setOpen = function (open) {
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
      nav.setAttribute('data-open', open ? 'true' : 'false');
      document.documentElement.style.overflow = open ? 'hidden' : '';
      burger.setAttribute('aria-label', open ? 'Κλείσιμο μενού' : 'Άνοιγμα μενού');
    };
    burger.addEventListener('click', function () {
      setOpen(burger.getAttribute('aria-expanded') !== 'true');
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && burger.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        burger.focus();
      }
    });
    window.addEventListener('resize', function () {
      if (window.innerWidth > 900) setOpen(false);
    });
  }

  /* ------------------------------- προεπισκόπηση στο ευρετήριο θεραπειών  */
  var preview = document.querySelector('.idx__preview');
  if (preview && window.matchMedia('(min-width: 1081px)').matches) {
    var slides = {};
    Array.prototype.forEach.call(preview.querySelectorAll('img'), function (img) {
      slides[img.dataset.key] = img;
    });
    var current = preview.querySelector('img.is-on');
    var show = function (key) {
      var next = slides[key];
      if (!next || next === current) return;
      if (current) current.classList.remove('is-on');
      next.classList.add('is-on');
      current = next;
    };
    Array.prototype.forEach.call(document.querySelectorAll('.row[data-key]'), function (row) {
      row.addEventListener('mouseenter', function () { show(row.dataset.key); });
      row.addEventListener('focus', function () { show(row.dataset.key); });
    });
  }

})();
