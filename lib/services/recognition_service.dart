import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../models/recognition_result.dart';

const String defaultHost = 'localhost';
const String androidEmulatorHost = '10.0.2.2';
const int bridgeServerPort = 8000;
const String recognizeEndpoint = '/recognize';
const String healthEndpoint = '/health';
const int requestTimeoutSeconds = 10;

class RecognitionServerUnavailableException implements Exception {
  const RecognitionServerUnavailableException(this.message);

  final String message;

  @override
  String toString() => message;
}

class RecognitionService {
  RecognitionService({String? baseUrl}) : _baseUrl = baseUrl ?? _resolveDefaultBaseUrl();

  final String _baseUrl;
  final http.Client _httpClient = http.Client();

  Future<RecognitionResult?> recognize(XFile imageFile) async {
    try {
      final Uri uri = Uri.parse('$_baseUrl$recognizeEndpoint');
      final List<int> imageBytes = await imageFile.readAsBytes();
      final String encodedImage = base64Encode(imageBytes);

      final http.Response response = await _httpClient
          .post(
            uri,
            headers: <String, String>{'Content-Type': 'application/json'},
            body: jsonEncode(<String, String>{'image_base64': encodedImage}),
          )
          .timeout(const Duration(seconds: requestTimeoutSeconds));

      if (response.statusCode != HttpStatus.ok) {
        debugPrint('RecognitionService.recognize non-200 status: ${response.statusCode}');
        return null;
      }

      final Object? decoded = jsonDecode(response.body);
      final Map<String, Object?> payload = decoded is Map
          ? Map<String, Object?>.from(decoded as Map)
          : <String, Object?>{};
      final bool found = payload['found'] == true;
      if (!found) {
        return null;
      }
      return RecognitionResult.fromJson(payload);
    } on TimeoutException catch (error) {
      throw RecognitionServerUnavailableException(
        'Recognition request timed out after $requestTimeoutSeconds seconds: $error',
      );
    } on SocketException catch (error) {
      throw RecognitionServerUnavailableException(
        'Cannot connect to recognition server at $_baseUrl: $error',
      );
    } on http.ClientException catch (error) {
      throw RecognitionServerUnavailableException(
        'Recognition server request failed at $_baseUrl: $error',
      );
    } catch (error) {
      debugPrint('RecognitionService.recognize failed: $error');
      return null;
    }
  }

  Future<bool> isServerAvailable() async {
    try {
      final Uri uri = Uri.parse('$_baseUrl$healthEndpoint');
      final http.Response response = await _httpClient
          .get(uri)
          .timeout(const Duration(seconds: requestTimeoutSeconds));

      if (response.statusCode != HttpStatus.ok) {
        return false;
      }
      final Object? decoded = jsonDecode(response.body);
      final Map<String, Object?> payload = decoded is Map
          ? Map<String, Object?>.from(decoded as Map)
          : <String, Object?>{};
      return payload['status'] == 'ok';
    } catch (error) {
      debugPrint('RecognitionService.isServerAvailable failed: $error');
      return false;
    }
  }

  static String _resolveDefaultBaseUrl() {
    final String host = Platform.isAndroid ? androidEmulatorHost : defaultHost;
    return 'http://$host:$bridgeServerPort';
  }
}
