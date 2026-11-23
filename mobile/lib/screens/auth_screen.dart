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
  final _passwordController = TextEditingController();
  bool _register = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final auth = ref.read(authServiceProvider);
      if (_register) {
        await auth.registerWithEmail(
          _emailController.text,
          _passwordController.text,
        );
      } else {
        await auth.signInWithEmail(
          _emailController.text,
          _passwordController.text,
        );
      }
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

  Future<void> _resetPassword() async {
    if (_emailController.text.isEmpty) {
      setState(() => _error = 'Enter your email first.');
      return;
    }
    try {
      await ref
          .read(authServiceProvider)
          .sendPasswordReset(_emailController.text);
      if (mounted) {
        setState(() => _error = 'Password reset email sent.');
      }
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
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
                    _register ? 'Create your account' : 'Welcome back',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 24),
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
                  const SizedBox(height: 16),
                  if (_error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(
                        _error!,
                        style: const TextStyle(color: AppColors.warning),
                      ),
                    ),
                  FilledButton(
                    onPressed: _busy ? null : _submit,
                    child: Text(_register ? 'Create account' : 'Sign in'),
                  ),
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: _busy ? null : _google,
                    icon: const Icon(Icons.g_mobiledata),
                    label: const Text('Continue with Google'),
                  ),
                  const SizedBox(height: 8),
                  TextButton(
                    onPressed: _register ? null : _resetPassword,
                    child: const Text('Forgot password?'),
                  ),
                  TextButton(
                    onPressed: () =>
                        setState(() => _register = !_register),
                    child: Text(
                      _register
                          ? 'Already have an account? Sign in'
                          : 'New here? Create an account',
                    ),
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
