import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:prediqo/main.dart';

void main() {
  testWidgets('Prediqo splash shows branding', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: PrediqoApp()));

    expect(find.text('Prediqo'), findsOneWidget);
    expect(
      find.text('Predict Smarter. Understand Deeper.'),
      findsOneWidget,
    );
    expect(find.byIcon(Icons.insights), findsOneWidget);
  });
}
