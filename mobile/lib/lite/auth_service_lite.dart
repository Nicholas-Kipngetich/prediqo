import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/app_config.dart';
import '../data/models.dart';

/// Lite auth shim for local testing.
///
/// Uses the backend's development email/password endpoints instead of Firebase
/// native plugins. Tokens are signed by the backend and attached to API calls.
class AuthService {
  AuthService();

  String? _token;

  late final Dio _dio = Dio(
    BaseOptions(
      baseUrl: apiBaseUrl,
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 8),
    ),
  );

  Stream<Object?> authStateChanges() => const Stream.empty();

  Object? get currentUser => null;

  bool get isSignedIn => _token != null;

  Future<String?> idToken() async => _token;

  Future<void> registerWithEmail(String email, String password) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/register',
      data: {'email': email.trim(), 'password': password},
    );
    final result = AuthResultModel.fromJson(response.data ?? {});
    _token = result.accessToken;
  }

  Future<void> signInWithEmail(String email, String password) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/login',
      data: {'email': email.trim(), 'password': password},
    );
    final result = AuthResultModel.fromJson(response.data ?? {});
    _token = result.accessToken;
  }

  Future<void> sendPasswordReset(String email) async {
    // Not available in dev auth mode.
  }

  Future<Object?> signInWithGoogle() async => null;

  Future<void> signOut() async {
    _token = null;
  }

  Future<void> deleteAccount() async {
    if (_token == null) return;
    await _dio.delete<void>(
      '/api/v1/users/me',
      options: Options(
        headers: {'Authorization': 'Bearer $_token'},
      ),
    );
    _token = null;
  }
}

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});
