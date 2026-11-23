import 'package:firebase_core/firebase_core.dart';

/// Placeholder Firebase configuration for local development and CI.
///
/// Replace these values with the ones from your Firebase project's
/// google-services.json before production. These IDs are not secrets, but they
/// must point to a real project for sign-in to work.
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform => android;

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyPLACEHOLDER_REPLACE_WITH_REAL_KEY',
    appId: '1:123456789012:android:0123456789abcdef012345',
    messagingSenderId: '123456789012',
    projectId: 'prediqo-placeholder',
    storageBucket: 'prediqo-placeholder.appspot.com',
  );
}
