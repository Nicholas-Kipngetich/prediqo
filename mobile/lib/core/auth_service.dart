import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

class AuthService {
  FirebaseAuth get _auth => FirebaseAuth.instance;

  Future<void> init() async {}

  Stream<User?> authStateChanges() => _auth.authStateChanges();

  User? get currentUser => _auth.currentUser;

  bool get isSignedIn => currentUser != null;

  Future<String> register({
    String? email,
    String? phone,
    required String password,
    String? displayName,
  }) async {
    // Full Firebase registration is completed in a later pass. The development
    // build uses the backend dev-auth endpoints instead of Firebase.
    throw UnimplementedError('Firebase registration is not wired in this build.');
  }

  Future<String> login({
    String? email,
    String? phone,
    required String password,
  }) async {
    throw UnimplementedError('Firebase login is not wired in this build.');
  }

  Future<String> verifyCode({
    String? email,
    String? phone,
    required String code,
  }) async {
    throw UnimplementedError('Firebase verification is not wired in this build.');
  }

  Future<UserCredential> registerWithEmail(String email, String password) {
    return _auth.createUserWithEmailAndPassword(
      email: email.trim(),
      password: password,
    );
  }

  Future<UserCredential> signInWithEmail(String email, String password) {
    return _auth.signInWithEmailAndPassword(
      email: email.trim(),
      password: password,
    );
  }

  Future<void> sendPasswordReset(String email) {
    return _auth.sendPasswordResetEmail(email: email.trim());
  }

  Future<UserCredential?> signInWithGoogle() async {
    final GoogleSignInAccount? account = await GoogleSignIn().signIn();
    if (account == null) return null;
    final GoogleSignInAuthentication auth = await account.authentication;
    final OAuthCredential credential = GoogleAuthProvider.credential(
      idToken: auth.idToken,
      accessToken: auth.accessToken,
    );
    return _auth.signInWithCredential(credential);
  }

  Future<String?> idToken() async {
    final user = _auth.currentUser;
    if (user == null) return null;
    return user.getIdToken();
  }

  Future<void> signOut() async {
    await GoogleSignIn().signOut();
    await _auth.signOut();
  }

  Future<void> deleteAccount() async {
    final User? user = _auth.currentUser;
    if (user == null) return;
    await user.delete();
  }
}

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});
