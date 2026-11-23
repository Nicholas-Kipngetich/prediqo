import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../state/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/design_system.dart';

class MatchDetailScreen extends ConsumerWidget {
  final String fixtureId;

  const MatchDetailScreen({super.key, required this.fixtureId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(fixtureDetailProvider(fixtureId));

    return AppScaffold(
      title: 'Match Analysis',
      selectedIndex: 1,
      body: state.when(
        data: (fixture) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (fixture.isSampleData)
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.surfaceAlt,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Text(
                  'DEMO DATA — this fixture is sample data for development '
                  'and is not a real match.',
                  style: TextStyle(color: AppColors.warning, fontSize: 12),
                ),
              ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    Text(
                      fixture.competition.name,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        Expanded(
                          child: Text(
                            fixture.homeTeam.name,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                        Text(
                          fixture.homeScore != null
                              ? '${fixture.homeScore} - ${fixture.awayScore}'
                              : 'vs',
                          style: const TextStyle(fontSize: 20),
                        ),
                        Expanded(
                          child: Text(
                            fixture.awayTeam.name,
                            textAlign: TextAlign.center,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      '${fixture.statusLabel}  •  ${fixture.kickoffLabel}',
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                  ],
                ),
              ),
            ),
            SectionHeader(title: 'Result Probabilities'),
            const EmptyState(
              title: 'Analysis in development',
              message: 'Probabilities are published only after the statistical '
                  'models are validated in Phase 5.',
              icon: Icons.analytics_outlined,
            ),
          ],
        ),
        loading: () => const LoadingState(),
        error: (error, _) => ErrorState(
          error: error,
          onRetry: () => ref.invalidate(fixtureDetailProvider(fixtureId)),
        ),
      ),
    );
  }
}
