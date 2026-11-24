import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../state/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/design_system.dart';

class PredictionHistoryScreen extends ConsumerStatefulWidget {
  const PredictionHistoryScreen({super.key});

  @override
  ConsumerState<PredictionHistoryScreen> createState() =>
      _PredictionHistoryScreenState();
}

class _PredictionHistoryScreenState
    extends ConsumerState<PredictionHistoryScreen> {
  String _status = 'all';

  @override
  Widget build(BuildContext context) {
    final history = ref.watch(predictionHistoryProvider(_status));

    return AppScaffold(
      title: 'Prediction History',
      selectedIndex: 2,
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Wrap(
              spacing: 8,
              children: [
                _chip('All', 'all'),
                _chip('Pending', 'PENDING'),
                _chip('Correct', 'CORRECT'),
                _chip('Incorrect', 'INCORRECT'),
                _chip('Void', 'VOID'),
              ],
            ),
          ),
          Expanded(
            child: history.when(
              data: (items) {
                if (items.isEmpty) {
                  return const EmptyState(
                    title: 'No predictions yet',
                    message: 'Published predictions will appear here.',
                    icon: Icons.history,
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
                        title: Text(
                          item.fixtureLabel ?? '${item.market} · ${item.selectedOutcome}',
                        ),
                        subtitle: Text(
                          '${item.market} · H $home% D $draw% A $away%\n'
                          '${item.competitionName ?? ''} • ${item.kickoffUtc?.toLocal().toString().split('.').first ?? ''}',
                        ),
                        isThreeLine: true,
                        trailing: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            Text(
                              item.status,
                              style: TextStyle(
                                color: item.status == 'CORRECT'
                                    ? AppColors.primary
                                    : AppColors.textSecondary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            if (item.actualOutcome != null)
                              Text(
                                item.actualOutcome!,
                                style: const TextStyle(fontSize: 10),
                              ),
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
              loading: () => const LoadingState(),
              error: (error, _) => ErrorState(
                error: error,
                onRetry: () =>
                    ref.invalidate(predictionHistoryProvider(_status)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _chip(String label, String value) {
    return ChoiceChip(
      label: Text(label),
      selected: _status == value,
      onSelected: (_) => setState(() => _status = value),
    );
  }
}
