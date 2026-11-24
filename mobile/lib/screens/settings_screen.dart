import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/api.dart';
import '../core/auth_service.dart';
import '../state/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/design_system.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider).value;
    final favorites = ref.watch(favoritesProvider).value;
    final preferences = ref.watch(preferencesProvider).value;
    final themeMode = ref.watch(themeModeProvider);

    return AppScaffold(
      title: 'Settings',
      selectedIndex: 4,
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    user?.displayName ?? 'Guest',
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user?.email ?? 'Not signed in',
                    style: const TextStyle(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 8),
                  Text('VIP: ${user?.isVip ?? false}'),
                  Text('Timezone: ${user?.timezone ?? 'Africa/Nairobi'}'),
                ],
              ),
            ),
          ),
          const SectionHeader(title: 'Appearance'),
          Card(
            child: ListTile(
              leading: const Icon(Icons.brightness_6),
              title: const Text('Theme'),
              trailing: DropdownButton<ThemeMode>(
                value: themeMode,
                underline: const SizedBox.shrink(),
                items: const [
                  DropdownMenuItem(
                    value: ThemeMode.system,
                    child: Text('System'),
                  ),
                  DropdownMenuItem(
                    value: ThemeMode.light,
                    child: Text('Light'),
                  ),
                  DropdownMenuItem(
                    value: ThemeMode.dark,
                    child: Text('Dark'),
                  ),
                ],
                onChanged: (value) {
                  if (value != null) {
                    ref.read(themeModeProvider.notifier).state = value;
                  }
                },
              ),
            ),
          ),
          ListTile(
            title: const Text('Edit timezone'),
            subtitle: Text(user?.timezone ?? 'Africa/Nairobi'),
            onTap: () => _editProfileField(
              context,
              ref,
              'timezone',
              user?.timezone ?? 'Africa/Nairobi',
            ),
          ),
          const SectionHeader(title: 'Notifications'),
          if (preferences == null)
            const Padding(
              padding: EdgeInsets.all(12),
              child: Center(child: CircularProgressIndicator()),
            )
          else
            Card(
              child: Column(
                children: [
                  _toggle(
                    ref,
                    'daily_insight',
                    'Daily insights',
                    preferences.dailyInsight,
                  ),
                  _toggle(
                    ref,
                    'upcoming_fixture',
                    'Upcoming fixtures',
                    preferences.upcomingFixture,
                  ),
                  _toggle(
                    ref,
                    'match_result',
                    'Match results',
                    preferences.matchResult,
                  ),
                  _toggle(
                    ref,
                    'favorite_team',
                    'Favourite team updates',
                    preferences.favoriteTeam,
                  ),
                  _toggle(
                    ref,
                    'vip_content',
                    'VIP content',
                    preferences.vipContent,
                  ),
                  _toggle(
                    ref,
                    'subscription',
                    'Subscription events',
                    preferences.subscription,
                  ),
                ],
              ),
            ),
          const SectionHeader(title: 'Favourites'),
          ListTile(
            leading: const Icon(Icons.sports_soccer_outlined),
            title: const Text('Favourite teams'),
            subtitle: Text('${favorites?.teamIds.length ?? 0} selected'),
            onTap: () => _editFavorites(
              context,
              ref,
              'teams',
              favorites?.teamIds ?? [],
            ),
          ),
          ListTile(
            leading: const Icon(Icons.emoji_events_outlined),
            title: const Text('Favourite competitions'),
            subtitle: Text('${favorites?.competitionIds.length ?? 0} selected'),
            onTap: () => _editFavorites(
              context,
              ref,
              'competitions',
              favorites?.competitionIds ?? [],
            ),
          ),
          const SectionHeader(title: 'Account'),
          ListTile(
            leading: const Icon(Icons.workspace_premium_outlined),
            title: const Text('VIP membership'),
            onTap: () => context.go('/vip'),
          ),
          ListTile(
            leading: const Icon(Icons.confirmation_number_outlined),
            title: const Text('Token store'),
            onTap: () => context.go('/tokens'),
          ),
          ListTile(
            leading: const Icon(Icons.privacy_tip_outlined),
            title: const Text('Privacy'),
            onTap: () => _infoDialog(
              context,
              'Privacy',
              'Prediqo collects only the data needed to provide accounts, '
              'predictions and notifications. See the published privacy policy '
              'before release.',
            ),
          ),
          ListTile(
            leading: const Icon(Icons.description_outlined),
            title: const Text('Terms and conditions'),
            onTap: () => _infoDialog(
              context,
              'Terms',
              'Prediqo is informational sports analytics, not betting. '
              'Full terms must be published before release.',
            ),
          ),
          ListTile(
            leading: const Icon(Icons.support_agent_outlined),
            title: const Text('Support'),
            onTap: () => _infoDialog(
              context,
              'Support',
              'Contact support through the email address published on the '
              'Prediqo website.',
            ),
          ),
          ListTile(
            leading: const Icon(Icons.logout, color: AppColors.textSecondary),
            title: const Text('Sign out'),
            onTap: () async {
              await ref.read(authServiceProvider).signOut();
              ref.invalidate(currentUserProvider);
              if (context.mounted) context.go('/auth');
            },
          ),
          ListTile(
            leading: const Icon(Icons.delete_outline, color: AppColors.warning),
            title: const Text('Delete account'),
            onTap: () => _confirmDelete(context, ref),
          ),
        ],
      ),
    );
  }

  Widget _toggle(
    WidgetRef ref,
    String key,
    String label,
    bool value,
  ) {
    return SwitchListTile(
      title: Text(label),
      value: value,
      onChanged: (enabled) async {
        await ref
            .read(fixturesRepositoryProvider)
            .updatePreferences({key: enabled});
        ref.invalidate(preferencesProvider);
      },
    );
  }

  Future<void> _editProfileField(
    BuildContext context,
    WidgetRef ref,
    String key,
    String current,
  ) async {
    final controller = TextEditingController(text: current);
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Edit $key'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: InputDecoration(labelText: key),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, controller.text),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (value == null || value.trim().isEmpty) return;
    await ref
        .read(fixturesRepositoryProvider)
        .updateProfile({key: value.trim()});
    ref.invalidate(currentUserProvider);
  }

  Future<void> _editFavorites(
    BuildContext context,
    WidgetRef ref,
    String kind,
    List<String> current,
  ) async {
    final controller = TextEditingController(text: current.join(', '));
    final value = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Favourite $kind'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Comma-separated IDs',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, controller.text),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (value == null) return;
    final ids = value
        .split(',')
        .map((item) => item.trim())
        .where((item) => item.isNotEmpty)
        .toList();
    await ref
        .read(fixturesRepositoryProvider)
        .setFavorites(kind, ids);
    ref.invalidate(favoritesProvider);
  }

  Future<void> _infoDialog(
    BuildContext context,
    String title,
    String message,
  ) {
    return showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Text(message),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  Future<void> _confirmDelete(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete account?'),
        content: const Text(
          'Your personal data will be removed. Historical predictions are '
          'retained anonymously for integrity.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true) return;
    try {
      await ref.read(fixturesRepositoryProvider).deleteAccount();
    } catch (_) {}
    try {
      await ref.read(authServiceProvider).deleteAccount();
    } catch (_) {}
    ref.invalidate(currentUserProvider);
    if (context.mounted) context.go('/auth');
  }
}
