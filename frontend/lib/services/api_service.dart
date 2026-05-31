import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/chat_models.dart';
import 'session_manager.dart';

class ApiService {
  static String get baseUrl {
    const defaultUrl = 'http://127.0.0.1:8000/api/v1';
    final url = const String.fromEnvironment('API_BASE_URL', defaultValue: defaultUrl);
    if (Platform.isAndroid && url == defaultUrl) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    return url;
  }

  Future<ChatMessage> sendChatQuery(String query, {String? violationCode}) async {
    final url = Uri.parse('$baseUrl/chat');
    
    try {
      final sessionId = await SessionManager().getSessionId();
      
      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'query': query,
          'session_id': sessionId,
          if (violationCode != null) 'violation_code': violationCode,
        }),
      ).timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return ChatMessage.fromBotResponse(data);
      } else {
        return ChatMessage(
          text: 'Error communicating with the server: ${response.statusCode}',
          isUser: false,
          isError: true,
        );
      }
    } catch (e) {
      return ChatMessage(
        text: 'Network error: Please ensure the DriveLegal backend is running.\nDetails: $e',
        isUser: false,
        isError: true,
      );
    }
  }
}
