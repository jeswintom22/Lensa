import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../models/recognition_result.dart';
import '../services/recognition_service.dart';
import 'artwork_detail_screen.dart';

const String defaultStatusMessage = 'Point camera at artwork';
const String analyzingStatusMessage = 'Analyzing artwork...';
const String offlineBannerText = 'Server offline — tap to retry';
const String noMatchSnackBarText =
    'Artwork not recognized. Try better lighting or a closer angle.';
const String serverOfflineDialogMessage =
    'Recognition server is not running. Start bridge_server.py first.';
const Duration snackBarDuration = Duration(seconds: 3);

class CameraScreen extends StatefulWidget {
  const CameraScreen({super.key, required this.cameras});

  final List<CameraDescription> cameras;

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  final RecognitionService _recognitionService = RecognitionService();

  CameraController? _controller;
  bool _isProcessing = false;
  bool _isServerAvailable = true;
  String _statusMessage = defaultStatusMessage;

  @override
  void initState() {
    super.initState();
    _initializeCamera();
    _checkServerAvailability();
  }

  Future<void> _initializeCamera() async {
    if (widget.cameras.isEmpty) {
      if (!mounted) {
        return;
      }
      setState(() {
        _statusMessage = 'No cameras available';
      });
      return;
    }

    _controller = CameraController(
      widget.cameras.first,
      ResolutionPreset.high,
      enableAudio: false,
    );

    try {
      await _controller!.initialize();
      if (!mounted) {
        return;
      }
      setState(() {});
    } catch (error) {
      debugPrint('CameraScreen._initializeCamera failed: $error');
      if (!mounted) {
        return;
      }
      setState(() {
        _statusMessage = 'Camera error: $error';
      });
    }
  }

