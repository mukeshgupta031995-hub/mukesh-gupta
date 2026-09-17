/**
 * Mukesh Gupta - Executive Retail Leadership Portfolio
 * Interactive Client Script
 */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  // --- 1. Dynamic Year ---
  const currentYearEl = document.getElementById('currentYear');
  if (currentYearEl) {
    currentYearEl.textContent = new Date().getFullYear();
  }

  // --- 2. Header Scroll Effect & Back-to-Top ---
  const siteHeader = document.getElementById('site-header');
  const backToTopBtn = document.getElementById('backToTopBtn');

  function handleScroll() {
    const scrollY = window.scrollY || window.pageYOffset;

    if (siteHeader) {
      if (scrollY > 20) {
        siteHeader.classList.add('scrolled');
      } else {
        siteHeader.classList.remove('scrolled');
      }
    }

    if (backToTopBtn) {
      if (scrollY > 400) {
        backToTopBtn.classList.add('is-active');
      } else {
        backToTopBtn.classList.remove('is-active');
      }
    }
  }

  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();

  if (backToTopBtn) {
    backToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // --- Focus Trap Helper ---
  let activeOverlay = null;
  let previousActiveElement = null;

  function trapFocus(element) {
    previousActiveElement = document.activeElement;
    activeOverlay = element;

    const focusableSelectors = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';
    const focusableElements = element.querySelectorAll(focusableSelectors);
    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
  }

  function releaseFocus() {
    activeOverlay = null;
    if (previousActiveElement && typeof previousActiveElement.focus === 'function') {
      previousActiveElement.focus();
      previousActiveElement = null;
    }
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Tab' && activeOverlay) {
      const focusableSelectors = 'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';
      const focusableElements = Array.from(activeOverlay.querySelectorAll(focusableSelectors)).filter(
        el => el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0
      );

      if (focusableElements.length === 0) {
        e.preventDefault();
        return;
      }

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === firstElement || !activeOverlay.contains(document.activeElement)) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement || !activeOverlay.contains(document.activeElement)) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    }
  });

  // --- 3. Mobile Navigation Drawer ---
  const mobileMenuToggle = document.getElementById('mobileMenuToggle');
  const closeDrawerBtn = document.getElementById('closeDrawerBtn');
  const mobileDrawer = document.getElementById('mobileDrawer');
  const drawerOverlay = document.getElementById('drawerOverlay');
  const drawerLinks = document.querySelectorAll('.drawer-nav-link');

  function openDrawer() {
    if (!mobileDrawer || !drawerOverlay) return;
    mobileDrawer.classList.add('is-open');
    mobileDrawer.setAttribute('aria-hidden', 'false');
    drawerOverlay.classList.add('is-visible');
    drawerOverlay.setAttribute('aria-hidden', 'false');
    if (mobileMenuToggle) {
      mobileMenuToggle.classList.add('is-active');
      mobileMenuToggle.setAttribute('aria-expanded', 'true');
    }
    document.body.style.overflow = 'hidden';
    trapFocus(mobileDrawer);
  }

  function closeDrawer() {
    if (!mobileDrawer || !drawerOverlay) return;
    mobileDrawer.classList.remove('is-open');
    mobileDrawer.setAttribute('aria-hidden', 'true');
    drawerOverlay.classList.remove('is-visible');
    drawerOverlay.setAttribute('aria-hidden', 'true');
    if (mobileMenuToggle) {
      mobileMenuToggle.classList.remove('is-active');
      mobileMenuToggle.setAttribute('aria-expanded', 'false');
    }
    document.body.style.overflow = '';
    releaseFocus();
  }

  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', () => {
      const isOpen = mobileDrawer && mobileDrawer.classList.contains('is-open');
      if (isOpen) {
        closeDrawer();
      } else {
        openDrawer();
      }
    });
  }

  if (closeDrawerBtn) {
    closeDrawerBtn.addEventListener('click', closeDrawer);
  }

  if (drawerOverlay) {
    drawerOverlay.addEventListener('click', closeDrawer);
  }

  drawerLinks.forEach(link => {
    link.addEventListener('click', () => {
      closeDrawer();
    });
  });

  // --- 4. Smooth Anchor Navigation with Fixed Header Offset ---
  const headerHeight = 70;
  const allAnchorLinks = document.querySelectorAll('a[href^="#"]');

  allAnchorLinks.forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (!targetId || targetId === '#') return;

      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        const elementPosition = targetEl.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerHeight;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });

        // Update focus for accessibility
        targetEl.setAttribute('tabindex', '-1');
        targetEl.focus({ preventScroll: true });
      }
    });
  });

  // --- 5. Scrollspy for Active Section Links ---
  const sections = document.querySelectorAll('section[id]');
  const desktopNavLinks = document.querySelectorAll('.desktop-nav .nav-link');

  function updateActiveNavOnScroll() {
    const scrollPos = window.pageYOffset + headerHeight + 50;

    sections.forEach(sec => {
      const top = sec.offsetTop;
      const height = sec.offsetHeight;
      const id = sec.getAttribute('id');

      if (scrollPos >= top && scrollPos < top + height) {
        desktopNavLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${id}`) {
            link.classList.add('active');
          }
        });
      }
    });
  }

  window.addEventListener('scroll', updateActiveNavOnScroll, { passive: true });

  // --- 6. Core Competencies Category Filter ---
  const filterPills = document.querySelectorAll('.filter-pill');
  const skillCards = document.querySelectorAll('.skill-category-card');

  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => {
        p.classList.remove('active');
        p.setAttribute('aria-selected', 'false');
      });
      pill.classList.add('active');
      pill.setAttribute('aria-selected', 'true');

      const filter = pill.getAttribute('data-filter');

      skillCards.forEach(card => {
        const category = card.getAttribute('data-category');
        if (filter === 'all' || category === filter) {
          card.classList.remove('hidden');
        } else {
          card.classList.add('hidden');
        }
      });
    });
  });

  // --- 7. Executive CV Modal ---
  const cvModal = document.getElementById('cvModal');
  const openCvModalBtn = document.getElementById('openCvModalBtn');
  const heroCvBtn = document.getElementById('heroCvBtn');
  const closeCvModalBtn = document.getElementById('closeCvModalBtn');

  function openModal() {
    if (!cvModal) return;
    cvModal.classList.add('is-open');
    cvModal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    trapFocus(cvModal);
  }

  function closeModal() {
    if (!cvModal) return;
    cvModal.classList.remove('is-open');
    cvModal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    releaseFocus();
  }

  if (openCvModalBtn) openCvModalBtn.addEventListener('click', openModal);
  if (heroCvBtn) heroCvBtn.addEventListener('click', openModal);
  if (closeCvModalBtn) closeCvModalBtn.addEventListener('click', closeModal);

  if (cvModal) {
    cvModal.addEventListener('click', (e) => {
      if (e.target === cvModal) {
        closeModal();
      }
    });
  }

  // Close with Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
      closeDrawer();
    }
  });

  // --- 8. Contact Form Validation & AJAX Submission ---
  const contactForm = document.getElementById('leadershipContactForm');
  const formAlert = document.getElementById('formAlert');
  const submitBtn = document.getElementById('submitInquiryBtn');
  const btnSpinner = document.getElementById('btnSpinner');
  const btnIcon = document.getElementById('btnIcon');
  const btnText = document.getElementById('btnText');

  // Input elements
  const inputName = document.getElementById('contactName');
  const inputEmail = document.getElementById('contactEmail');
  const inputPhone = document.getElementById('contactPhone');
  const inputMessage = document.getElementById('contactMessage');
  const inputOrg = document.getElementById('contactOrg');
  const inputRole = document.getElementById('contactRoleType');

  // Error message labels
  const errorName = document.getElementById('error-name');
  const errorEmail = document.getElementById('error-email');
  const errorPhone = document.getElementById('error-phone');
  const errorMessage = document.getElementById('error-message');

  function clearErrors() {
    [errorName, errorEmail, errorPhone, errorMessage].forEach(el => {
      if (el) el.textContent = '';
    });
    document.querySelectorAll('.form-group').forEach(group => {
      group.classList.remove('has-error');
    });
    if (formAlert) {
      formAlert.className = 'form-alert hidden';
      formAlert.innerHTML = '';
    }
  }

  function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
  }

  function validatePhone(phone) {
    if (!phone) return true; // optional
    const clean = phone.replace(/[\s\-\(\)\+]/g, '');
    return clean.length >= 7 && /^\d+$/.test(clean);
  }

  if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearErrors();

      let hasError = false;

      // Validate Name
      const nameVal = (inputName ? inputName.value : '').trim();
      if (!nameVal || nameVal.length < 2) {
        if (errorName) errorName.textContent = 'Please enter your full name.';
        document.getElementById('group-name')?.classList.add('has-error');
        hasError = true;
      }

      // Validate Email
      const emailVal = (inputEmail ? inputEmail.value : '').trim();
      if (!emailVal || !validateEmail(emailVal)) {
        if (errorEmail) errorEmail.textContent = 'Please enter a valid email address.';
        document.getElementById('group-email')?.classList.add('has-error');
        hasError = true;
      }

      // Validate Phone (optional but must be valid if provided)
      const phoneVal = (inputPhone ? inputPhone.value : '').trim();
      if (phoneVal && !validatePhone(phoneVal)) {
        if (errorPhone) errorPhone.textContent = 'Please enter a valid phone number (at least 7 digits).';
        document.getElementById('group-phone')?.classList.add('has-error');
        hasError = true;
      }

      // Validate Message
      const messageVal = (inputMessage ? inputMessage.value : '').trim();
      if (!messageVal || messageVal.length < 5) {
        if (errorMessage) errorMessage.textContent = 'Please write a message (at least 5 characters).';
        document.getElementById('group-message')?.classList.add('has-error');
        hasError = true;
      }

      if (hasError) {
        if (formAlert) {
          formAlert.className = 'form-alert alert-error';
          formAlert.textContent = 'Please correct the highlighted fields and submit again.';
        }
        return;
      }

      // Submitting State
      if (submitBtn) submitBtn.disabled = true;
      if (btnSpinner) btnSpinner.classList.remove('hidden');
      if (btnIcon) btnIcon.classList.add('hidden');
      if (btnText) btnText.textContent = 'Sending Inquiry...';

      const payload = {
        name: nameVal,
        email: emailVal,
        phone: phoneVal,
        organization: inputOrg ? inputOrg.value.trim() : '',
        role_type: inputRole ? inputRole.value : '',
        message: messageVal
      };

      try {
        const response = await fetch('/api/contact', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok && data.success) {
          if (formAlert) {
            formAlert.className = 'form-alert alert-success';
            formAlert.innerHTML = `
              <strong>Inquiry Received!</strong> ${data.message}
              <div style="margin-top: 0.5rem; font-size: 13px;">
                Alternatively, you can also <a href="${data.mailto_fallback}" style="color: inherit; text-decoration: underline; font-weight: 700;">click here to send a pre-filled email directly</a>.
              </div>
            `;
          }
          contactForm.reset();
        } else {
          if (formAlert) {
            formAlert.className = 'form-alert alert-error';
            const fallbackLink = data.mailto_fallback 
              ? `<div style="margin-top: 0.5rem; font-size: 13px;">Alternatively, you can <a href="${data.mailto_fallback}" style="color: inherit; text-decoration: underline; font-weight: 700;">click here to send a pre-filled email directly</a> or contact directly.</div>`
              : '';
            formAlert.innerHTML = `<strong>Delivery Issue:</strong> ${data.message || 'There was an issue processing your inquiry. Please try again or call directly.'}${fallbackLink}`;
          }
          if (data.errors) {
            Object.keys(data.errors).forEach(field => {
              const errLabel = document.getElementById(`error-${field}`);
              if (errLabel) errLabel.textContent = data.errors[field];
              document.getElementById(`group-${field}`)?.classList.add('has-error');
            });
          }
        }
      } catch (err) {
        if (formAlert) {
          formAlert.className = 'form-alert alert-error';
          formAlert.innerHTML = `
            Could not connect to server. You can reach Mukesh Gupta directly via 
            <a href="mailto:mgsmukeshgupta@gmail.com" style="color: inherit; text-decoration: underline; font-weight: 700;">email</a> 
            or <a href="tel:+917016498175" style="color: inherit; text-decoration: underline; font-weight: 700;">phone (+91 7016498175)</a>.
          `;
        }
      } finally {
        if (submitBtn) submitBtn.disabled = false;
        if (btnSpinner) btnSpinner.classList.add('hidden');
        if (btnIcon) btnIcon.classList.remove('hidden');
        if (btnText) btnText.textContent = 'Submit Leadership Inquiry';
      }
    });
  }
});
