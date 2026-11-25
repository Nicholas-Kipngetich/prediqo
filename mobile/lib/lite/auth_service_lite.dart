import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/app_config.dart';

class AuthService {
  AuthService();

  static const _tokenKey = 'prediqo_dev_token';

  String? _token;

  Future<void> init() async {
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(_tokenKey);
  }

  Future<void> _persist() async {
    final prefs = await SharedPreferences.getInstance();
    if (_token == null) {
      await prefs.remove(_tokenKey);
    } else {
      await prefs.setString(_tokenKey, _token!);
    }
  }

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
    await _persist();
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
    await _persist();
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
    await _persist();
    return _token ?? '';
  }

  Future<String> requestPasswordReset({String? email, String? phone}) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/forgot-password',
      data: {
        if (email != null) 'email': email.trim(),
        if (phone != null) 'phone': phone.trim(),
      },
    );
    return response.data?['verification_code'] as String? ?? '';
  }

  Future<void> resetPassword({
    String? email,
    String? phone,
    required String code,
    required String newPassword,
  }) async {
    await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/reset-password',
      data: {
        if (email != null) 'email': email.trim(),
        if (phone != null) 'phone': phone.trim(),
        'code': code.trim(),
        'new_password': newPassword,
      },
    );
  }

  Future<void> sendPasswordReset(String email) async {}

  Future<Object?> signInWithGoogle() async => null;

  Future<void> signOut() async {
    _token = null;
    await _persist();
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
    await _persist();
  }
}

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});
