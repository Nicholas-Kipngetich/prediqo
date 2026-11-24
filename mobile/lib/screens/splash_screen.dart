import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/ads.dart';
import '../core/auth_service.dart';
import '../state/providers.dart';
import '../theme/app_theme.dart';

const bool devBypassAuth = bool.fromEnvironment(
  'DEV_BYPASS_AUTH',
  defaultValue: false,
);

class SplashScreen extends ConsumerStatefulWidget {
  const SplashScreen({super.key});

  @override
  ConsumerState<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends ConsumerState<SplashScreen> {
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _timer = Timer(const Duration(milliseconds: 1200), _continue);
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _continue() async {
    if (!mounted) return;
    bool signedIn = false;
    bool isVip = false;
    try {
      signedIn = ref.read(authServiceProvider).isSignedIn;
      final user = await ref.read(currentUserProvider.future);
      isVip = user?.isVip ?? false;
    } catch (_) {
      // Firebase or API unavailable in local tests.
    }
    if (!adsLocallyDisabled) {
      try {
        final config = await ref.read(adsConfigProvider.future);
        await AdService.instance.showAppOpen(
          config,
          isVip,
          ref.read(adConsentProvider),
        );
      } catch (_) {
        // Ads are optional.
      }
    }
    if (!mounted) return;
    context.go(devBypassAuth || signedIn ? '/home' : '/auth');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 96,
              height: 96,
              decoration: BoxDecoration(
                color: AppColors.surface,
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: AppColors.primary, width: 2),
              ),
              child: const Icon(
                Icons.insights,
                color: AppColors.primary,
                size: 52,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Prediqo',
              style: TextStyle(
                fontSize: 36,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Predict Smarter. Understand Deeper.',
              style: TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 32),
            const CircularProgressIndicator(color: AppColors.primary),
          ],
        ),
      ),
    );
  }
}
