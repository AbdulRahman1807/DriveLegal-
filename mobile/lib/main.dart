import 'package:flutter/material.dart';
import 'screens/auth_screen.dart';
import 'screens/chat_screen.dart';
import 'services/api_service.dart';
import 'theme/app_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiService.loadSession();
  runApp(const MainApp());
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DriveLegal',
      debugShowCheckedModeBanner: false,
      theme: DriveLegalTheme.dark(),
      home: ApiService.isAuthenticated ? const ChatScreen() : const AuthScreen(),
    );
  }
}
