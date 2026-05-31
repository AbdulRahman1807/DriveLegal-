import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'services/api_service.dart';
import 'theme/app_theme.dart';
import 'screens/auth_screen.dart';
import 'screens/chat_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ApiService.loadSession();
  runApp(
    const ProviderScope(
      child: DriveLegalApp(),
    ),
  );
}

class DriveLegalApp extends StatelessWidget {
  const DriveLegalApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DriveLegal',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: ApiService.isAuthenticated ? const ChatScreen() : const AuthScreen(),
    );
  }
}
