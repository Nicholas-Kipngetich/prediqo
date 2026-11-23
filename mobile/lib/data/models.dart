class CompetitionModel {
  final String id;
  final String name;
  final String? country;
  final int? tier;
  final bool isSampleData;

  CompetitionModel({
    required this.id,
    required this.name,
    this.country,
    this.tier,
    this.isSampleData = false,
  });

  factory CompetitionModel.fromJson(Map<String, dynamic> json) {
    return CompetitionModel(
      id: json['id'] as String,
      name: json['name'] as String,
      country: json['country'] as String?,
      tier: json['tier'] as int?,
      isSampleData: json['is_sample_data'] as bool? ?? false,
    );
  }
}

class TeamModel {
  final String id;
  final String name;
  final String? shortName;
  final String? logoUrl;
  final bool isSampleData;

  TeamModel({
    required this.id,
    required this.name,
    this.shortName,
    this.logoUrl,
    this.isSampleData = false,
  });

  factory TeamModel.fromJson(Map<String, dynamic> json) {
    return TeamModel(
      id: json['id'] as String,
      name: json['name'] as String,
      shortName: json['short_name'] as String?,
      logoUrl: json['logo_url'] as String?,
      isSampleData: json['is_sample_data'] as bool? ?? false,
    );
  }
}

class FixtureModel {
  final String id;
  final CompetitionModel competition;
  final TeamModel homeTeam;
  final TeamModel awayTeam;
  final DateTime kickoffUtc;
  final String status;
  final int? homeScore;
  final int? awayScore;
  final bool isSampleData;

  FixtureModel({
    required this.id,
    required this.competition,
    required this.homeTeam,
    required this.awayTeam,
    required this.kickoffUtc,
    required this.status,
    this.homeScore,
    this.awayScore,
    this.isSampleData = false,
  });

  factory FixtureModel.fromJson(Map<String, dynamic> json) {
    return FixtureModel(
      id: json['id'] as String,
      competition: CompetitionModel.fromJson(
        json['competition'] as Map<String, dynamic>,
      ),
      homeTeam: TeamModel.fromJson(json['home_team'] as Map<String, dynamic>),
      awayTeam: TeamModel.fromJson(json['away_team'] as Map<String, dynamic>),
      kickoffUtc: DateTime.parse(json['kickoff_utc'] as String).toLocal(),
      status: json['status'] as String,
      homeScore: json['home_score'] as int?,
      awayScore: json['away_score'] as int?,
      isSampleData: json['is_sample_data'] as bool? ?? false,
    );
  }

  String get statusLabel {
    switch (status) {
      case 'FINISHED':
        return 'FT';
      case 'LIVE':
      case '1H':
      case '2H':
        return 'LIVE';
      case 'POSTPONED':
      case 'PST':
        return 'Postponed';
      case 'CANCELLED':
      case 'CANC':
        return 'Cancelled';
      default:
        return 'Scheduled';
    }
  }

  String get kickoffLabel {
    final hour = kickoffUtc.hour.toString().padLeft(2, '0');
    final minute = kickoffUtc.minute.toString().padLeft(2, '0');
    return '$hour:$minute';
  }
}

class FixturePage {
  final List<FixtureModel> items;
  final int total;

  FixturePage({required this.items, required this.total});

  factory FixturePage.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return FixturePage(
      items: rawItems
          .map((item) => FixtureModel.fromJson(item as Map<String, dynamic>))
          .toList(),
      total: json['total'] as int? ?? 0,
    );
  }
}

class TokenPackageModel {
  final String id;
  final String name;
  final int tokens;
  final int priceMinor;
  final String currency;

  TokenPackageModel({
    required this.id,
    required this.name,
    required this.tokens,
    required this.priceMinor,
    required this.currency,
  });

  factory TokenPackageModel.fromJson(Map<String, dynamic> json) {
    return TokenPackageModel(
      id: json['id'] as String,
      name: json['name'] as String,
      tokens: json['tokens'] as int? ?? 0,
      priceMinor: json['price_minor'] as int? ?? 0,
      currency: json['currency'] as String? ?? 'KES',
    );
  }

  String get priceLabel => '${currency} ${(priceMinor / 100).toStringAsFixed(0)}';
}

class TokenBalanceModel {
  final int balance;

  TokenBalanceModel({required this.balance});

