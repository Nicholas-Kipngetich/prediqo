import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:prediqo/main.dart';

void main() {
  testWidgets('Prediqo app renders the home screen', (tester) async {
    await tester.pumpWidget(
      const ProviderScope(
        overrides: [
          healthProvider.overrideWith(
            (ref) async => <String, dynamic>{'status': 'ok'},
          ),
        ],
        child: PrediqoApp(),
      ),
    );

    expect(find.text('Prediqo'), findsOneWidget);
    expect(
      find.text('Predict Smarter. Understand Deeper.'),
      findsOneWidget,
    );
    await tester.pumpAndSettle();
    expect(find.textContaining('API status: ok'), findsOneWidget);
  });
}
