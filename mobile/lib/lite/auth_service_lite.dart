import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/app_config.dart';

class AuthService {
  AuthService();

  final _auth = FirebaseAuth.instance;
  final _googleSignIn = GoogleSignIn();

  static const _devTokenKey = 'prediqo_dev_token';

  String? _devToken;

  late final Dio _dio = Dio(
    BaseOptions(
      baseUrl: apiBaseUrl,
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 8),
    ),
  );

  Future<void> init() async {
    _devToken = await _getStoredDevToken();
  }

  Future<String?> _getStoredDevToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_devTokenKey);
  }

  Future<void> _storeDevToken(String? token) async {
    final prefs = await SharedPreferences.getInstance();
    if (token == null) {
      await prefs.remove(_devTokenKey);
    } else {
      await prefs.setString(_devTokenKey, token);
    }
  }

  Stream<Object?> authStateChanges() =>
      _auth.authStateChanges().asyncMap((_) => null);

  Object? get currentUser => _auth.currentUser;

  bool get isSignedIn => _auth.currentUser != null && _devToken != null;

  Future<String?> idToken() async => _auth.currentUser?.getIdToken();

  Future<String> register({
    String? email,
    String? phone,
    required String password,
    String? displayName,
  }) async {
    // Create Firebase user first
    try {
      await _auth.createUserWithEmailAndPassword(
        email: email!.trim(),
        password: password,
      );
    } on FirebaseAuthException catch (e) {
      if (e.code == 'email-already-in-use') {
        // Firebase user exists, that's OK — dev backend may or may not have them
      } else {
        rethrow;
      }
    }

    // Call dev backend to register and get verification code
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
    _devToken = response.data?['access_token'] as String?;
    await _storeDevToken(_devToken);
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
    _devToken = response.data?['access_token'] as String?;
    await _storeDevToken(_devToken);
    return _devToken ?? '';
  }

  Future<String> login({
    String? email,
    String? phone,
    required String password,
  }) async {
    // Sign in with Firebase first (for session persistence)
    try {
      await _auth.signInWithEmailAndPassword(
        email: email!.trim(),
        password: password,
      );
    } on FirebaseAuthException {
      // Firebase user may not exist; continue with dev backend login
    }

    // Call dev backend to get dev token for API calls
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/login',
      data: {
        if (email != null) 'email': email.trim(),
        if (phone != null) 'phone': phone.trim(),
        'password': password,
      },
    );
    _devToken = response.data?['access_token'] as String?;
    await _storeDevToken(_devToken);
    return _devToken ?? '';
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
    // Update Firebase password if email-based
    if (email != null) {
      try {
        await _auth.sendPasswordResetEmail(email: email.trim());
      } on FirebaseAuthException {
        // Firebase may not have this user; ignore
      }
    }
  }

  Future<void> sendPasswordReset(String email) async {
    await _auth.sendPasswordResetEmail(email: email.trim());
  }

  Future<Object?> signInWithGoogle() async {
    try {
      final googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;

      final googleAuth = await googleUser.authentication;
      final credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );
      await _auth.signInWithCredential(credential);

      // Call dev backend login with the Google email
      final email = _auth.currentUser?.email;
      if (email != null) {
        // Try to log in via dev backend (user may need to register first)
        try {
          final response = await _dio.post<Map<String, dynamic>>(
            '/api/v1/auth/login',
            data: {'email': email, 'password': ''},
          );
          _devToken = response.data?['access_token'] as String?;
          await _storeDevToken(_devToken);
          return _devToken;
        } on DioException catch (e) {
          if (e.response?.statusCode == 401) {
            // User not registered in dev backend — return email so frontend can prompt registration
            return {'email': email, 'needs_registration': true};
          }
          rethrow;
        }
      }
      return null;
    } on FirebaseAuthException catch (e) {
      return {'error': e.code};
    }
  }

  Future<void> signOut() async {
    _devToken = null;
    await _storeDevToken(null);
    try {
      await _auth.signOut();
    } on FirebaseAuthException {
      // Ignore sign-out errors
    }
    try {
      await _googleSignIn.signOut();
    } on Exception {
      // Ignore
    }
  }

  Future<void> deleteAccount() async {
    if (_devToken == null) return;
    await _dio.delete<void>(
      '/api/v1/users/me',
      options: Options(
        headers: {'Authorization': 'Bearer $_devToken'},
      ),
    );
    _devToken = null;
    await _storeDevToken(null);
    try {
      await _auth.currentUser?.delete();
    } on FirebaseAuthException {
      // Ignore
    }
  }
}

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService();
});
