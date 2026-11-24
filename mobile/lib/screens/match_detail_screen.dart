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
    final analysis = ref.watch(analysisProvider(fixtureId));

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
            analysis.when(
              data: (model) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SectionHeader(title: 'Result Probabilities'),
                  Row(
                    children: [
                      Icon(
                        Icons.verified_user_outlined,
                        size: 16,
                        color: AppColors.primary,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        'Access: ${model.entitlement.toUpperCase()}',
                        style: const TextStyle(fontSize: 12),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ProbabilityBar(
                    label: 'Home',
                    value: model.oneXTwo['home'] ?? 0,
                  ),
                  ProbabilityBar(
                    label: 'Draw',
                    value: model.oneXTwo['draw'] ?? 0,
                  ),
                  ProbabilityBar(
                    label: 'Away',
                    value: model.oneXTwo['away'] ?? 0,
                  ),
                  if (model.expectedHomeGoals != null &&
                      model.expectedAwayGoals != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 12),
                      child: Text(
                        'Expected goals: '
                        '${model.expectedHomeGoals!.toStringAsFixed(2)} - '
                        '${model.expectedAwayGoals!.toStringAsFixed(2)}',
                      ),
                    ),
                  const SectionHeader(title: 'Other Markets'),
                  ...model.markets.entries
                      .where((entry) => entry.key != '1X2')
                      .map(
                        (entry) => Card(
                          child: ListTile(
                            title: Text('${entry.key} · ${entry.value.name}'),
                            subtitle: Text(
                              'Selection: ${entry.value.selectedOutcome}',
                            ),
                          ),
                        ),
                      ),
                  const SectionHeader(title: 'Model Explanation'),
                  ...model.facts.map(
                    (fact) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Text('• $fact'),
                    ),
                  ),
                ],
              ),
              loading: () => const Padding(
                padding: EdgeInsets.all(16),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, _) =>
                  _analysisError(error, ref, fixtureId),
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

  Widget _analysisError(Object error, WidgetRef ref, String fixtureId) {
    final text = error.toString();
    final locked =
        text.contains('403') || text.contains('ENTITLEMENT_REQUIRED');
    final message = locked
        ? 'Daily free analysis limit reached. Upgrade to VIP or unlock with '
            'tokens to see this report.'
        : 'Could not load analysis: $text';

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              message,
              style: const TextStyle(color: AppColors.warning),
            ),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: () => ref.invalidate(analysisProvider(fixtureId)),
              child: const Text('Retry'),
            ),
          ],
        ),
      ),
    );
  }
}
