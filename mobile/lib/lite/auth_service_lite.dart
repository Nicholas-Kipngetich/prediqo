import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Lite auth shim for local testing without Firebase native plugins.
/// All API calls use the dev token via the Dio interceptor.
class AuthService {
  Stream<Object?> authStateChanges() => const Stream.empty();

  Object? get currentUser => null;

  bool get isSignedIn => true;

  Future<Object> registerWithEmail(String email, String password) async {
    throw UnimplementedError('Use the dev token in lite builds.');
  }

  Future<Object> signInWithEmail(String email, String password) async {
    throw UnimplementedError('Use the dev token in lite builds.');
  }

  Future<void> sendPasswordReset(String email) async {}

  Future<Object?> signInWithGoogle() async => null;

  Future<String?> idToken() async => null;

  Future<void> signOut() async {}

  Future<void> deleteAccount() async {}
}

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});
