import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../data/models.dart';
import '../state/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/design_system.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final fixtures = ref.watch(fixturesProvider);
    final trending = ref.watch(trendingProvider);
    final user = ref.watch(currentUserProvider);
    final tokenBalance = ref.watch(tokenBalanceProvider);
    final now = DateTime.now();
    final date = '${now.day}/${now.month}/${now.year}';

    return AppScaffold(
      title: 'Prediqo',
      selectedIndex: 0,
      actions: [
        IconButton(
          icon: const Icon(Icons.notifications_none),
          onPressed: () => context.go('/notifications'),
        ),
      ],
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _greeting(user),
          Text(date, style: const TextStyle(color: AppColors.textSecondary)),
          const SizedBox(height: 8),
          _statusChips(user, tokenBalance),
          SectionHeader(
            title: 'Today\'s Matches',
            onAction: () => context.go('/matches'),
          ),
          _fixtureList(fixtures, ref, context),
          SectionHeader(
            title: 'Trending Fixtures',
            onAction: () => context.go('/matches'),
          ),
          _fixtureList(trending, ref, context),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _greeting(AsyncValue<UserModel?> user) {
    final name = user.value?.displayName ?? 'there';
    return Text(
      'Hello, $name',
      style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
    );
  }

  Widget _statusChips(
    AsyncValue<UserModel?> user,
    AsyncValue<TokenBalanceModel> tokenBalance,
  ) {
    final isVip = user.value?.isVip ?? false;
    return Wrap(
      spacing: 8,
      children: [
        Chip(
          label: Text(isVip ? 'VIP Member' : 'Free Plan'),
          backgroundColor: isVip ? AppColors.primary : AppColors.surfaceAlt,
        ),
        Chip(
          label: Text('Tokens: ${tokenBalance.value?.balance ?? 0}'),
          backgroundColor: AppColors.surfaceAlt,
        ),
      ],
    );
  }

  Widget _fixtureList(
    AsyncValue<FixturePage> state,
    WidgetRef ref,
    BuildContext context,
  ) {
    return state.when(
      data: (page) {
        if (page.items.isEmpty) {
          return const EmptyState(
            title: 'No matches yet',
            message: 'Run a data sync to load fixtures.',
          );
        }
        return Column(
          children: page.items
              .map(
                (fixture) => MatchCard(
                  fixture: fixture,
                  onTap: () => context.go('/matches/${fixture.id}'),
                ),
              )
              .toList(),
        );
      },
      loading: () => const LoadingState(),
      error: (error, _) => ErrorState(
        error: error,
        onRetry: () => ref.invalidate(fixturesProvider),
      ),
    );
  }
}
