// Theme toggle, image lightbox, and one-video-at-a-time playback.

(function () {
  'use strict';

  /* ── Theme ─────────────────────────────────────────────────── */

  var root = document.documentElement;
  var toggle = document.getElementById('theme-toggle');
  var stored = null;

  try { stored = localStorage.getItem('theme'); } catch (e) { /* private mode */ }
  if (stored) root.setAttribute('data-theme', stored);

  function currentlyDark() {
    var set = root.getAttribute('data-theme');
    if (set) return set === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }

  function paintToggle() {
    toggle.textContent = currentlyDark() ? '☀' : '☾';
  }

  toggle.addEventListener('click', function () {
    var next = currentlyDark() ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('theme', next); } catch (e) { /* ignore */ }
    paintToggle();
  });

  paintToggle();

  /* ── Lightbox ──────────────────────────────────────────────── */

  var box = document.getElementById('lightbox');
  var boxImg = document.getElementById('lightbox-img');
  var lastOpener = null;

  function openLightbox(img) {
    boxImg.src = img.dataset.full || img.src;
    boxImg.alt = img.alt;
    box.hidden = false;
    document.body.style.overflow = 'hidden';
    document.getElementById('lightbox-close').focus();
  }

  function closeLightbox() {
    box.hidden = true;
    boxImg.src = '';
    document.body.style.overflow = '';
    if (lastOpener) lastOpener.focus();
  }

  document.querySelectorAll('.lightbox-open').forEach(function (button) {
    button.addEventListener('click', function () {
      lastOpener = button;
      openLightbox(button.querySelector('img'));
    });
  });

  box.addEventListener('click', closeLightbox);

  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && !box.hidden) closeLightbox();
  });

  /* ── Video ─────────────────────────────────────────────────── */

  // Several clips on screen at once gets noisy, so starting one stops the rest.
  var videos = Array.prototype.slice.call(document.querySelectorAll('video'));

  videos.forEach(function (video) {
    video.addEventListener('play', function () {
      videos.forEach(function (other) {
        if (other !== video && !other.paused) other.pause();
      });
    });
  });
}());
