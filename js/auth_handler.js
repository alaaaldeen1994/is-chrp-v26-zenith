// auth_handler.js

// State
let isLoginMode = true;

// UI Elements
const form = document.getElementById('auth-form');
const submitBtn = document.getElementById('submit-btn');
const toggleLink = document.getElementById('toggle-link');
const errorMsg = document.getElementById('error-msg');
const errorText = document.getElementById('error-text');
const confirmPassContainer = document.getElementById('confirm-pass-container');

// Toggle between Login and Register
function toggleMode() {
    isLoginMode = !isLoginMode;
    const title = document.querySelector('h3');
    const subtitle = document.querySelector('p.text-slate-400');
    const btnText = submitBtn.querySelector('span');

    if (isLoginMode) {
        title.innerText = "Welcome Back";
        subtitle.innerText = "Sign in to access your simulation dashboard.";
        btnText.innerText = "Sign In";
        toggleLink.innerText = "Create Account";
        submitBtn.classList.replace('bg-slate-900', 'bg-slate-900');
        submitBtn.classList.replace('hover:bg-slate-800', 'hover:bg-slate-800');
        submitBtn.classList.replace('shadow-slate-900/20', 'shadow-slate-900/20');
        confirmPassContainer.classList.add('hidden');
        document.getElementById('confirm-password').removeAttribute('required');
    } else {
        title.innerText = "Create Account";
        subtitle.innerText = "Join Nilus Lab secure platform.";
        btnText.innerText = "Sign Up";
        toggleLink.innerText = "Back to Login";
        // Change button color to indicate creation
        submitBtn.classList.replace('bg-slate-900', 'bg-slate-900');
        submitBtn.classList.replace('hover:bg-slate-800', 'hover:bg-slate-800');
        submitBtn.classList.replace('shadow-slate-900/20', 'shadow-slate-900/20');
        confirmPassContainer.classList.remove('hidden');
        document.getElementById('confirm-password').setAttribute('required', 'true');

    }

    // Clear errors
    errorMsg.classList.add('hidden');
}

// Handle Form Submission
async function handleAuth(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    if (!isLoginMode) {
        const confirmPassword = document.getElementById('confirm-password').value;
        if (password !== confirmPassword) {
            errorText.innerText = "Passwords do not match.";
            errorMsg.classList.remove('hidden');
            return;
        }
    }

    // Loading State
    const originalBtnContent = submitBtn.innerHTML;
    submitBtn.innerHTML = `<i class="animate-spin w-5 h-5" data-lucide="loader-2"></i> PROCESSING...`;
    submitBtn.disabled = true;
    lucide.createIcons();
    errorMsg.classList.add('hidden');

    try {
        if (isLoginMode) {
            // Sign In
            await auth.signInWithEmailAndPassword(email, password);
        } else {
            // Sign Up
            await auth.createUserWithEmailAndPassword(email, password);
        }

        // Success Animation before Redirect
        submitBtn.innerHTML = `<i data-lucide="check" class="w-5 h-5"></i> ACCESS GRANTED`;
        submitBtn.classList.replace('bg-slate-900', 'bg-slate-800');
        lucide.createIcons();

        setTimeout(() => {
            // Check if there's a redirect URL in the query params
            const urlParams = new URLSearchParams(window.location.search);
            const redirectUrl = urlParams.get('redirect');
            window.location.href = redirectUrl || "index.html"; // Default to simulation
        }, 1000);

    } catch (error) {
        console.error("Auth Error:", error);

        // Reset Button
        submitBtn.innerHTML = originalBtnContent;
        submitBtn.disabled = false;
        lucide.createIcons();

        // Show Error
        errorText.innerText = parseError(error.code);
        errorMsg.classList.remove('hidden');
    }
}

// Helper to make Firebase errors user-friendly
function parseError(code) {
    switch (code) {
        case 'auth/invalid-email': return 'Invalid email address format.';
        case 'auth/user-disabled': return 'This account has been disabled.';
        case 'auth/user-not-found': return 'No account found with these credentials.';
        case 'auth/wrong-password': return 'Incorrect password.';
        case 'auth/email-already-in-use': return 'This email is already registered.';
        case 'auth/weak-password': return 'Password must be at least 6 characters.';
        default: return 'Authentication failed. Please try again.';
    }
}

// Monitor Auth State (Redirect if already logged in)
auth.onAuthStateChanged(user => {
    if (user) {
        // If we are on the login page and user is already logged in, redirect them
        // Check prevents redirect loop if we just signed out
        // For now, we rely on the form submission for the immediate redirect, 
        // but this could auto-login returning users.
        // console.log("User already logged in:", user.email);
    }
});
