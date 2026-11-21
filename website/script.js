const header = document.querySelector("[data-header]");
const nav = document.querySelector(".site-nav");
const toggle = document.querySelector(".nav-toggle");
const contactForm = document.querySelector("[data-contact-form]");
const formStatus = document.querySelector("[data-form-status]");
const submitButton = document.querySelector("[data-submit-button]");
const formStartedAt = document.querySelector("[data-form-started-at]");

const updateHeader = () => {
  header.classList.toggle("is-scrolled", window.scrollY > 20);
};

toggle.addEventListener("click", () => {
  const isOpen = nav.classList.toggle("is-open");
  toggle.setAttribute("aria-expanded", String(isOpen));
  toggle.setAttribute("aria-label", isOpen ? "Menü schliessen" : "Menü öffnen");
});

nav.addEventListener("click", (event) => {
  if (event.target instanceof HTMLAnchorElement) {
    nav.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "Menü öffnen");
  }
});

updateHeader();
window.addEventListener("scroll", updateHeader, { passive: true });

const params = new URLSearchParams(window.location.search);

const showFormStatus = (state, html, focus = false) => {
  if (!formStatus) return;
  formStatus.hidden = false;
  formStatus.dataset.state = state;
  formStatus.innerHTML = html;
  if (focus) {
    formStatus.focus({ preventScroll: true });
    formStatus.scrollIntoView({ block: "center", behavior: "instant" });
  }
};

if (formStatus && params.get("sent") === "1") {
  showFormStatus("success", '<strong>Vielen Dank! Ihre Anfrage wurde gesendet.</strong><span>Der Mailserver hat Ihre Nachricht zum Versand angenommen.</span>');
}

if (formStatus && params.get("sent") === "0") {
  showFormStatus("error", '<strong>Ihre Anfrage konnte nicht gesendet werden.</strong><span>Bitte versuchen Sie es erneut oder schreiben Sie an <a href="mailto:hello@digitalheat.ch">hello@digitalheat.ch</a>.</span>');
}

if (formStatus && ["0", "1"].includes(params.get("sent"))) {
  window.addEventListener("load", () => {
    formStatus.focus({ preventScroll: true });
    formStatus.scrollIntoView({ block: "center", behavior: "instant" });
  }, { once: true });
}

const markFormStarted = () => {
  if (formStartedAt instanceof HTMLInputElement && formStartedAt.value === "") {
    formStartedAt.value = String(Date.now());
  }
};

contactForm?.addEventListener("focusin", markFormStarted);
contactForm?.addEventListener("input", markFormStarted);

contactForm?.addEventListener("submit", (event) => {
  markFormStarted();

  if (window.location.protocol === "file:") {
    event.preventDefault();
    showFormStatus("error", '<strong>Die Nachricht wurde nicht gesendet.</strong><span>Der Versand funktioniert nur auf der gehosteten Website. Schreiben Sie direkt an <a href="mailto:hello@digitalheat.ch">hello@digitalheat.ch</a>.</span>', true);
    return;
  }

  if (submitButton instanceof HTMLButtonElement) {
    submitButton.disabled = true;
    submitButton.textContent = "Wird gesendet...";
  }

  showFormStatus("pending", '<strong>Ihre Anfrage wird gesendet...</strong>', true);
});
