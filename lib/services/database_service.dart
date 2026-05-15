<<<<<<< HEAD
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart' show ByteData, rootBundle;
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:sqflite/sqflite.dart';

import '../models/artwork.dart';

const String databaseFileName = 'museum_guide.db';
const String databaseAssetPath = 'assets/database/museum_guide.db';
const List<String> artworkColumns = <String>[
  'id',
  'met_object_id',
=======
const String databaseFileName = 'museum_guide.db';
const String databaseAssetDirectory = 'assets/database';

const List<String> artworkColumns = <String>[
  'id',
  'object_id',
>>>>>>> 5170222 (chore: scaffold Flutter app and finalize setup fixes)
  'title',
  'artist',
  'date',
  'medium',
  'department',
<<<<<<< HEAD
  'image_url',
  'audio_file_path',
];

class DatabaseService {
  DatabaseService._internal();

  static final DatabaseService instance = DatabaseService._internal();

  Database? _database;

  Future<void> initDatabase() async {
    if (_database != null) {
      return;
    }
    _database = await _openDatabase();
  }

  Future<int> getArtworkCount() async {
    try {
      final Database db = await _getDatabase();
      final List<Map<String, Object?>> rows =
          await db.rawQuery('SELECT COUNT(*) AS count FROM artworks');
      if (rows.isEmpty) {
        return 0;
      }
      final Object? value = rows.first['count'];
      if (value is int) {
        return value;
      }
      if (value is num) {
        return value.toInt();
      }
      return int.tryParse(value?.toString() ?? '0') ?? 0;
    } catch (error) {
      debugPrint('DatabaseService.getArtworkCount failed: $error');
      return 0;
    }
  }

  Future<List<Artwork>> getAllArtworks() async {
    try {
      final Database db = await _getDatabase();
      final List<Map<String, Object?>> rows = await db.query(
        artworkTableName,
        columns: artworkColumns,
        orderBy: 'title ASC',
      );
      return rows.map((Map<String, Object?> row) => Artwork.fromMap(row)).toList();
    } catch (error) {
      debugPrint('DatabaseService.getAllArtworks failed: $error');
      return <Artwork>[];
    }
  }

  Future<Artwork?> getArtworkById(int id) async {
    try {
      final Database db = await _getDatabase();
      final List<Map<String, Object?>> rows = await db.query(
        artworkTableName,
        columns: artworkColumns,
        where: 'id = ?',
        whereArgs: <Object>[id],
        limit: 1,
      );
      if (rows.isEmpty) {
        return null;
      }
      return Artwork.fromMap(rows.first);
    } catch (error) {
      debugPrint('DatabaseService.getArtworkById failed for id=$id: $error');
      return null;
    }
  }

  Future<List<Artwork>> searchArtworks(String query) async {
    try {
      final String trimmed = query.trim();
      if (trimmed.isEmpty) {
        return getAllArtworks();
      }
      final String likePattern = '%$trimmed%';
      final Database db = await _getDatabase();
      final List<Map<String, Object?>> rows = await db.query(
        artworkTableName,
        columns: artworkColumns,
        where: 'title LIKE ? OR artist LIKE ?',
        whereArgs: <Object>[likePattern, likePattern],
        orderBy: 'title ASC',
      );
      return rows.map((Map<String, Object?> row) => Artwork.fromMap(row)).toList();
    } catch (error) {
      debugPrint('DatabaseService.searchArtworks failed: $error');
      return <Artwork>[];
    }
  }

  Future<List<Artwork>> getArtworksByDepartment(String department) async {
    try {
      final Database db = await _getDatabase();
      final List<Map<String, Object?>> rows = await db.query(
        artworkTableName,
        columns: artworkColumns,
        where: 'department = ?',
        whereArgs: <Object>[department],
        orderBy: 'title ASC',
      );
      return rows.map((Map<String, Object?> row) => Artwork.fromMap(row)).toList();
    } catch (error) {
      debugPrint(
        'DatabaseService.getArtworksByDepartment failed for department=$department: $error',
      );
      return <Artwork>[];
    }
  }

  Future<List<String>> getDepartments() async {
    try {
      final Database db = await _getDatabase();
      final List<Map<String, Object?>> rows = await db.rawQuery(
        '''
        SELECT DISTINCT department
        FROM artworks
        WHERE department IS NOT NULL AND TRIM(department) != ''
        ORDER BY department
        ''',
      );
      return rows
          .map((Map<String, Object?> row) => row['department']?.toString() ?? '')
          .where((String value) => value.trim().isNotEmpty)
          .toList();
    } catch (error) {
      debugPrint('DatabaseService.getDepartments failed: $error');
      return <String>[];
    }
  }

  Future<void> close() async {
    try {
      await _database?.close();
      _database = null;
    } catch (error) {
      debugPrint('DatabaseService.close failed: $error');
    }
  }

  Future<Database> _openDatabase() async {
    final Directory docsDir = await getApplicationDocumentsDirectory();
    final String dbPath = p.join(docsDir.path, databaseFileName);
    final File dbFile = File(dbPath);

    if (!await dbFile.exists()) {
      await _copyBundledDatabase(targetPath: dbPath);
    }

    return openDatabase(dbPath);
  }

  Future<void> _copyBundledDatabase({required String targetPath}) async {
    try {
      final ByteData data = await rootBundle.load(databaseAssetPath);
      final Uint8List bytes = data.buffer.asUint8List(
        data.offsetInBytes,
        data.lengthInBytes,
      );
      final File destination = File(targetPath);
      await destination.create(recursive: true);
      await destination.writeAsBytes(bytes, flush: true);
      debugPrint('Database copied from assets to $targetPath');
    } catch (error) {
      throw Exception(
        'Failed to copy database asset from $databaseAssetPath to $targetPath: $error',
      );
    }
  }

  Future<Database> _getDatabase() async {
    if (_database != null) {
      return _database!;
    }
    _database = await _openDatabase();
    return _database!;
  }
=======
  'image_path',
  'audio_path',
  'description',
];

const String artworkTableName = 'artworks';

class DatabaseService {
  const DatabaseService();
>>>>>>> 5170222 (chore: scaffold Flutter app and finalize setup fixes)
}
