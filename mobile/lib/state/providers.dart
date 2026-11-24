import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api.dart';
import '../data/models.dart';

enum FixtureScope { scheduled, finished, trending }

final fixtureScopeProvider = StateProvider<FixtureScope>((ref) {
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

final analysisProvider =
    FutureProvider.family<AnalysisModel, String>((ref, fixtureId) async {
  return ref.watch(fixturesRepositoryProvider).fetchAnalysis(fixtureId);
});

final predictionsProvider =
    FutureProvider.family<List<PredictionModel>, String>((ref, market) async {
  return ref.watch(fixturesRepositoryProvider).fetchPredictions(market);
});

final predictionHistoryProvider =
    FutureProvider.family<List<PredictionModel>, String>((ref, status) async {
  return ref.watch(fixturesRepositoryProvider).fetchPredictionHistory(
        status: status == 'all' ? null : status,
      );
});

final notificationsProvider =
    FutureProvider<List<NotificationModel>>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchNotifications();
});

final tokenBalanceProvider = FutureProvider<TokenBalanceModel>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchTokenBalance();
});

final tokenPackagesProvider =
    FutureProvider<List<TokenPackageModel>>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchTokenPackages();
});

final plansProvider = FutureProvider<List<PlanModel>>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchPlans();
});

final subscriptionStatusProvider =
    FutureProvider<SubscriptionStatusModel>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchSubscriptionStatus();
});

final performanceProvider = FutureProvider<PerformanceOverview>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchPerformanceOverview();
});

final competitionsProvider = FutureProvider<List<CompetitionModel>>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchCompetitions();
});

final searchProvider =
    FutureProvider.family<SearchResultModel, String>((ref, query) async {
  return ref.watch(fixturesRepositoryProvider).search(query);
});

final currentUserProvider = FutureProvider<UserModel?>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchCurrentUser();
});

final themeModeProvider = StateProvider<ThemeMode>((ref) {
  return ThemeMode.dark;
});

final favoritesProvider = FutureProvider<FavoritesModel>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchFavorites();
});

final preferencesProvider = FutureProvider<PreferencesModel>((ref) async {
  return ref.watch(fixturesRepositoryProvider).fetchPreferences();
});
