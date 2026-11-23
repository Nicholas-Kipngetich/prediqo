import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api.dart';
import '../data/models.dart';

enum FixtureScope { scheduled, finished, trending }

final fixtureScopeProvider = Provider<FixtureScope>((ref) {
  return FixtureScope.scheduled;
});

final fixturesProvider = FutureProvider<FixturePage>((ref) async {
  final repo = ref.watch(fixturesRepositoryProvider);
  final scope = ref.watch(fixtureScopeProvider);
  switch (scope) {
    case FixtureScope.finished:
      return repo.fetchFixtures(status: 'FINISHED');
    case FixtureScope.trending:
      return repo.fetchTrending();
    case FixtureScope.scheduled:
      return repo.fetchFixtures(status: 'SCHEDULED');
  }
});

final fixtureDetailProvider =
    FutureProvider.family<FixtureModel, String>((ref, id) async {
  return ref.watch(fixturesRepositoryProvider).fetchFixture(id);
});

final trendingProvider = FutureProvider<FixturePage>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchTrending();
});

final currentUserProvider = FutureProvider<UserModel?>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchCurrentUser();
});
