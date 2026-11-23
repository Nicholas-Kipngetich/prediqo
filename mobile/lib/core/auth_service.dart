import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

class AuthService {
  FirebaseAuth get _auth => FirebaseAuth.instance;

  Stream<User?> authStateChanges() => _auth.authStateChanges();

  User? get currentUser => _auth.currentUser;

  bool get isSignedIn => currentUser != null;

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

  Future<String?> idToken() => _auth.currentUser?.getIdToken();

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
