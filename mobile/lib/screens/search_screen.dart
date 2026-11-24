import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../state/providers.dart';
import '../theme/app_theme.dart';
import '../widgets/app_scaffold.dart';
import '../widgets/design_system.dart';

class SearchScreen extends ConsumerStatefulWidget {
  const SearchScreen({super.key});

  @override
  ConsumerState<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends ConsumerState<SearchScreen> {
  final _controller = TextEditingController();
  String _query = '';

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _search(String value) {
    setState(() => _query = value.trim());
  }

  @override
  Widget build(BuildContext context) {
    final result = _query.length < 2
        ? null
        : ref.watch(searchProvider(_query));

    return AppScaffold(
      title: 'Search',
      selectedIndex: 1,
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              controller: _controller,
              decoration: InputDecoration(
                prefixIcon: const Icon(Icons.search),
                hintText: 'Competition, team or fixture',
                suffixIcon: _query.isEmpty
                    ? null
                    : IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _controller.clear();
                          _search('');
                        },
                      ),
              ),
              onSubmitted: _search,
            ),
          ),
          Expanded(
            child: _query.length < 2
                ? const EmptyState(
                    title: 'Search',
                    message: 'Type at least two characters.',
                    icon: Icons.search,
                  )
                : result!.when(
                    data: (data) {
                      if (data.competitions.isEmpty &&
                          data.teams.isEmpty &&
                          data.fixtures.isEmpty) {
                        return const EmptyState(
                          title: 'No results',
                          message: 'Try a different term.',
                          icon: Icons.search_off,
                        );
                      }
                      return ListView(
                        padding: const EdgeInsets.symmetric(horizontal: 12),
                        children: [
                          if (data.competitions.isNotEmpty) ...[
                            const SectionHeader(title: 'Competitions'),
                            ...data.competitions.map(
                              (item) => Card(
                                child: ListTile(title: Text(item.name)),
                              ),
                            ),
                          ],
                          if (data.teams.isNotEmpty) ...[
                            const SectionHeader(title: 'Teams'),
                            ...data.teams.map(
                              (item) => Card(
                                child: ListTile(title: Text(item.name)),
                              ),
                            ),
                          ],
                          if (data.fixtures.isNotEmpty) ...[
                            const SectionHeader(title: 'Fixtures'),
                            ...data.fixtures.map(
                              (fixture) => MatchCard(
                                fixture: fixture,
                                onTap: () => context.go('/matches/${fixture.id}'),
                              ),
                            ),
                          ],
                        ],
                      );
                    },
                    loading: () => const LoadingState(),
                    error: (error, _) => ErrorState(
                      error: error,
                      onRetry: () => ref.invalidate(searchProvider(_query)),
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}
