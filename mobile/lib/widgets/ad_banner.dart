import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

import '../core/ads.dart';
import '../state/providers.dart';

class AdBanner extends ConsumerStatefulWidget {
  const AdBanner({super.key});

  @override
  ConsumerState<AdBanner> createState() => _AdBannerState();
}

class _AdBannerState extends ConsumerState<AdBanner> {
  BannerAd? _banner;
  bool _loaded = false;
  bool _loading = false;

  @override
  void dispose() {
    _banner?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final configAsync = ref.watch(adsConfigProvider);
    final consent = ref.watch(adConsentProvider);
    final userAsync = ref.watch(currentUserProvider);

    return configAsync.when(
      data: (config) {
        final isVip = userAsync.value?.isVip ?? false;
        if (!AdService.instance.canShow(
          config,
          isVip,
          consent,
          'banner_home',
        )) {
          return const SizedBox.shrink();
        }
        final placement = config.placement('banner_home')!;
        _banner ??= BannerAd(
          adUnitId: placement.unitId,
          size: AdSize.banner,
          request: AdRequest(),
          listener: BannerAdListener(
            onAdLoaded: (ad) => setState(() {
              _loaded = true;
              _loading = false;
            }),
            onAdFailedToLoad: (ad, error) {
              ad.dispose();
              _banner = null;
              _loaded = false;
              _loading = false;
            },
          ),
        );
        if (!_loaded && !_loading) {
          _loading = true;
          _banner!.load();
        }
        if (!_loaded) return const SizedBox.shrink();
        return SizedBox(
          height: _banner!.size.height.toDouble(),
          child: AdWidget(ad: _banner!),
        );
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }
}
