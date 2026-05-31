import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'theme/app_theme.dart';
import 'screens/chat_screen.dart';

void main() {
  runApp(
    const ProviderScope(
      child: DriveLegalApp(),
    ),
  );
}

class DriveLegalApp extends StatelessWidget {
  const DriveLegalApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DriveLegal',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const ChatScreen(),
    );
  }
}
