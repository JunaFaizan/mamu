/* ================= NAV (mobile) — shared across every page ================= */
function toggleMobileNav(forceClose) {
  const nav = document.getElementById('mobileNav');
  if (!nav) return;
  const open = forceClose === true ? false : !nav.classList.contains('open');
  const backdrop = document.getElementById('mobileNavBackdrop');
  const btn = document.getElementById('mobileMenuBtn');
  nav.classList.toggle('open', open);
  if (backdrop) backdrop.classList.toggle('open', open);
  if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  document.body.classList.toggle('nav-locked', open);
}
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') toggleMobileNav(true);
});

function markActiveNav() {
  const page = document.body.dataset.page;
  document.querySelectorAll('[data-nav]').forEach(el => {
    el.classList.toggle('active', el.dataset.nav === page);
  });
}
document.addEventListener('DOMContentLoaded', markActiveNav);

/* ================= Toast auto-hide (server-rendered messages) ================= */
document.addEventListener('DOMContentLoaded', () => {
  const t = document.getElementById('toast');
  if (t && !t.classList.contains('hidden')) {
    setTimeout(() => t.classList.add('hidden'), 2600);
  }
});
