import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/api.dart';
import '../core/auth_service.dart';
import '../state/providers.dart';
import '../theme/app_theme.dart';

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final PageController _controller = PageController();
  int _page = 0;

  final List<_OnboardingPage> _pages = const [
    _OnboardingPage(
      icon: Icons.insights,
      title: 'Understand the game',
      body: 'Prediqo brings you fixtures, team form and statistical '
          'insights in one place.',
    ),
    _OnboardingPage(
      icon: Icons.data_object,
      title: 'Transparent probabilities',
      body: 'Estimates come from evaluated statistical models. We show '
          'the probabilities and explain the facts behind them.',
    ),
    _OnboardingPage(
      icon: Icons.confirmation_number_outlined,
      title: 'Free, tokens or VIP',
      body: 'Start free, unlock individual reports with tokens, or get '
          'expanded access with VIP.',
    ),
    _OnboardingPage(
      icon: Icons.privacy_tip_outlined,
      title: 'Responsible use',
      body: 'Prediqo is informational sports analytics, not betting. '
          'Predictions are estimates and can be wrong.',
    ),
  ];

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _finish() async {
    try {
      await ref
          .read(fixturesRepositoryProvider)
          .updateProfile({'onboarding_completed': true});
      ref.invalidate(currentUserProvider);
    } catch (_) {
      // Keep navigating even if profile update fails offline.
    }
    if (!mounted) return;
    final signedIn = ref.read(authServiceProvider).isSignedIn;
    context.go(signedIn ? '/home' : '/auth');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Welcome'),
        actions: [
          TextButton(
            onPressed: _finish,
            child: const Text('Skip'),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView.builder(
                controller: _controller,
                itemCount: _pages.length,
                onPageChanged: (index) => setState(() => _page = index),
                itemBuilder: (context, index) => _buildPage(_pages[index]),
              ),
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _pages.length,
                (index) => Container(
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: index == _page
                        ? AppColors.primary
                        : AppColors.divider,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 24),
            Padding(
              padding: const EdgeInsets.all(24),
              child: SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () {
                    if (_page < _pages.length - 1) {
                      _controller.nextPage(
                        duration: const Duration(milliseconds: 250),
                        curve: Curves.easeInOut,
                      );
                    } else {
                      _finish();
                    }
                  },
                  child: Text(
                    _page < _pages.length - 1 ? 'Next' : 'Get started',
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPage(_OnboardingPage page) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(page.icon, size: 88, color: AppColors.primary),
          const SizedBox(height: 32),
          Text(
            page.title,
            style: Theme.of(context).textTheme.headlineSmall,
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 16),
          Text(
            page.body,
            style: const TextStyle(
              color: AppColors.textSecondary,
              fontSize: 16,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _OnboardingPage {
  const _OnboardingPage({
    required this.icon,
    required this.title,
    required this.body,
  });

  final IconData icon;
  final String title;
  final String body;
}
