import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../services/database_service.dart';

const String homeTitle = 'Lensa';
const String scanRoute = '/camera';
const String browseRoute = '/browse';
const double primaryCardPadding = 24;

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _artworkCount = 0;

  @override
  void initState() {
    super.initState();
    _loadArtworkCount();
  }

  Future<void> _loadArtworkCount() async {
    try {
      final int count = await DatabaseService.instance.getArtworkCount();
      if (!mounted) {
        return;
      }
      setState(() {
        _artworkCount = count;
      });
    } catch (error) {
      debugPrint('HomeScreen._loadArtworkCount failed: $error');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(homeTitle),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(primaryCardPadding),
                  child: Column(
                    children: <Widget>[
                      const Icon(Icons.museum, size: 80, color: Colors.indigo),
                      const SizedBox(height: 16),
                      const Text(
                        'Welcome to The Met',
                        style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '$_artworkCount artworks ready to explore',
                        style: TextStyle(
                          fontSize: 16,
                          color: Colors.grey.shade700,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: () => Navigator.pushNamed(context, scanRoute),
                icon: const Icon(Icons.camera_alt, size: 28),
                label: const Text('Scan Artwork', style: TextStyle(fontSize: 18)),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 20),
                  backgroundColor: Colors.indigo,
                  foregroundColor: Colors.white,
                ),
              ),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: () => Navigator.pushNamed(context, browseRoute),
                icon: const Icon(Icons.grid_view),
                label: const Text('Browse Collection'),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  side: const BorderSide(color: Colors.indigo, width: 2),
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.indigo.shade50,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: const <Widget>[
                    Text(
                      'Tips for better recognition:',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                    ),
                    SizedBox(height: 8),
                    _TipRow(text: 'Point camera directly at artwork'),
                    _TipRow(text: 'Ensure bright, even lighting'),
                    _TipRow(text: 'Capture the artwork fully in frame'),
                    _TipRow(text: 'Hold steady while analyzing'),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _TipRow extends StatelessWidget {
  const _TipRow({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 4),
      child: Row(
        children: <Widget>[
          const Icon(Icons.check_circle, size: 16, color: Colors.indigo),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(fontSize: 14),
            ),
          ),
        ],
      ),
    );
  }
}