  Future<void> _checkServerAvailability({bool showSuccessSnackBar = false}) async {
    final bool available = await _recognitionService.isServerAvailable();
    if (!mounted) {
      return;
    }

    setState(() {
      _isServerAvailable = available;
    });

    if (available && showSuccessSnackBar) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Server is online'),
          duration: Duration(seconds: 2),
        ),
      );
    }
  }

  Future<void> _captureAndRecognize() async {
    final CameraController? controller = _controller;
    if (controller == null || !controller.value.isInitialized || _isProcessing) {
      return;
    }

    if (!mounted) {
      return;
    }
    setState(() {
      _isProcessing = true;
      _statusMessage = analyzingStatusMessage;
    });

    try {
      final XFile image = await controller.takePicture();
      final RecognitionResult? result = await _recognitionService.recognize(image);

      if (!mounted) {
        return;
      }

      if (result != null) {
        await Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (BuildContext context) => ArtworkDetailScreen(
              artwork: result.artwork,
              confidence: result.confidence,
            ),
          ),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(noMatchSnackBarText),
            duration: snackBarDuration,
          ),
        );
      }
    } on RecognitionServerUnavailableException catch (error) {
      debugPrint('CameraScreen._captureAndRecognize server unavailable: $error');
      if (!mounted) {
        return;
      }
      setState(() {
        _isServerAvailable = false;
      });
      await showDialog<void>(
        context: context,
        builder: (BuildContext context) {
          return AlertDialog(
            title: const Text('Server Offline'),
            content: const Text(serverOfflineDialogMessage),
            actions: <Widget>[
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('OK'),
              ),
            ],
          );
        },
      );
    } catch (error) {
      debugPrint('CameraScreen._captureAndRecognize failed: $error');
      if (!mounted) {
        return;
      }
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Failed to process image. Please try again.'),
          duration: snackBarDuration,
        ),
      );
    } finally {
      if (!mounted) {
        return;
      }
      setState(() {
        _isProcessing = false;
        _statusMessage = defaultStatusMessage;
      });
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final CameraController? controller = _controller;
    if (controller == null || !controller.value.isInitialized) {
      return Scaffold(
        appBar: AppBar(title: const Text('Scan Artwork')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: <Widget>[
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              Text(_statusMessage),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      body: Stack(
        children: <Widget>[
          SizedBox.expand(
            child: CameraPreview(controller),
          ),
          CustomPaint(
            painter: FrameOverlayPainter(),
            child: Container(),
          ),
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: _TopOverlay(
              statusMessage: _statusMessage,
              isServerAvailable: _isServerAvailable,
              onClosePressed: () => Navigator.of(context).pop(),
              onRetryServer: () => _checkServerAvailability(showSuccessSnackBar: true),
            ),
          ),
          Positioned(
            bottom: 40,
            left: 0,
            right: 0,
            child: Center(
              child: GestureDetector(
                onTap: _isProcessing ? null : _captureAndRecognize,
                child: Container(
                  width: 82,
                  height: 82,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white,
                    border: Border.all(color: Colors.indigo, width: 4),
                  ),
                  child: _isProcessing
                      ? const Padding(
                          padding: EdgeInsets.all(22),
                          child: CircularProgressIndicator(strokeWidth: 3),
                        )
                      : const Icon(
                          Icons.camera,
                          size: 40,
                          color: Colors.indigo,
                        ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TopOverlay extends StatelessWidget {
  const _TopOverlay({
    required this.statusMessage,
    required this.isServerAvailable,
    required this.onClosePressed,
    required this.onRetryServer,
  });

  final String statusMessage;
  final bool isServerAvailable;
  final VoidCallback onClosePressed;
  final VoidCallback onRetryServer;

  @override
  Widget build(BuildContext context) {
    final double topInset = MediaQuery.of(context).padding.top;
    return Container(
      padding: EdgeInsets.only(
        top: topInset + 10,
        bottom: 16,
        left: 16,
        right: 16,
      ),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: <Color>[
            Colors.black.withOpacity(0.75),
            Colors.black.withOpacity(0.20),
            Colors.transparent,
          ],
        ),
      ),
      child: Column(
        children: <Widget>[
          if (!isServerAvailable)
            GestureDetector(
              onTap: onRetryServer,
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                margin: const EdgeInsets.only(bottom: 10),
                decoration: BoxDecoration(
                  color: Colors.orange.shade700,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Text(
                  offlineBannerText,
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          Row(
            children: <Widget>[
              IconButton(
                onPressed: onClosePressed,
                icon: const Icon(Icons.close, color: Colors.white),
              ),
              Expanded(
                child: Text(
                  statusMessage,
                  textAlign: TextAlign.center,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
              const SizedBox(width: 48),
            ],
          ),
        ],
      ),
    );
  }
}

class FrameOverlayPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final Paint paint = Paint()
      ..color = Colors.white.withOpacity(0.6)
      ..strokeWidth = 3
      ..style = PaintingStyle.stroke;

    final Rect rect = Rect.fromCenter(
      center: Offset(size.width / 2, size.height / 2),
      width: size.width * 0.82,
      height: size.height * 0.58,
    );
    const double cornerLength = 40;

    canvas.drawLine(rect.topLeft, rect.topLeft + const Offset(cornerLength, 0), paint);
    canvas.drawLine(rect.topLeft, rect.topLeft + const Offset(0, cornerLength), paint);

    canvas.drawLine(rect.topRight, rect.topRight + const Offset(-cornerLength, 0), paint);
    canvas.drawLine(rect.topRight, rect.topRight + const Offset(0, cornerLength), paint);

    canvas.drawLine(
      rect.bottomLeft,
      rect.bottomLeft + const Offset(cornerLength, 0),
      paint,
    );
    canvas.drawLine(
      rect.bottomLeft,
      rect.bottomLeft + const Offset(0, -cornerLength),
      paint,
    );

    canvas.drawLine(
      rect.bottomRight,
      rect.bottomRight + const Offset(-cornerLength, 0),
      paint,
    );
    canvas.drawLine(
      rect.bottomRight,
      rect.bottomRight + const Offset(0, -cornerLength),
      paint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) {
    return false;
  }
}
