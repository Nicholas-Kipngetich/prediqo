import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/models.dart';

const apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

const devAuthToken = String.fromEnvironment(
  'DEV_AUTH_TOKEN',
  defaultValue: 'prediqo-dev-token',
);

final dioProvider = Provider<Dio>((ref) {
  return Dio(
    BaseOptions(
      baseUrl: apiBaseUrl,
      connectTimeout: const Duration(seconds: 8),
      receiveTimeout: const Duration(seconds: 8),
      headers: {'Authorization': 'Bearer $devAuthToken'},
    ),
  );
});

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
}
