import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../state/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/design_system.dart';

class PredictionsScreen extends StatelessWidget {
  const PredictionsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const AppScaffold(
      title: 'Predictions',
      selectedIndex: 2,
      body: EmptyState(
        title: 'No predictions published yet',
        message: 'Predictions appear here after validated models are deployed in '
            'Phase 5. Nothing is shown before it can be verified.',
        icon: Icons.insights_outlined,
      ),
    );
  }
}

class PerformanceScreen extends StatelessWidget {
  const PerformanceScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const AppScaffold(
      title: 'Performance',
      selectedIndex: 3,
      body: EmptyState(
        title: 'No settled predictions yet',
        message: 'Accuracy and calibration charts appear after predictions have '
            'been settled. Sample sizes are always shown.',
        icon: Icons.bar_chart_outlined,
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

  Widget _tile(BuildContext context, IconData icon, String label, String route) {
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

class VipScreen extends StatelessWidget {
  const VipScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return AppScaffold(
      title: 'VIP Membership',
      selectedIndex: 4,
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Prediqo VIP',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                  SizedBox(height: 8),
                  Text('KSh 499 per month'),
                  SizedBox(height: 16),
                  Text('• Expanded daily predictions'),
                  Text('• Advanced match analysis'),
                  Text('• Detailed AI explanations'),
                  Text('• Extended prediction history'),
                  Text('• Ad-free experience'),
                ],
              ),
            ),
          ),
          EmptyState(
            title: 'Purchase flow in Phase 7',
            message: 'Subscriptions are verified by the backend via Google Play '
                'Billing. No payment is taken in this build.',
            icon: Icons.workspace_premium_outlined,
          ),
        ],
      ),
    );
  }
}

class TokenStoreScreen extends StatelessWidget {
  const TokenStoreScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const AppScaffold(
      title: 'Token Store',
      selectedIndex: 4,
      body: EmptyState(
        title: 'Token store in Phase 7',
        message: 'Token packages and the immutable transaction ledger are '
            'implemented before any purchase is enabled.',
        icon: Icons.confirmation_number_outlined,
      ),
    );
  }
}

class NotificationsScreen extends StatelessWidget {
  const NotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const AppScaffold(
      title: 'Notifications',
      selectedIndex: 0,
      body: EmptyState(
        title: 'No notifications',
        message: 'Match reminders and daily insights arrive in Phase 10.',
        icon: Icons.notifications_none,
      ),
    );
  }
}
