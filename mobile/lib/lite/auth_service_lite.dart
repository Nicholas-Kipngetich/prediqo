import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/app_config.dart';

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

  Future<String> register({
    String? email,
    String? phone,
    required String password,
    String? displayName,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/register',
      data: {
        if (email != null) 'email': email.trim(),
        if (phone != null) 'phone': phone.trim(),
        'password': password,
        'confirm_password': password,
        if (displayName != null) 'display_name': displayName,
      },
    );
    _token = response.data?['access_token'] as String?;
    final code = response.data?['verification_code'] as String?;
    return code ?? '';
  }

  Future<String> verifyCode({
    String? email,
    String? phone,
    required String code,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/verify-code',
      data: {
        if (email != null) 'email': email.trim(),
        if (phone != null) 'phone': phone.trim(),
        'code': code.trim(),
      },
    );
    _token = response.data?['access_token'] as String?;
    return _token ?? '';
  }

  Future<String> login({
    String? email,
    String? phone,
    required String password,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/login',
      data: {
        if (email != null) 'email': email.trim(),
        if (phone != null) 'phone': phone.trim(),
        'password': password,
      },
    );
    _token = response.data?['access_token'] as String?;
    return _token ?? '';
  }

  Future<void> sendPasswordReset(String email) async {}

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
