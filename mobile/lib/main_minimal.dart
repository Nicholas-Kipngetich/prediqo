import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';

const String apiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MinimalApp());
}

class MinimalApp extends StatelessWidget {
  const MinimalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Prediqo Test',
      theme: ThemeData.dark(useMaterial3: true),
      home: const MinimalHome(),
    );
  }
}

class MinimalHome extends StatefulWidget {
  const MinimalHome({super.key});

  @override
  State<MinimalHome> createState() => _MinimalHomeState();
}

class _MinimalHomeState extends State<MinimalHome> {
  String _status = 'Loading…';
  List<String> _fixtures = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final client = HttpClient();
      final uri = Uri.parse('$apiBaseUrl/api/v1/fixtures?page_size=5');
      final request = await client.getUrl(uri);
      final response = await request.close();
      final body = await response.transform(utf8.decoder).join();
      if (response.statusCode != 200) {
        _status = 'HTTP ${response.statusCode}: $body';
      } else {
        final decoded = jsonDecode(body) as Map<String, dynamic>;
        final items = decoded['items'] as List<dynamic>? ?? [];
        _fixtures = items
            .map((item) {
              final map = item as Map<String, dynamic>;
              return '${map['home_team']['name']} vs ${map['away_team']['name']}';
            })
            .toList();
        _status = 'OK — ${decoded['total']} fixtures';
      }
      client.close();
    } catch (error) {
      _status = 'ERROR: $error';
    }
    if (mounted) setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Prediqo Diagnostic')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(_status, style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 16),
            ..._fixtures.map((item) => Padding(
                  padding: const EdgeInsets.all(8),
                  child: Text(item),
                )),
          ],
        ),
      ),
    );
  }
}
