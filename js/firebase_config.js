// Firebase Configuration
// Using compat libraries (v8 syntax) to match the HTML script tags in the project
// If you switch to modules, you'll need a bundler (Vite/Webpack).
// For this vanilla setup, we use the global 'firebase' object.

const firebaseConfig = {
    apiKey: "AIzaSyAE_gVH5df3GNZzamxKTTA5VhADSVo7Rv8",
    authDomain: "nilus-lab.firebaseapp.com",
    projectId: "nilus-lab",
    storageBucket: "nilus-lab.firebasestorage.app",
    messagingSenderId: "848627146995",
    appId: "1:848627146995:web:eb962314ffbcf8c030d786",
    measurementId: "G-PWJHZVSR04"
};

// Initialize Firebase
if (typeof firebase !== 'undefined' && firebase.apps.length === 0) {
    firebase.initializeApp(firebaseConfig);

    // Check if analytics is available (optional safety)
    if (firebase.analytics) {
        firebase.analytics();
    }
} else {
    // Basic fallback if loaded as a module (though our HTML uses CDN globals)
    // console.log("Firebase Global checks or init waiting.");
}

// Export auth instance for potential module usage, 
// though global 'firebase.auth()' is better for our vanilla scripts.
// We assign it to a global variable for convenience in our other scripts.
const auth = firebase.auth();
