import 'package:flutter/foundation.dart';

const String artworkTableName = 'artworks';

@immutable
class Artwork {
  const Artwork({
    required this.id,
    required this.metObjectId,
    required this.title,
    required this.artist,
    required this.date,
    required this.medium,
    required this.department,
    required this.imageUrl,
    this.audioFilePath,
  });

  final int id;
  final int metObjectId;
  final String title;
  final String artist;
  final String date;
  final String medium;
  final String department;
  final String imageUrl;
  final String? audioFilePath;

  factory Artwork.fromMap(Map<String, dynamic> map) {
    return Artwork(
      id: _toInt(map['id']),
      metObjectId: _toInt(map['met_object_id']),
      title: _toString(map['title']),
      artist: _toString(map['artist']),
      date: _toString(map['date']),
      medium: _toString(map['medium']),
      department: _toString(map['department']),
      imageUrl: _toString(map['image_url']),
      audioFilePath: _toNullableString(map['audio_file_path']),
    );
  }

  Map<String, Object?> toMap() {
    return <String, Object?>{
      'id': id,
      'met_object_id': metObjectId,
      'title': title,
      'artist': artist,
      'date': date,
      'medium': medium,
      'department': department,
      'image_url': imageUrl,
      'audio_file_path': audioFilePath,
    };
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

  static String _toString(Object? value) {
    if (value == null) {
      return '';
    }
    return value.toString();
  }

  static String? _toNullableString(Object? value) {
    final String text = _toString(value).trim();
    if (text.isEmpty) {
      return null;
    }
    return text;
  }
}
