// Theme toggle, image lightbox, and click to play video.

(function () {
  'use strict';

  /* ── Theme ─────────────────────────────────────────────── */

  var root = document.documentElement;
  var toggle = document.getElementById('theme-toggle');
  var stored = null;

  try { stored = localStorage.getItem('theme'); } catch (e) { /* private mode */ }
  if (stored) root.setAttribute('data-theme', stored);

  function isDark() {
    var set = root.getAttribute('data-theme');
    if (set) return set === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function paint() { toggle.textContent = isDark() ? '☀' : '☾'; }

  toggle.addEventListener('click', function () {
    var next = isDark() ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) { /* ignore */ }
    paint();
  });

  paint();

  /* ── Lightbox ──────────────────────────────────────────── */

  var box = document.getElementById('lightbox');
  var boxImg = document.getElementById('lightbox-img');
  var opener = null;

  function open(button) {
    opener = button;
    boxImg.src = button.dataset.full;
    boxImg.alt = button.querySelector('img').alt;
    box.hidden = false;
    document.body.style.overflow = 'hidden';
    document.getElementById('lightbox-close').focus();
  }

  function close() {
    box.hidden = true;
    boxImg.src = '';
    document.body.style.overflow = '';
    if (opener) opener.focus();
  }

  box.addEventListener('click', close);
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && !box.hidden) close();
  });

  /* ── Media ─────────────────────────────────────────────── */

  // Videos sit in the grid as a poster image with a play badge, so a row of
  // them reads as evenly as a row of photos. The real <video> is only built
  // once someone asks for it, which also keeps the page weight down.
  function play(button) {
    var video = document.createElement('video');
    video.src = button.dataset.video;
    video.controls = true;
    video.autoplay = true;
    video.playsInline = true;
    video.loop = true;

    video.addEventListener('play', function () {
      document.querySelectorAll('video').forEach(function (other) {
        if (other !== video && !other.paused) other.pause();
      });
    });

    button.replaceChildren(video);
    button.classList.add('playing');
    button.style.cursor = 'default';
  }

  document.querySelectorAll('.media').forEach(function (button) {
    button.addEventListener('click', function () {
      if (button.classList.contains('playing')) return;
      if (button.dataset.video) play(button);
      else if (button.dataset.full) open(button);
    });
  });
}());
