import 'package:firebase_core/firebase_core.dart';

/// Firebase configuration for Prediqo project (prediqo-1035a).
/// Values from google-services.json.
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform => android;

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyBXrxSB7V_WTpcx0iXhloDD85zFC7dzB9Q',
    appId: '1:295910631373:android:7a522e8b1498e90a858684',
    messagingSenderId: '295910631373',
    projectId: 'prediqo-1035a',
    storageBucket: 'prediqo-1035a.firebasestorage.app',
  );
}
