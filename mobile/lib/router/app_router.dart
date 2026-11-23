import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../screens/auth_screen.dart';
import '../screens/home_screen.dart';
import '../screens/match_detail_screen.dart';
import '../screens/matches_screen.dart';
import '../screens/other_screens.dart';
import '../screens/splash_screen.dart';

final routerProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/splash',
    routes: [
      GoRoute(
        path: '/splash',
        builder: (context, state) => const SplashScreen(),
      ),
      GoRoute(
        path: '/auth',
        builder: (context, state) => const AuthScreen(),
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const HomeScreen(),
      ),
      GoRoute(
        path: '/matches',
        builder: (context, state) => const MatchesScreen(),
      ),
      GoRoute(
        path: '/matches/:id',
        builder: (context, state) {
          final id = state.pathParameters['id'] ?? '';
          return MatchDetailScreen(fixtureId: id);
        },
      ),
      GoRoute(
        path: '/predictions',
        builder: (context, state) => const PredictionsScreen(),
      ),
      GoRoute(
        path: '/performance',
        builder: (context, state) => const PerformanceScreen(),
      ),
      GoRoute(
        path: '/profile',
        builder: (context, state) => const ProfileScreen(),
      ),
      GoRoute(
        path: '/vip',
        builder: (context, state) => const VipScreen(),
      ),
      GoRoute(
        path: '/tokens',
        builder: (context, state) => const TokenStoreScreen(),
      ),
      GoRoute(
        path: '/notifications',
        builder: (context, state) => const NotificationsScreen(),
      ),
    ],
  );
});