  factory TokenBalanceModel.fromJson(Map<String, dynamic> json) {
    return TokenBalanceModel(balance: json['balance'] as int? ?? 0);
  }
}

class PlanModel {
  final String id;
  final String code;
  final String interval;
  final int priceMinor;
  final String currency;

  PlanModel({
    required this.id,
    required this.code,
    required this.interval,
    required this.priceMinor,
    required this.currency,
  });

  factory PlanModel.fromJson(Map<String, dynamic> json) {
    return PlanModel(
      id: json['id'] as String,
      code: json['code'] as String,
      interval: json['interval'] as String,
      priceMinor: json['price_minor'] as int? ?? 0,
      currency: json['currency'] as String? ?? 'KES',
    );
  }

  String get priceLabel => '${currency} ${(priceMinor / 100).toStringAsFixed(0)}';
}

class SubscriptionStatusModel {
  final bool isVip;
  final String? status;
  final String? planCode;

  SubscriptionStatusModel({
    required this.isVip,
    this.status,
    this.planCode,
  });

  factory SubscriptionStatusModel.fromJson(Map<String, dynamic> json) {
    return SubscriptionStatusModel(
      isVip: json['is_vip'] as bool? ?? false,
      status: json['status'] as String?,
      planCode: json['plan_code'] as String?,
    );
  }
}

class PerformanceOverview {
  final int totalPredictions;
  final int settledPredictions;
  final int correct;
  final int incorrect;
  final int pending;
  final int voidCount;
  final double? accuracy;
  final int sampleSize;

  PerformanceOverview({
    required this.totalPredictions,
    required this.settledPredictions,
    required this.correct,
    required this.incorrect,
    required this.pending,
    required this.voidCount,
    required this.accuracy,
    required this.sampleSize,
  });

  factory PerformanceOverview.fromJson(Map<String, dynamic> json) {
    final rawAccuracy = json['accuracy'];
    return PerformanceOverview(
      totalPredictions: json['total_predictions'] as int? ?? 0,
      settledPredictions: json['settled_predictions'] as int? ?? 0,
      correct: json['correct'] as int? ?? 0,
      incorrect: json['incorrect'] as int? ?? 0,
      pending: json['pending'] as int? ?? 0,
      voidCount: json['void'] as int? ?? 0,
      accuracy: rawAccuracy is num ? rawAccuracy.toDouble() : null,
      sampleSize: json['sample_size'] as int? ?? 0,
    );
  }

  String get accuracyLabel {
    if (accuracy == null) return 'Not yet available';
    return '${(accuracy! * 100).toStringAsFixed(1)}%';
  }
}

class PredictionModel {
  final String id;
  final String fixtureId;
  final String market;
  final String modelVersion;
  final Map<String, int> probabilitiesBp;
  final String selectedOutcome;
  final String status;
  final bool isSampleData;

  PredictionModel({
    required this.id,
    required this.fixtureId,
    required this.market,
    required this.modelVersion,
    required this.probabilitiesBp,
    required this.selectedOutcome,
    required this.status,
    required this.isSampleData,
  });

  factory PredictionModel.fromJson(Map<String, dynamic> json) {
    final raw = json['probabilities_bp'] as Map<String, dynamic>? ?? {};
    return PredictionModel(
      id: json['id'] as String,
      fixtureId: json['fixture_id'] as String,
      market: json['market'] as String,
      modelVersion: json['model_version'] as String,
      probabilitiesBp: raw.map(
        (key, value) => MapEntry(key, (value as num).toInt()),
      ),
      selectedOutcome: json['selected_outcome'] as String,
      status: json['status'] as String,
      isSampleData: json['is_sample_data'] as bool? ?? false,
    );
  }
}

class UserModel {
  final String id;
  final String? email;
  final String? displayName;
  final List<String> roles;
  final bool isVip;

  UserModel({
    required this.id,
    this.email,
    this.displayName,
    required this.roles,
    required this.isVip,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) {
    final rawRoles = json['roles'] as List<dynamic>? ?? [];
    return UserModel(
      id: json['id'] as String,
      email: json['email'] as String?,
      displayName: json['display_name'] as String?,
      roles: rawRoles.map((role) => role as String).toList(),
      isVip: json['is_vip'] as bool? ?? false,
    );
  }
}
