import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'api.dart';

class AdPlacementConfig {
  final String key;
  final String adType;
  final String unitId;
  final bool enabled;
  final int frequencyCapPerHour;
  final bool vipExcluded;

  AdPlacementConfig({
    required this.key,
    required this.adType,
    required this.unitId,
    required this.enabled,
    required this.frequencyCapPerHour,
    required this.vipExcluded,
  });

  factory AdPlacementConfig.fromJson(Map<String, dynamic> json) {
    return AdPlacementConfig(
      key: json['key'] as String,
      adType: json['ad_type'] as String,
      unitId: json['unit_id'] as String? ?? '',
      enabled: json['enabled'] as bool? ?? false,
      frequencyCapPerHour: json['frequency_cap_per_hour'] as int? ?? 2,
      vipExcluded: json['vip_excluded'] as bool? ?? true,
    );
  }
}

class AdsConfig {
  final bool enabled;
  final String appId;
  final List<AdPlacementConfig> placements;

  AdsConfig({
    required this.enabled,
    required this.appId,
    required this.placements,
  });

  factory AdsConfig.fromJson(Map<String, dynamic> json) {
    final raw = json['placements'] as List<dynamic>? ?? [];
    return AdsConfig(
      enabled: json['ads_enabled'] as bool? ?? false,
      appId: json['admob_app_id_android'] as String? ?? '',
      placements: raw
          .map((item) => AdPlacementConfig.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }

  AdPlacementConfig? placement(String key) {
    for (final item in placements) {
      if (item.key == key) return item;
    }
    return null;
  }
}

final adsConfigProvider = FutureProvider<AdsConfig>((ref) async {
  final response = await ref.watch(dioProvider).get<Map<String, dynamic>>(
        '/api/v1/config/client',
      );
  return AdsConfig.fromJson(response.data ?? {});
});

final adConsentProvider = StateProvider<bool>((ref) => false);

final adConsentLoadedProvider = FutureProvider<bool>((ref) async {
  final prefs = await SharedPreferences.getInstance();
  // Ads are enabled in this build; a stored decline is still respected.
  final granted = prefs.getBool('ad_consent') ?? true;
  ref.read(adConsentProvider.notifier).state = granted;
  return granted;
});

class AdService {
  static final AdService instance = AdService._();

  AdService._();

  Future<void> initialize() async {
    await MobileAds.instance.initialize();
  }

  Future<void> setConsent(bool granted) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('ad_consent', granted);
  }

  bool canShow(
    AdsConfig config,
    bool isVip,
    bool consent,
    String key,
  ) {
    final placement = config.placement(key);
    if (placement == null || !config.enabled || !placement.enabled) {
      return false;
    }
    if (consent == false) return false;
    if (placement.vipExcluded && isVip) return false;
    return true;
  }

  Future<void> showAppOpen(
    AdsConfig config,
    bool isVip,
    bool consent,
  ) async {
    if (!canShow(config, isVip, consent, 'app_open')) return;
    final placement = config.placement('app_open')!;
    final ad = AppOpenAd(
      adUnitId: placement.unitId,
      request: AdRequest(),
      onAdLoaded: (loaded) => loaded.show(),
      onAdFailedToLoad: (failed, error) => failed.dispose(),
    );
    await ad.load();
  }

  Future<InterstitialAd?> loadInterstitial(
    AdsConfig config,
    bool isVip,
    bool consent,
  ) async {
    if (!canShow(config, isVip, consent, 'interstitial_navigation')) {
      return null;
    }
    final placement = config.placement('interstitial_navigation')!;
    return InterstitialAd.load(
      adUnitId: placement.unitId,
      request: AdRequest(),
    );
  }
}
