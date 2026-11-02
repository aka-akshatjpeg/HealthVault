import { initializeApp } from 'https://www.gstatic.com/firebasejs/13.1.0/firebase-app.js';
import {
  getAuth, GoogleAuthProvider, OAuthProvider, RecaptchaVerifier,
  setPersistence, browserLocalPersistence, signInWithPopup, signInWithPhoneNumber,
} from 'https://www.gstatic.com/firebasejs/13.1.0/firebase-auth.js';

const root = document.getElementById('firebase-auth');
if (root) {
  const status = document.getElementById('firebase-auth-status');
  const googleButton = document.getElementById('firebase-google');
  const appleButton = document.getElementById('firebase-apple');
  const phoneToggle = document.getElementById('firebase-phone-toggle');
  const phonePanel = document.getElementById('firebase-phone-panel');
  const codePanel = document.getElementById('firebase-code-panel');
  const profilePanel = document.getElementById('firebase-profile-panel');
  let auth;
  let verifier;
  let confirmation;
  let pendingUser;

  const showStatus = (message, kind = 'info') => {
    status.textContent = message;
    status.className = 'auth-alert ' + kind;
    status.hidden = !message;
  };

  try {
    const config = JSON.parse(root.dataset.firebaseConfig || '{}');
    if (!config.apiKey || !config.authDomain || !config.projectId || !config.appId) {
      throw new Error('Add the Firebase web app settings to backend/.env before using Firebase sign-in.');
    }
    auth = getAuth(initializeApp(config));
    auth.languageCode = navigator.language || 'en';
    setPersistence(auth, browserLocalPersistence).catch(() => {});
  } catch (error) {
    googleButton.disabled = true;
    appleButton.disabled = true;
    phoneToggle.disabled = true;
    showStatus(error.message || 'Firebase web sign-in is not configured.', 'warning');
  }

  const sendToHealthVault = async (user, profile = {}) => {
    const idToken = await user.getIdToken(true);
    const response = await fetch('/firebase-login', {
      method: 'POST', credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id_token: idToken, ...profile }),
    });
    const data = await response.json().catch(() => ({}));
    if (response.status === 422 && data.error === 'profile_required') {
      pendingUser = user;
      document.getElementById('firebase-full-name').value = user.displayName || '';
      profilePanel.hidden = false;
      showStatus('Add your name to finish creating your patient account.');
      return;
    }
    if (!response.ok) throw new Error(data.error || 'Unable to connect this Firebase account to HealthVault.');
    window.location.assign(data.redirect_url);
  };

  if (auth) {
    googleButton.addEventListener('click', async () => {
      try {
        showStatus('Opening Google sign-in…');
        await sendToHealthVault((await signInWithPopup(auth, new GoogleAuthProvider())).user);
      } catch (error) { showStatus(error.message || 'Google sign-in failed.', 'danger'); }
    });
    appleButton.addEventListener('click', async () => {
      try {
        showStatus('Opening Apple sign-in…');
        const provider = new OAuthProvider('apple.com');
        provider.addScope('email');
        provider.addScope('name');
        await sendToHealthVault((await signInWithPopup(auth, provider)).user);
      } catch (error) { showStatus(error.message || 'Apple sign-in failed.', 'danger'); }
    });
    phoneToggle.addEventListener('click', () => {
      phonePanel.hidden = !phonePanel.hidden;
      if (!phonePanel.hidden) showStatus('Use international format, such as +91 98765 43210. SMS rates may apply.');
    });
    document.getElementById('firebase-send-code').addEventListener('click', async () => {
      try {
        const phone = document.getElementById('firebase-phone').value.trim().replace(/[\s()-]/g, '');
        if (!/^\+[1-9]\d{7,14}$/.test(phone)) throw new Error('Enter a valid phone number with its country code.');
        if (!verifier) {
          verifier = new RecaptchaVerifier(auth, 'firebase-recaptcha', { size: 'normal' });
          await verifier.render();
        }
        confirmation = await signInWithPhoneNumber(auth, phone, verifier);
        codePanel.hidden = false;
        showStatus('Verification code sent. Check your phone.');
      } catch (error) {
        if (verifier) { verifier.clear(); verifier = null; }
        showStatus(error.message || 'Could not send the verification code.', 'danger');
      }
    });
    document.getElementById('firebase-verify-code').addEventListener('click', async () => {
      try {
        if (!confirmation) throw new Error('Request a verification code first.');
        const result = await confirmation.confirm(document.getElementById('firebase-code').value.trim());
        await sendToHealthVault(result.user);
      } catch (error) { showStatus(error.message || 'The verification code is invalid.', 'danger'); }
    });
    document.getElementById('firebase-complete-profile').addEventListener('click', async () => {
      try {
        if (!pendingUser) throw new Error('Please sign in again to complete your profile.');
        await sendToHealthVault(pendingUser, {
          full_name: document.getElementById('firebase-full-name').value.trim(),
        });
      } catch (error) { showStatus(error.message || 'Could not complete your profile.', 'danger'); }
    });
  }
}
