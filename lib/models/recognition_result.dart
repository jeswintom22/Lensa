import 'artwork.dart';

const String recognitionArtworkKey = 'artwork';
const String recognitionConfidenceKey = 'confidence';
const String recognitionGoodMatchesKey = 'good_matches';

class RecognitionResult {
  const RecognitionResult({
    required this.artwork,
    required this.confidence,
    required this.goodMatches,
  });

  final Artwork artwork;
  final double confidence;
  final int goodMatches;

  factory RecognitionResult.fromJson(Map<String, Object?> json) {
    final Object? artworkRaw = json[recognitionArtworkKey];
    final Map<String, Object?> artworkJson = artworkRaw is Map
        ? Map<String, Object?>.from(artworkRaw as Map)
        : <String, Object?>{};
    return RecognitionResult(
      artwork: Artwork.fromMap(artworkJson.cast<String, dynamic>()),
      confidence: _toDouble(json[recognitionConfidenceKey]),
      goodMatches: _toInt(json[recognitionGoodMatchesKey]),
    );
  }

  static double _toDouble(Object? value) {
    if (value is double) {
      return value;
    }
    if (value is num) {
      return value.toDouble();
    }
    if (value is String) {
      return double.tryParse(value) ?? 0;
    }
    return 0;
  }

  static int _toInt(Object? value) {
    if (value is int) {
      return value;
    }
    if (value is num) {
      return value.toInt();
    }
    if (value is String) {
      return int.tryParse(value) ?? 0;
    }
    return 0;
  }
}
