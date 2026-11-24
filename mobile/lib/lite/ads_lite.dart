import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api.dart';

const bool adsLocallyDisabled = true;

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
      key: json['key'] as String? ?? '',
      adType: json['ad_type'] as String? ?? '',
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
          .map((item) =>
              AdPlacementConfig.fromJson(item as Map<String, dynamic>))
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

final adConsentProvider = StateProvider<bool>((ref) => true);

final adConsentLoadedProvider = FutureProvider<bool>((ref) async {
  ref.read(adConsentProvider.notifier).state = true;
  return true;
});

class AdService {
  static final AdService instance = AdService._();

  AdService._();

  Future<void> initialize() async {}

  Future<void> setConsent(bool granted) async {}

  bool canShow(
    AdsConfig config,
    bool isVip,
    bool consent,
    String key,
  ) {
    return false;
  }

  Future<void> showAppOpen(
    AdsConfig config,
    bool isVip,
    bool consent,
  ) async {}
}
