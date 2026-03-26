import 'package:camera/camera.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import 'screens/browse_screen.dart';
import 'screens/camera_screen.dart';
import 'screens/home_screen.dart';
import 'services/database_service.dart';

const String appTitle = 'Lensa';
const MaterialColor appPrimarySwatch = Colors.indigo;

List<CameraDescription> appCameras = <CameraDescription>[];

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  try {
    appCameras = await availableCameras();
  } catch (error) {
    debugPrint('Unable to initialize cameras: $error');
  }

  try {
    await DatabaseService.instance.initDatabase();
  } catch (error) {
    debugPrint('Unable to initialize database: $error');
  }

  runApp(const LensaApp());
}

class LensaApp extends StatelessWidget {
  const LensaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: appTitle,
      theme: ThemeData(
        primarySwatch: appPrimarySwatch,
        scaffoldBackgroundColor: Colors.white,
        appBarTheme: const AppBarTheme(
          backgroundColor: Colors.indigo,
          foregroundColor: Colors.white,
          elevation: 0,
        ),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
      routes: <String, WidgetBuilder>{
        '/camera': (BuildContext context) => CameraScreen(cameras: appCameras),
        '/browse': (BuildContext context) => const BrowseScreen(),
      },
    );
  }
}
