import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../state/providers.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/design_system.dart';

class MatchesScreen extends ConsumerWidget {
  const MatchesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scope = ref.watch(fixtureScopeProvider);
    final fixtures = ref.watch(fixturesProvider);

    return AppScaffold(
      title: 'Matches',
      selectedIndex: 1,
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                _filterChip(ref, FixtureScope.scheduled, 'Upcoming', scope),
                const SizedBox(width: 8),
                _filterChip(ref, FixtureScope.finished, 'Results', scope),
                const SizedBox(width: 8),
                _filterChip(ref, FixtureScope.trending, 'Trending', scope),
              ],
            ),
          ),
          Expanded(
            child: fixtures.when(
              data: (page) {
                if (page.items.isEmpty) {
                  return const EmptyState(
                    title: 'No fixtures',
                    message: 'No fixtures match this filter.',
                  );
                }
                return ListView(
                  padding: const EdgeInsets.symmetric(horizontal: 12),
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
            ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip(
    WidgetRef ref,
    FixtureScope value,
    String label,
    FixtureScope current,
  ) {
    return ChoiceChip(
      label: Text(label),
      selected: value == current,
      onSelected: (_) {
        ref.read(fixtureScopeProvider.notifier).state = value;
      },
    );
  }
}
