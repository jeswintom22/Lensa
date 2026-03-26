import 'dart:async';

import 'package:audioplayers/audioplayers.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/artwork.dart';

const String favoritesPreferenceKey = 'favorite_artwork_ids';
const String metCollectionUrlPrefix = 'https://www.metmuseum.org/art/collection/search/';
const String listenHeading = 'Listen to narration';
const String highConfidenceLabel = 'High confidence match';
const String moderateConfidenceLabel = 'Moderate confidence';
const String lowConfidenceLabel = 'Low confidence';
const Color highConfidenceColor = Color(0xFF2E7D32);
const Color moderateConfidenceColor = Color(0xFFF9A825);
const Color lowConfidenceColor = Color(0xFFC62828);
const String audioAssetSubdirectory = 'audio';

class ArtworkDetailScreen extends StatefulWidget {
  const ArtworkDetailScreen({
    super.key,
    required this.artwork,
    this.confidence,
  });

  final Artwork artwork;
  final double? confidence;

  @override
  State<ArtworkDetailScreen> createState() => _ArtworkDetailScreenState();
}

class _ArtworkDetailScreenState extends State<ArtworkDetailScreen> {
  final AudioPlayer _audioPlayer = AudioPlayer();
  StreamSubscription<PlayerState>? _playerStateSubscription;
  StreamSubscription<Duration>? _durationSubscription;

  Duration _duration = Duration.zero;
  PlayerState _playerState = PlayerState.stopped;
  bool _isFavorite = false;
  bool _isAudioPreparing = false;

  @override
  void initState() {
    super.initState();
    _loadFavoriteState();
    _listenToPlayerState();
    _prepareAudioIfNeeded();
  }

  @override
  void dispose() {
    _playerStateSubscription?.cancel();
    _durationSubscription?.cancel();
    _audioPlayer.dispose();
    super.dispose();
  }

  Future<void> _loadFavoriteState() async {
    try {
      final SharedPreferences preferences = await SharedPreferences.getInstance();
      final List<String> ids = preferences.getStringList(favoritesPreferenceKey) ?? <String>[];
      if (!mounted) {
        return;
      }
      setState(() {
        _isFavorite = ids.contains(widget.artwork.id.toString());
      });
    } catch (error) {
      debugPrint('ArtworkDetailScreen._loadFavoriteState failed: $error');
    }
  }

  void _listenToPlayerState() {
    _playerStateSubscription =
        _audioPlayer.onPlayerStateChanged.listen((PlayerState state) {
      if (!mounted) {
        return;
      }
      setState(() {
        _playerState = state;
      });
    });

    _durationSubscription =
        _audioPlayer.onDurationChanged.listen((Duration value) {
      if (!mounted) {
        return;
      }
      setState(() {
        _duration = value;
      });
    });
  }

  Future<void> _prepareAudioIfNeeded() async {
    final String? rawAudioPath = widget.artwork.audioFilePath;
    if (rawAudioPath == null || rawAudioPath.trim().isEmpty) {
      return;
    }

    setState(() {
      _isAudioPreparing = true;
    });

    try {
      final String sourcePath = _normalizedAssetAudioPath(rawAudioPath);
      await _audioPlayer.setSourceAsset(sourcePath);
    } catch (error) {
      debugPrint('ArtworkDetailScreen._prepareAudioIfNeeded failed: $error');
    } finally {
      if (!mounted) {
        return;
      }
      setState(() {
        _isAudioPreparing = false;
      });
    }
  }

  Future<void> _toggleFavorite() async {
    try {
      final SharedPreferences preferences = await SharedPreferences.getInstance();
      final List<String> ids = preferences.getStringList(favoritesPreferenceKey) ?? <String>[];
      final String currentId = widget.artwork.id.toString();

      if (ids.contains(currentId)) {
        ids.remove(currentId);
      } else {
        ids.add(currentId);
      }

      await preferences.setStringList(favoritesPreferenceKey, ids);
      if (!mounted) {
        return;
      }
      setState(() {
        _isFavorite = ids.contains(currentId);
      });
    } catch (error) {
      debugPrint('ArtworkDetailScreen._toggleFavorite failed: $error');
    }
  }

