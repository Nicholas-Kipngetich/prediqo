// Flutter 3.50 deprecates material.dart in favour of material_ui.dart. Keep the
// established import until the design system is migrated.
// ignore: deprecated_member_use
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/ads.dart';
import 'core/firebase_options.dart';
import 'router/app_router.dart';
import 'state/providers.dart';
import 'theme/app_theme.dart';

const bool skipFirebase = bool.fromEnvironment(
  'SKIP_FIREBASE',
  defaultValue: false,
);
const bool skipAds = bool.fromEnvironment(
  'SKIP_ADS',
  defaultValue: false,
);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (!skipFirebase) {
    try {
      await Firebase.initializeApp(
        options: DefaultFirebaseOptions.currentPlatform,
      );
    } catch (_) {
      // Production builds must initialise Firebase with real config.
    }
  }
  if (!skipAds) {
    try {
      await AdService.instance.initialize();
    } catch (_) {
      // Ads are optional; the app works without AdMob available.
    }
  }
  runApp(const ProviderScope(child: PrediqoApp()));
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
