// ignore: deprecated_member_use
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/ads.dart';
import '../core/auth_service.dart';
import '../router/app_router.dart';
import '../state/providers.dart';
import '../theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AdService.instance.initialize();
  final auth = AuthService();
  await auth.init();
  runApp(
    ProviderScope(
      overrides: [authServiceProvider.overrideWithValue(auth)],
      child: const PrediqoApp(),
    ),
  );
}

class PrediqoApp extends ConsumerWidget {
  const PrediqoApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(adConsentLoadedProvider);
    final router = ref.watch(routerProvider);
    final themeMode = ref.watch(themeModeProvider);
    return MaterialApp.router(
      title: 'Prediqo',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: themeMode,
      routerConfig: router,
    );
  }
}
