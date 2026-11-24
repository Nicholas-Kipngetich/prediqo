import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/auth_service.dart';
import '../state/providers.dart';
import '../theme/app_theme.dart';

class AuthScreen extends ConsumerStatefulWidget {
  const AuthScreen({super.key});

  @override
  ConsumerState<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends ConsumerState<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmController = TextEditingController();
  final _codeController = TextEditingController();

  bool _register = false;
  bool _useEmail = true;
  bool _awaitingCode = false;
  bool _busy = false;
  String? _error;
  String? _verificationCode;
  String? _identifier;

  @override
  void dispose() {
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  String? _identifierValue() {
    if (_useEmail) {
      final value = _emailController.text.trim();
      return value.isEmpty ? null : value;
    }
    final value = _phoneController.text.trim();
    return value.isEmpty ? null : value;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final auth = ref.read(authServiceProvider);
      final identifier = _identifierValue();
      if (identifier == null) {
        throw Exception('Enter an email or phone number.');
      }
      if (_register) {
        final code = await auth.register(
          email: _useEmail ? identifier : null,
          phone: _useEmail ? null : identifier,
          password: _passwordController.text,
          displayName: null,
        );
        _identifier = identifier;
        _verificationCode = code;
        _awaitingCode = true;
        _codeController.clear();
      } else {
        await auth.login(
          email: _useEmail ? identifier : null,
          phone: _useEmail ? null : identifier,
          password: _passwordController.text,
        );
        ref.invalidate(currentUserProvider);
        if (mounted) context.go('/home');
      }
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _verifyCode() async {
    final identifier = _identifier;
    if (identifier == null) return;
    if (_codeController.text.trim().length < 4) {
      setState(() => _error = 'Enter the verification code.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(authServiceProvider).verifyCode(
            email: _useEmail ? identifier : null,
            phone: _useEmail ? null : identifier,
            code: _codeController.text.trim(),
          );
      ref.invalidate(currentUserProvider);
      if (mounted) context.go('/home');
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _google() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final credential = await ref.read(authServiceProvider).signInWithGoogle();
      if (credential != null) {
        ref.invalidate(currentUserProvider);
        if (mounted) context.go('/home');
      }
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Sign in')),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text(
                    'Prediqo',
                    style: TextStyle(
                      fontSize: 36,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primary,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _awaitingCode
                        ? 'We sent a verification code to your '
                            '${_useEmail ? 'email' : 'phone'}'
                        : _register
                            ? 'Create your account'
                            : 'Welcome back',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 24),
                  if (!_awaitingCode) ...[
                    SegmentedButton<bool>(
                      segments: const [
                        ButtonSegment(value: true, label: Text('Email')),
                        ButtonSegment(value: false, label: Text('Phone')),
                      ],
                      selected: {_useEmail},
                      onSelectionChanged: (value) {
                        setState(() => _useEmail = value.first);
                      },
                    ),
                    const SizedBox(height: 16),
                    if (_useEmail)
                      TextFormField(
                        controller: _emailController,
                        keyboardType: TextInputType.emailAddress,
                        decoration: const InputDecoration(labelText: 'Email'),
                        validator: (value) {
                          if (value == null || !value.contains('@')) {
                            return 'Enter a valid email';
                          }
                          return null;
                        },
                      )
                    else
                      TextFormField(
                        controller: _phoneController,
                        keyboardType: TextInputType.phone,
                        decoration: const InputDecoration(labelText: 'Phone number'),
                        validator: (value) {
                          if (value == null || value.trim().length < 7) {
                            return 'Enter a valid phone number';
                          }
                          return null;
                        },
                      ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _passwordController,
                      obscureText: true,
                      decoration: const InputDecoration(labelText: 'Password'),
                      validator: (value) {
                        if (value == null || value.length < 6) {
                          return 'At least 6 characters';
                        }
                        return null;
                      },
                    ),
                    if (_register) ...[
                      const SizedBox(height: 12),
                      TextFormField(
                        controller: _confirmController,
                        obscureText: true,
                        decoration: const InputDecoration(
                          labelText: 'Confirm password',
                        ),
                        validator: (value) {
                          if (value != _passwordController.text) {
                            return 'Passwords do not match';
                          }
                          return null;
                        },
                      ),
                    ],
                  ],
                  if (_awaitingCode) ...[
                    TextFormField(
                      controller: _codeController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(
                        labelText: 'Verification code',
                      ),
                      validator: (value) {
                        if (value == null || value.trim().length < 4) {
                          return 'Enter the code';
                        }
                        return null;
                      },
                    ),
                    if (_verificationCode != null &&
                        _verificationCode!.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(
                        'Development code: $_verificationCode',
                        style: const TextStyle(color: AppColors.warning),
                      ),
                    ],
                  ],
                  const SizedBox(height: 16),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(
                        _error!,
                        style: const TextStyle(color: AppColors.warning),
                      ),
                    ),
                  if (!_awaitingCode)
                    FilledButton(
                      onPressed: _busy ? null : _submit,
                      child: Text(_register ? 'Create account' : 'Sign in'),
                    )
                  else
                    FilledButton(
                      onPressed: _busy ? null : _verifyCode,
                      child: const Text('Verify'),
                    ),
                  if (!_awaitingCode) ...[
                    const SizedBox(height: 8),
                    OutlinedButton.icon(
                      onPressed: _busy ? null : _google,
                      icon: const Icon(Icons.g_mobiledata),
                      label: const Text('Continue with Google'),
                    ),
                    const SizedBox(height: 8),
                    TextButton(
                      onPressed: _register
                          ? null
                          : () => context.go('/reset-password'),
                      child: const Text('Forgot password?'),
                    ),
                    TextButton(
                      onPressed: () => setState(() => _register = !_register),
                      child: Text(
                        _register
                            ? 'Already have an account? Sign in'
                            : 'New here? Create an account',
                      ),
                    ),
                  ] else
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _awaitingCode = false;
                          _verificationCode = null;
                        });
                      },
                      child: const Text('Back'),
                    ),
                  if (_busy)
                    const Padding(
                      padding: EdgeInsets.all(12),
                      child: Center(child: CircularProgressIndicator()),
                    ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
