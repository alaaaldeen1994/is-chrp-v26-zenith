// auth_guard.js - Protects the main application

// Monitor Auth State
// We expect firebase to be initialized in firebase_config.js which must be loaded before this.

auth.onAuthStateChanged(user => {
    if (!user) {
        // No user is signed in, redirect to profile landing page instead of login.html
        console.warn("Unauthorized access. Redirecting to institutional profile...");
        window.location.href = "profile.html";
    } else {
        console.log("Authenticated Researcher:", user.email);
        // Optional: Update UI with user info
        const userDisplay = document.getElementById('user-display');
        const userDisplayFull = document.getElementById('user-display-full');
        if (userDisplay) {
            // Display only name part (capitalize first letter)
            const name = user.email.split('@')[0];
            userDisplay.innerText = name.charAt(0).toUpperCase() + name.slice(1);
        }
        if (userDisplayFull) {
            userDisplayFull.innerText = user.email;
        }
    }
});

// Logout Function
function performLogout() {
    auth.signOut().then(() => {
        console.log("Signed out successfully");
        // Redirect to profile page after logout
        window.location.href = "profile.html";
    }).catch((error) => {
        console.error("Sign out error", error);
    });
}

