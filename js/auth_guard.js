// auth_guard.js - Protects the main application
// Supports both real Firebase login and demo bypass mode

auth.onAuthStateChanged(user => {
    const isDemo = localStorage.getItem('ZENITH_DEMO_BYPASS') === 'true';

    if (!user && !isDemo) {
        // No user is signed in and no demo bypass — redirect to profile page
        console.warn("Unauthorized access. Redirecting to institutional profile...");
        window.location.href = "index.html";
    } else if (user) {
        // Real Firebase authenticated user
        console.log("Authenticated Researcher:", user.email);
        const userDisplay = document.getElementById('user-display');
        const userDisplayFull = document.getElementById('user-display-full');
        if (userDisplay) {
            const name = user.email.split('@')[0];
            userDisplay.innerText = name.charAt(0).toUpperCase() + name.slice(1);
        }
        if (userDisplayFull) {
            userDisplayFull.innerText = user.email;
        }
    } else {
        // Demo bypass active — institutional access granted without Firebase
        console.log("Demo bypass active — institutional access granted.");
        const userDisplay = document.getElementById('user-display');
        if (userDisplay) userDisplay.innerText = "Researcher";
    }
});

// Logout Function
function performLogout() {
    auth.signOut().then(() => {
        localStorage.removeItem('ZENITH_DEMO_BYPASS');
        console.log("Signed out successfully");
        window.location.href = "index.html";
    }).catch((error) => {
        console.error("Sign out error", error);
    });
}
