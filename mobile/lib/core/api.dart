import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/models.dart';
import 'app_config.dart';
import 'auth_service.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(
    BaseOptions(
      baseUrl: apiBaseUrl,
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 8),
    ),
  );
  dio.interceptors.add(_AuthInterceptor(ref));
  return dio;
});

class _AuthInterceptor extends Interceptor {
  _AuthInterceptor(this._ref);

  final Ref _ref;

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    var token = devAuthToken;
    try {
      token = await _ref.read(authServiceProvider).idToken() ?? devAuthToken;
    } catch (_) {
      // Firebase is not initialised in local widget tests; use the dev token.
    }
    options.headers['Authorization'] = 'Bearer $token';
    handler.next(options);
  }
}

final fixturesRepositoryProvider = Provider<FixturesRepository>((ref) {
  return FixturesRepository(ref.watch(dioProvider));
});

class FixturesRepository {
  final Dio _dio;

  FixturesRepository(this._dio);

  Future<FixturePage> fetchFixtures({
    String? status,
    int page = 1,
    int pageSize = 20,
  }) async {
    final query = <String, dynamic>{
      'page': page,
      'page_size': pageSize,
      if (status != null) 'status': status,
    };
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/fixtures',
      queryParameters: query,
    );
    return FixturePage.fromJson(response.data ?? {});
  }

  Future<FixturePage> fetchTrending({int page = 1, int pageSize = 20}) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/fixtures/trending',
      queryParameters: {'page': page, 'page_size': pageSize},
    );
    return FixturePage.fromJson(response.data ?? {});
  }

  Future<FixtureModel> fetchFixture(String id) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/fixtures/$id',
    );
    return FixtureModel.fromJson(response.data ?? {});
  }

  Future<List<PredictionModel>> fetchPredictionHistory({
    String? market,
    String? status,
    int limit = 50,
  }) async {
    final query = <String, dynamic>{
      'limit': limit,
      if (market != null) 'market': market,
      if (status != null) 'status': status,
    };
    final response = await _dio.get<List<dynamic>>(
      '/api/v1/predictions/history',
      queryParameters: query,
    );
    final raw = response.data ?? [];
    return raw
        .map((item) => PredictionModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<PredictionModel>> fetchPredictions(String market) async {
    final response = await _dio.get<List<dynamic>>(
      '/api/v1/predictions',
      queryParameters: {'market': market},
    );
    final raw = response.data ?? [];
    return raw
        .map((item) => PredictionModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<NotificationModel>> fetchNotifications() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/notifications');
    final raw = response.data ?? [];
    return raw
        .map((item) => NotificationModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<TokenBalanceModel> fetchTokenBalance() async {
    final response =
        await _dio.get<Map<String, dynamic>>('/api/v1/tokens/balance');
    return TokenBalanceModel.fromJson(response.data ?? {});
  }

  Future<List<TokenPackageModel>> fetchTokenPackages() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/tokens/packages');
    final raw = response.data ?? [];
    return raw
        .map((item) => TokenPackageModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<List<PlanModel>> fetchPlans() async {
    final response =
        await _dio.get<List<dynamic>>('/api/v1/subscriptions/plans');
    final raw = response.data ?? [];
    return raw
        .map((item) => PlanModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<SubscriptionStatusModel> fetchSubscriptionStatus() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/subscriptions/status',
    );
    return SubscriptionStatusModel.fromJson(response.data ?? {});
  }

  Future<PerformanceOverview> fetchPerformanceOverview() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/performance/overview',
    );
    return PerformanceOverview.fromJson(response.data ?? {});
  }

  Future<void> deleteAccount() async {
    await _dio.delete<void>('/api/v1/users/me');
  }

  Future<AuthResultModel> register(
    String email,
    String password,
    String? displayName,
  ) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/register',
      data: {
        'email': email,
        'password': password,
        if (displayName != null) 'display_name': displayName,
      },
    );
    return AuthResultModel.fromJson(response.data ?? {});
  }

  Future<AuthResultModel> login(String email, String password) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/login',
      data: {'email': email, 'password': password},
    );
    return AuthResultModel.fromJson(response.data ?? {});
  }

  Future<AnalysisModel> fetchAnalysis(String fixtureId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/fixtures/$fixtureId/analysis',
    );
    return AnalysisModel.fromJson(response.data ?? {});
  }

  Future<List<CompetitionModel>> fetchCompetitions() async {
    final response = await _dio.get<List<dynamic>>('/api/v1/competitions');
    final raw = response.data ?? [];
    return raw
        .map((item) => CompetitionModel.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<SearchResultModel> search(String query) async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/search',
      queryParameters: {'q': query, 'limit': 10},
    );
    return SearchResultModel.fromJson(response.data ?? {});
  }

  Future<UserModel?> fetchCurrentUser() async {
    try {
      final response = await _dio.post<Map<String, dynamic>>(
        '/api/v1/auth/verify',
      );
      final data = response.data;
      if (data == null) return null;
      return UserModel.fromJson(data);
    } on DioException {
      return null;
    }
  }

  Future<UserModel> updateProfile(Map<String, dynamic> changes) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/api/v1/users/me',
      data: changes,
    );
    return UserModel.fromJson(response.data ?? {});
  }

  Future<PreferencesModel> fetchPreferences() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/notifications/preferences',
    );
    return PreferencesModel.fromJson(response.data ?? {});
  }

  Future<PreferencesModel> updatePreferences(
    Map<String, dynamic> changes,
  ) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      '/api/v1/notifications/preferences',
      data: changes,
    );
    return PreferencesModel.fromJson(response.data ?? {});
  }

  Future<FavoritesModel> fetchFavorites() async {
    final response = await _dio.get<Map<String, dynamic>>(
      '/api/v1/users/me/favorites',
    );
    return FavoritesModel.fromJson(response.data ?? {});
  }

  Future<FavoritesModel> setFavorites(
    String kind,
    List<String> ids,
  ) async {
    final response = await _dio.put<Map<String, dynamic>>(
      '/api/v1/users/me/favorites/$kind',
      data: {'ids': ids},
    );
    return FavoritesModel.fromJson(response.data ?? {});
  }
}
