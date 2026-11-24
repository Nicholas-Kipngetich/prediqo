import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/auth_service.dart';
import '../state/providers.dart';
import '../theme/app_theme.dart';

class ResetPasswordScreen extends ConsumerStatefulWidget {
  const ResetPasswordScreen({super.key});

  @override
  ConsumerState<ResetPasswordScreen> createState() =>
      _ResetPasswordScreenState();
}

class _ResetPasswordScreenState extends ConsumerState<ResetPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _codeController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _useEmail = true;
  bool _codeSent = false;
  bool _busy = false;
  String? _error;
  String? _resetCode;

  @override
  void dispose() {
    _emailController.dispose();
    _phoneController.dispose();
    _codeController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  String? _identifier() {
    final value =
        _useEmail ? _emailController.text.trim() : _phoneController.text.trim();
    return value.isEmpty ? null : value;
  }

  Future<void> _requestCode() async {
    final id = _identifier();
    if (id == null) {
      setState(() => _error = 'Enter your email or phone first.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final code = await ref.read(authServiceProvider).requestPasswordReset(
            email: _useEmail ? id : null,
            phone: _useEmail ? null : id,
          );
      if (mounted) {
        setState(() {
          _codeSent = true;
          _resetCode = code;
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _reset() async {
    final id = _identifier();
    if (id == null) return;
    if (_codeController.text.trim().length < 4) {
      setState(() => _error = 'Enter the reset code.');
      return;
    }
    if (_passwordController.text.length < 6) {
      setState(() => _error = 'Password must be at least 6 characters.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(authServiceProvider).resetPassword(
            email: _useEmail ? id : null,
            phone: _useEmail ? null : id,
            code: _codeController.text.trim(),
            newPassword: _passwordController.text,
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Password updated. You can now sign in.')),
        );
        context.go('/auth');
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
      appBar: AppBar(title: const Text('Reset password')),
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
                    _codeSent ? 'Enter the reset code' : 'Reset your password',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 24),
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
                    )
                  else
                    TextFormField(
                      controller: _phoneController,
                      keyboardType: TextInputType.phone,
                      decoration: const InputDecoration(labelText: 'Phone number'),
                    ),
                  if (_codeSent) ...[
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _codeController,
                      keyboardType: TextInputType.number,
                      decoration: const InputDecoration(labelText: 'Reset code'),
                    ),
                    const SizedBox(height: 12),
                    TextFormField(
                      controller: _passwordController,
                      obscureText: true,
                      decoration: const InputDecoration(labelText: 'New password'),
                    ),
                    if (_resetCode != null && _resetCode!.isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(
                        'Development code: $_resetCode',
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
                  if (!_codeSent)
                    FilledButton(
                      onPressed: _busy ? null : _requestCode,
                      child: const Text('Send reset code'),
                    )
                  else
                    FilledButton(
                      onPressed: _busy ? null : _reset,
                      child: const Text('Reset password'),
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
