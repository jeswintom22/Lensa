import 'dart:async';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/artwork.dart';
import '../services/database_service.dart';
import 'artwork_detail_screen.dart';

const String allDepartmentsLabel = 'All';
const Duration searchDebounceDuration = Duration(milliseconds: 300);
const int browseGridCrossAxisCount = 2;
const double browseGridSpacing = 12;
const double browseGridAspectRatio = 0.66;

class BrowseScreen extends StatefulWidget {
  const BrowseScreen({super.key});

  @override
  State<BrowseScreen> createState() => _BrowseScreenState();
}

class _BrowseScreenState extends State<BrowseScreen> {
  final TextEditingController _searchController = TextEditingController();

  Timer? _debounce;
  List<Artwork> _allArtworks = <Artwork>[];
  List<Artwork> _filteredArtworks = <Artwork>[];
  List<String> _departments = <String>[];
  bool _isLoading = true;
  String _selectedDepartment = allDepartmentsLabel;
  String _searchQuery = '';

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    setState(() {
      _isLoading = true;
    });

    try {
      final List<Artwork> artworks = await DatabaseService.instance.getAllArtworks();
      final List<String> departments = await DatabaseService.instance.getDepartments();
      if (!mounted) {
        return;
      }

      setState(() {
        _allArtworks = artworks;
        _departments = departments;
        _isLoading = false;
      });
      _applyFilters();
    } catch (error) {
      debugPrint('BrowseScreen._loadData failed: $error');
      if (!mounted) {
        return;
      }
      setState(() {
        _isLoading = false;
        _allArtworks = <Artwork>[];
        _filteredArtworks = <Artwork>[];
      });
    }
  }

  void _onSearchChanged(String value) {
    _debounce?.cancel();
    _debounce = Timer(searchDebounceDuration, () {
      if (!mounted) {
        return;
      }
      setState(() {
        _searchQuery = value.trim();
      });
      _applyFilters();
    });
  }

  void _onDepartmentSelected(String department) {
    setState(() {
      _selectedDepartment = department;
    });
    _applyFilters();
  }

  void _applyFilters() {
    final String query = _searchQuery.toLowerCase();
    final bool isAllDepartments = _selectedDepartment == allDepartmentsLabel;

    final List<Artwork> filtered = _allArtworks.where((Artwork artwork) {
      final bool matchesDepartment =
          isAllDepartments || artwork.department == _selectedDepartment;

      final String title = artwork.title.toLowerCase();
      final String artist = artwork.artist.toLowerCase();
      final bool matchesQuery = query.isEmpty || title.contains(query) || artist.contains(query);

      return matchesDepartment && matchesQuery;
    }).toList();

    if (!mounted) {
      return;
    }
    setState(() {
      _filteredArtworks = filtered;
    });
  }

  PreferredSizeWidget _buildAppBar() {
    return AppBar(
      titleSpacing: 0,
      title: Padding(
        padding: const EdgeInsets.only(right: 12),
        child: TextField(
          controller: _searchController,
          onChanged: _onSearchChanged,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: 'Search title or artist',
            hintStyle: TextStyle(color: Colors.white.withOpacity(0.8)),
            border: InputBorder.none,
            prefixIcon: const Icon(Icons.search, color: Colors.white),
            suffixIcon: _searchQuery.isEmpty
                ? null
                : IconButton(
                    icon: const Icon(Icons.close, color: Colors.white),
                    onPressed: () {
                      _searchController.clear();
                      _onSearchChanged('');
                    },
                  ),
          ),
        ),
      ),
      bottom: PreferredSize(
        preferredSize: const Size.fromHeight(56),
        child: SizedBox(
          height: 56,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            children: <Widget>[
              _buildDepartmentChip(allDepartmentsLabel),
              for (final String department in _departments)
                _buildDepartmentChip(department),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDepartmentChip(String label) {
    final bool selected = _selectedDepartment == label;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        selected: selected,
        label: Text(label),
        onSelected: (_) => _onDepartmentSelected(label),
        selectedColor: Colors.indigo.shade100,
        checkmarkColor: Colors.indigo.shade800,
      ),
    );
  }

  Widget _buildGrid() {
    if (_isLoading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_filteredArtworks.isEmpty) {
      return RefreshIndicator(
        onRefresh: _loadData,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: <Widget>[
            SizedBox(
              height: MediaQuery.of(context).size.height * 0.55,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const <Widget>[
                  Icon(Icons.image_not_supported, size: 64, color: Colors.grey),
                  SizedBox(height: 12),
                  Text(
                    'No artworks found',
                    style: TextStyle(fontSize: 16, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      child: GridView.builder(
        padding: const EdgeInsets.all(12),
        physics: const AlwaysScrollableScrollPhysics(),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: browseGridCrossAxisCount,
          crossAxisSpacing: browseGridSpacing,
          mainAxisSpacing: browseGridSpacing,
          childAspectRatio: browseGridAspectRatio,
        ),
        itemCount: _filteredArtworks.length,
        itemBuilder: (BuildContext context, int index) {
          final Artwork artwork = _filteredArtworks[index];
          return _ArtworkCard(
            artwork: artwork,
            onTap: () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (BuildContext context) => ArtworkDetailScreen(artwork: artwork),
                ),
              );
            },
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: _buildAppBar(),
      body: _buildGrid(),
    );
  }
}

class _ArtworkCard extends StatelessWidget {
  const _ArtworkCard({required this.artwork, required this.onTap});

  final Artwork artwork;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final String heroTag = 'artwork-hero-${artwork.id}';

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Card(
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Expanded(
              child: Hero(
                tag: heroTag,
                child: AspectRatio(
                  aspectRatio: 1,
                  child: CachedNetworkImage(
                    imageUrl: artwork.imageUrl,
                    fit: BoxFit.cover,
                    width: double.infinity,
                    placeholder: (BuildContext context, String _) {
                      return Container(
                        color: Colors.grey.shade200,
                        alignment: Alignment.center,
                        child: const CircularProgressIndicator(strokeWidth: 2),
                      );
                    },
                    errorWidget: (BuildContext context, String _, Object __) {
                      return Container(
                        color: Colors.grey.shade300,
                        alignment: Alignment.center,
                        child: const Icon(
                          Icons.broken_image,
                          color: Colors.grey,
                        ),
                      );
                    },
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(10, 10, 10, 8),
              child: Text(
                artwork.title,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(10, 0, 10, 10),
              child: Text(
                artwork.artist,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 12, color: Colors.grey.shade700),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
