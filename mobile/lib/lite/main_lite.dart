// ignore: deprecated_member_use
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/ads.dart';
import '../router/app_router.dart';
import '../theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await AdService.instance.initialize();
  runApp(const ProviderScope(child: PrediqoApp()));
}

class PrediqoApp extends ConsumerWidget {
  const PrediqoApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(adConsentLoadedProvider);
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'Prediqo',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: ThemeMode.dark,
      routerConfig: router,
    );
  }
}