  Future<void> _shareArtwork() async {
    final String url = _metArtworkUrl();
    final String message = '${widget.artwork.title}\n$url';
    try {
      await Share.share(message);
    } catch (error) {
      debugPrint('ArtworkDetailScreen._shareArtwork failed: $error');
    }
  }

  Future<void> _openMetWebsite() async {
    final Uri uri = Uri.parse(_metArtworkUrl());
    try {
      final bool launched = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!launched && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Unable to open the Met website link.')),
        );
      }
    } catch (error) {
      debugPrint('ArtworkDetailScreen._openMetWebsite failed: $error');
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Unable to open the Met website link.')),
      );
    }
  }

  Future<void> _toggleAudio() async {
    try {
      if (_playerState == PlayerState.playing) {
        await _audioPlayer.pause();
      } else {
        await _audioPlayer.resume();
      }
    } catch (error) {
      debugPrint('ArtworkDetailScreen._toggleAudio failed: $error');
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Unable to play narration audio.')),
      );
    }
  }

  String _metArtworkUrl() {
    return '$metCollectionUrlPrefix${widget.artwork.metObjectId}';
  }

  String _normalizedAssetAudioPath(String rawAudioPath) {
    final String normalized = rawAudioPath.replaceAll('\\', '/').trim();
    final String fileName = normalized.split('/').last;
    return '$audioAssetSubdirectory/$fileName';
  }

  String _metadataLine() {
    final List<String> values = <String>[
      widget.artwork.date,
      widget.artwork.medium,
      widget.artwork.department,
    ].where((String value) => value.trim().isNotEmpty).toList();
    return values.join(' • ');
  }

  @override
  Widget build(BuildContext context) {
    final String heroTag = 'artwork-hero-${widget.artwork.id}';

    return Scaffold(
      appBar: AppBar(
        title: const Text('Artwork Details'),
        actions: <Widget>[
          IconButton(
            onPressed: _shareArtwork,
            icon: const Icon(Icons.share),
            tooltip: 'Share',
          ),
          IconButton(
            onPressed: _toggleFavorite,
            icon: Icon(_isFavorite ? Icons.favorite : Icons.favorite_border),
            tooltip: 'Favorite',
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Hero(
              tag: heroTag,
              child: SizedBox(
                height: 280,
                width: double.infinity,
                child: CachedNetworkImage(
                  imageUrl: widget.artwork.imageUrl,
                  fit: BoxFit.cover,
                  placeholder: (BuildContext context, String _) {
                    return Container(
                      color: Colors.grey.shade200,
                      alignment: Alignment.center,
                      child: const CircularProgressIndicator(),
                    );
                  },
                  errorWidget: (BuildContext context, String _, Object __) {
                    return Container(
                      color: Colors.grey.shade300,
                      alignment: Alignment.center,
                      child: const Icon(
                        Icons.museum_outlined,
                        size: 72,
                        color: Colors.grey,
                      ),
                    );
                  },
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  if (widget.confidence != null) _ConfidenceBadge(confidence: widget.confidence!),
                  const SizedBox(height: 12),
                  Text(
                    widget.artwork.title,
                    style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    widget.artwork.artist,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                      color: Colors.indigo,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _metadataLine(),
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.grey.shade700,
                    ),
                  ),
                  const SizedBox(height: 12),
                  const Divider(),
                  const SizedBox(height: 8),
                  if (widget.artwork.audioFilePath != null)
                    _AudioSection(
                      audioPlayer: _audioPlayer,
                      duration: _duration,
                      playerState: _playerState,
                      isPreparing: _isAudioPreparing,
                      onToggleAudio: _toggleAudio,
                    ),
                  if (widget.artwork.audioFilePath != null) const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      onPressed: _openMetWebsite,
                      icon: const Icon(Icons.open_in_new),
                      label: const Text('View on Met Website'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.indigo,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ConfidenceBadge extends StatelessWidget {
  const _ConfidenceBadge({required this.confidence});

  final double confidence;

  @override
  Widget build(BuildContext context) {
    final int percent = (confidence * 100).round();
    final _BadgeAppearance appearance = _appearanceFor(confidence);

    return Chip(
      backgroundColor: appearance.backgroundColor.withOpacity(0.18),
      side: BorderSide(color: appearance.backgroundColor.withOpacity(0.45)),
      label: Text(
        '${appearance.label} • $percent% match',
        style: TextStyle(
          color: appearance.backgroundColor,
          fontWeight: FontWeight.w600,
        ),
      ),
      avatar: Icon(Icons.verified, color: appearance.backgroundColor, size: 18),
    );
  }

  _BadgeAppearance _appearanceFor(double value) {
    if (value > 0.6) {
      return const _BadgeAppearance(
        label: highConfidenceLabel,
        backgroundColor: highConfidenceColor,
      );
    }
    if (value >= 0.3) {
      return const _BadgeAppearance(
        label: moderateConfidenceLabel,
        backgroundColor: moderateConfidenceColor,
      );
    }
    return const _BadgeAppearance(
      label: lowConfidenceLabel,
      backgroundColor: lowConfidenceColor,
    );
  }
}

class _BadgeAppearance {
  const _BadgeAppearance({required this.label, required this.backgroundColor});

  final String label;
  final Color backgroundColor;
}

class _AudioSection extends StatelessWidget {
  const _AudioSection({
    required this.audioPlayer,
    required this.duration,
    required this.playerState,
    required this.isPreparing,
    required this.onToggleAudio,
  });

  final AudioPlayer audioPlayer;
  final Duration duration;
  final PlayerState playerState;
  final bool isPreparing;
  final Future<void> Function() onToggleAudio;

  @override
  Widget build(BuildContext context) {
    final bool isPlaying = playerState == PlayerState.playing;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        const Text(
          listenHeading,
          style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 12),
        Row(
          children: <Widget>[
            IconButton.filled(
              onPressed: isPreparing ? null : () => onToggleAudio(),
              iconSize: 34,
              style: IconButton.styleFrom(
                backgroundColor: Colors.indigo,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.all(16),
              ),
              icon: Icon(isPlaying ? Icons.pause : Icons.play_arrow),
            ),
            const SizedBox(width: 12),
            if (isPreparing) const Expanded(child: LinearProgressIndicator()),
          ],
        ),
        const SizedBox(height: 6),
        StreamBuilder<Duration>(
          stream: audioPlayer.onPositionChanged,
          builder: (BuildContext context, AsyncSnapshot<Duration> snapshot) {
            final Duration position = snapshot.data ?? Duration.zero;
            final double maxSeconds = duration.inMilliseconds > 0
                ? duration.inMilliseconds.toDouble()
                : 1;
            final double valueSeconds = position.inMilliseconds
                .clamp(0, duration.inMilliseconds > 0 ? duration.inMilliseconds : 1)
                .toDouble();

            return Column(
              children: <Widget>[
                Slider(
                  value: valueSeconds,
                  min: 0,
                  max: maxSeconds,
                  activeColor: Colors.indigo,
                  onChanged: (double value) {
                    audioPlayer.seek(Duration(milliseconds: value.round()));
                  },
                ),
                Align(
                  alignment: Alignment.centerRight,
                  child: Text(
                    '${_formatDuration(position)} / ${_formatDuration(duration)}',
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                  ),
                ),
              ],
            );
          },
        ),
      ],
    );
  }

  static String _formatDuration(Duration duration) {
    final int minutes = duration.inMinutes;
    final int seconds = duration.inSeconds.remainder(60);
    final String paddedSeconds = seconds.toString().padLeft(2, '0');
    return '$minutes:$paddedSeconds';
  }
}
