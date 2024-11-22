// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBYAuhIUbAK7ACty7PdWvHOBbAe4TPDf7g",
  authDomain: "agritest-10701.firebaseapp.com",
  databaseURL: "https://agritest-10701-default-rtdb.firebaseio.com",
  projectId: "agritest-10701",
  storageBucket: "agritest-10701.firebasestorage.app",
  messagingSenderId: "1055187803843",
  appId: "1:1055187803843:web:2886440c136f8e4953cc76",
  measurementId: "G-VWQFRLBGTC"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);