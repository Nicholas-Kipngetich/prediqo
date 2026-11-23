import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../state/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/design_system.dart';

class PredictionsScreen extends ConsumerWidget {
  const PredictionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final predictions = ref.watch(predictionsProvider('1X2'));

    return AppScaffold(
      title: 'Predictions',
      selectedIndex: 2,
      body: predictions.when(
        data: (items) {
          if (items.isEmpty) {
            return const EmptyState(
              title: 'No predictions published yet',
              message:
                  'Run prediction generation from the admin API to publish '
                  'the first validated predictions.',
              icon: Icons.insights_outlined,
            );
          }
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, index) {
              final item = items[index];
              final probs = item.probabilitiesBp;
              final home = probs['home'] ?? 0;
              final draw = probs['draw'] ?? 0;
              final away = probs['away'] ?? 0;
              return Card(
                child: ListTile(
                  title: Text('${item.market} · ${item.selectedOutcome}'),
                  subtitle: Text('H $home%  D $draw%  A $away%'),
                  trailing: Text(
                    item.isSampleData ? 'DEMO' : item.status,
                    style: const TextStyle(fontSize: 10),
                  ),
                ),
              );
            },
          );
        },
        loading: () => const LoadingState(),
        error: (error, _) => ErrorState(
          error: error,
          onRetry: () => ref.invalidate(predictionsProvider('1X2')),
        ),
      ),
    );
  }
}

class PerformanceScreen extends ConsumerWidget {
  const PerformanceScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final performance = ref.watch(performanceProvider);

    return AppScaffold(
      title: 'Performance',
      selectedIndex: 3,
      body: performance.when(
        data: (data) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    const Text(
                      'Accuracy',
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      data.accuracyLabel,
                      style: const TextStyle(
                        fontSize: 36,
                        fontWeight: FontWeight.bold,
                        color: AppColors.primary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text('Sample size: ${data.sampleSize}'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            _statTile('Total predictions', data.totalPredictions),
            _statTile('Settled', data.settledPredictions),
            _statTile('Correct', data.correct),
            _statTile('Incorrect', data.incorrect),
            _statTile('Pending', data.pending),
            _statTile('Void', data.voidCount),
          ],
        ),
        loading: () => const LoadingState(),
        error: (error, _) => ErrorState(
          error: error,
          onRetry: () => ref.invalidate(performanceProvider),
        ),
      ),
    );
  }

  Widget _statTile(String label, int value) {
    return Card(
      child: ListTile(
        title: Text(label),
        trailing: Text(value.toString()),
      ),
    );
  }
}

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider);

    return AppScaffold(
      title: 'Profile',
      selectedIndex: 4,
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          user.when(
            data: (model) => Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      model?.displayName ?? 'Guest',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      model?.email ?? 'Not signed in',
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 12),
                    Text('Roles: ${model?.roles.join(', ') ?? 'none'}'),
                    Text('VIP: ${model?.isVip ?? false}'),
                  ],
                ),
              ),
            ),
            loading: () => const LoadingState(),
            error: (error, _) => Text('Error: $error'),
          ),
          const SizedBox(height: 16),
          _tile(context, Icons.workspace_premium, 'VIP Membership', '/vip'),
          _tile(context, Icons.confirmation_number, 'Token Store', '/tokens'),
          _tile(
            context,
            Icons.notifications_none,
            'Notifications',
            '/notifications',
          ),
        ],
      ),
    );
  }

  Widget _tile(
      BuildContext context, IconData icon, String label, String route) {
    return Card(
      child: ListTile(
        leading: Icon(icon, color: AppColors.primary),
        title: Text(label),
        trailing: const Icon(Icons.chevron_right),
        onTap: () => context.go(route),
      ),
    );
  }
}

class VipScreen extends ConsumerWidget {
  const VipScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(subscriptionStatusProvider);
    final plans = ref.watch(plansProvider);

    return AppScaffold(
      title: 'VIP Membership',
      selectedIndex: 4,
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          status.when(
            data: (data) => Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      data.isVip ? 'VIP Active' : 'Free Plan',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text('Status: ${data.status ?? 'none'}'),
                    Text('Plan: ${data.planCode ?? 'none'}'),
                  ],
                ),
              ),
            ),
            loading: () => const LoadingState(),
            error: (error, _) => Text('Error: $error'),
          ),
          const SectionHeader(title: 'Plans'),
          plans.when(
            data: (items) => Column(
              children: items
                  .map(
                    (plan) => Card(
                      child: ListTile(
                        title: Text('VIP ${plan.interval}'),
                        subtitle: Text(plan.priceLabel),
                        trailing: Text(plan.code),
                      ),
                    ),
                  )
                  .toList(),
            ),
            loading: () => const LoadingState(),
            error: (error, _) => Text('Error: $error'),
          ),
          const EmptyState(
            title: 'Purchase flow',
            message: 'Subscriptions are verified by the backend via Google '
                'Play Billing. No payment is taken in this build.',
            icon: Icons.workspace_premium_outlined,
          ),
        ],
      ),
    );
  }
}

class TokenStoreScreen extends ConsumerWidget {
  const TokenStoreScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final balance = ref.watch(tokenBalanceProvider);
    final packages = ref.watch(tokenPackagesProvider);

    return AppScaffold(
      title: 'Token Store',
      selectedIndex: 4,
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          balance.when(
            data: (data) => Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    const Text(
                      'Balance',
                      style: TextStyle(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '${data.balance}',
                      style: const TextStyle(
                        fontSize: 36,
                        fontWeight: FontWeight.bold,
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            loading: () => const LoadingState(),
            error: (error, _) => Text('Error: $error'),
          ),
          const SectionHeader(title: 'Packages'),
          packages.when(
            data: (items) => Column(
              children: items
                  .map(
                    (item) => Card(
                      child: ListTile(
                        title: Text(item.name),
                        subtitle: Text('${item.tokens} tokens'),
                        trailing: Text(item.priceLabel),
                      ),
                    ),
                  )
                  .toList(),
            ),
            loading: () => const LoadingState(),
            error: (error, _) => Text('Error: $error'),
          ),
          const EmptyState(
            title: 'Purchases are server-verified',
            message: 'No payment is taken in this build. Token credits use an '
                'immutable ledger.',
            icon: Icons.confirmation_number_outlined,
          ),
        ],
      ),
    );
  }
}

class NotificationsScreen extends ConsumerWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final notifications = ref.watch(notificationsProvider);

    return AppScaffold(
      title: 'Notifications',
      selectedIndex: 0,
      body: notifications.when(
        data: (items) {
          if (items.isEmpty) {
            return const EmptyState(
              title: 'No notifications',
              message: 'Match reminders and daily insights will appear here.',
              icon: Icons.notifications_none,
            );
          }
          return ListView.builder(
            itemCount: items.length,
            itemBuilder: (context, index) {
              final item = items[index];
              return Card(
                child: ListTile(
                  leading: Icon(
                    item.isRead
                        ? Icons.notifications_none
                        : Icons.notifications_active,
                    color: item.isRead
                        ? AppColors.textSecondary
                        : AppColors.primary,
                  ),
                  title: Text(item.title),
                  subtitle: Text(item.body),
                  trailing: Text(item.type),
                ),
              );
            },
          );
        },
        loading: () => const LoadingState(),
        error: (error, _) => ErrorState(
          error: error,
          onRetry: () => ref.invalidate(notificationsProvider),
        ),
      ),
    );
  }
}
