import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

/// Override at build time, e.g.:
/// flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

final dioProvider = Provider<Dio>((ref) {
  return Dio(
    BaseOptions(
      baseUrl: apiBaseUrl,
      connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 5),
    ),
  );
});

final healthProvider = FutureProvider<Map<String, dynamic>>((ref) async {
  final response = await ref.read(dioProvider).get<Map<String, dynamic>>('/health');
  return response.data ?? <String, dynamic>{};
});

void main() {
  runApp(const ProviderScope(child: PrediqoApp()));
}

class PrediqoApp extends StatelessWidget {
  const PrediqoApp({super.key});

  @override
  Widget build(BuildContext context) {
    final router = GoRouter(
      routes: [
        GoRoute(
          path: '/',
          builder: (context, state) => const HomeScreen(),
        ),
      ],
    );

    return MaterialApp.router(
      title: 'Prediqo',
      debugShowCheckedModeBanner: false,
      themeMode: ThemeMode.dark,
      theme: _buildTheme(Brightness.dark),
      darkTheme: _buildTheme(Brightness.dark),
      routerConfig: router,
    );
  }

  ThemeData _buildTheme(Brightness brightness) {
    final colorScheme = ColorScheme.fromSeed(
      seedColor: const Color(0xFF39FF14),
      brightness: brightness,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: colorScheme,
      scaffoldBackgroundColor: const Color(0xFF0B0B0D),
    );
  }
}

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final health = ref.watch(healthProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Prediqo'),
        actions: const [
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 16),
            child: Icon(Icons.notifications_none),
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Predict Smarter. Understand Deeper.',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 24),
            health.when(
              data: (data) => Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text('API status: ${data['status'] ?? 'unknown'}'),
                ),
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, stack) => Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text('Backend unavailable: $error'),
                ),
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: const NavigationBar(
        destinations: [
          NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.sports_soccer_outlined), label: 'Matches'),
          NavigationDestination(icon: Icon(Icons.insights_outlined), label: 'Predictions'),
          NavigationDestination(icon: Icon(Icons.bar_chart_outlined), label: 'Performance'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Profile'),
        ],
        selectedIndex: 0,
      ),
    );
  }
}
