import 'dart:convert';

import 'package:flutter/foundation.dart' show defaultTargetPlatform, kIsWeb, TargetPlatform;
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

import '../models/chat_models.dart';
import 'session_manager.dart';

class ApiService {
  static const _accessKey = 'drivelegal_access_token';
  static const _refreshKey = 'drivelegal_refresh_token';
  static const _emailKey = 'drivelegal_user_email';

  static String get baseUrl {
    const defaultUrl = 'http://127.0.0.1:8000/api/v1';
    const url = String.fromEnvironment('API_BASE_URL', defaultValue: defaultUrl);
    if (!kIsWeb &&
        defaultTargetPlatform == TargetPlatform.android &&
        url == defaultUrl) {
      return 'http://10.0.2.2:8000/api/v1';
    }
    return url;
  }

  static String? _accessToken;
  static String? _refreshToken;
  static String? _userEmail;

  static String? get userEmail => _userEmail;
  static bool get isAuthenticated => _accessToken != null;

  static Future<void> loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    _accessToken = prefs.getString(_accessKey);
    _refreshToken = prefs.getString(_refreshKey);
    _userEmail = prefs.getString(_emailKey);
  }

  static Future<void> _persistTokens() async {
    final prefs = await SharedPreferences.getInstance();
    if (_accessToken != null) {
      await prefs.setString(_accessKey, _accessToken!);
      await prefs.setString(_refreshKey, _refreshToken ?? '');
      await prefs.setString(_emailKey, _userEmail ?? '');
    } else {
      await prefs.remove(_accessKey);
      await prefs.remove(_refreshKey);
      await prefs.remove(_emailKey);
    }
  }

  static String _parseError(http.Response response) {
    try {
      final data = jsonDecode(response.body);
      final detail = data['detail'];
      if (detail is String) return detail;
      if (detail is List && detail.isNotEmpty) {
        return detail.map((e) => e['msg'] ?? e.toString()).join(', ');
      }
    } catch (_) {}
    return 'Request failed (${response.statusCode}).';
  }

  Map<String, String> get _authHeaders => {
        'Content-Type': 'application/json',
        if (_accessToken != null) 'Authorization': 'Bearer $_accessToken',
      };

  Future<void> register(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'language_preference': 'en',
      }),
    );

    if (response.statusCode == 201) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      _accessToken = data['access_token'] as String?;
      _refreshToken = data['refresh_token'] as String?;
      _userEmail = email;
      await _persistTokens();
      return;
    }
    throw Exception(_parseError(response));
  }

  Future<void> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      _accessToken = data['access_token'] as String?;
      _refreshToken = data['refresh_token'] as String?;
      _userEmail = email;
      await _persistTokens();
      return;
    }
    throw Exception(_parseError(response));
  }

  Future<Map<String, dynamic>?> getProfile() async {
    if (_accessToken == null) return null;
    final response = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: _authHeaders,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    if (response.statusCode == 401) {
      final ok = await refreshTokens();
      if (ok) return getProfile();
    }
    return null;
  }

  Future<Map<String, dynamic>> updateProfile({
    String? email,
    String? languagePreference,
    String? currentPassword,
    String? newPassword,
  }) async {
    final body = <String, dynamic>{};
    if (email != null) body['email'] = email;
    if (languagePreference != null) {
      body['language_preference'] = languagePreference;
    }
    if (newPassword != null) {
      body['current_password'] = currentPassword;
      body['new_password'] = newPassword;
    }

    final response = await http.patch(
      Uri.parse('$baseUrl/auth/me'),
      headers: _authHeaders,
      body: jsonEncode(body),
    );

    if (response.statusCode == 200) {
      final profile = jsonDecode(response.body) as Map<String, dynamic>;
      _userEmail = profile['email'] as String?;
      await _persistTokens();
      return profile;
    }
    throw Exception(_parseError(response));
  }

  Future<void> deleteAccount() async {
    final response = await http.delete(
      Uri.parse('$baseUrl/auth/me'),
      headers: _authHeaders,
    );
    if (response.statusCode == 204) {
      logout();
      return;
    }
    throw Exception(_parseError(response));
  }

  Future<bool> refreshTokens() async {
    if (_refreshToken == null) return false;
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/refresh'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'refresh_token': _refreshToken}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        _accessToken = data['access_token'] as String?;
        _refreshToken = data['refresh_token'] as String?;
        await _persistTokens();
        return true;
      }
    } catch (_) {}
    await logout();
    return false;
  }

  Future<void> logout() async {
    _accessToken = null;
    _refreshToken = null;
    _userEmail = null;
    await _persistTokens();
  }

  Future<ChatMessage> sendChatQuery(String query, {String? violationCode}) async {
    final url = Uri.parse('$baseUrl/chat');

    try {
      final sessionId = await SessionManager().getSessionId();

      final response = await http
          .post(
            url,
            headers: _authHeaders,
            body: jsonEncode({
              'query': query,
              'session_id': sessionId,
              if (violationCode != null) 'violation_code': violationCode,
            }),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 401) {
        final success = await refreshTokens();
        if (success) {
          return sendChatQuery(query, violationCode: violationCode);
        }
        return ChatMessage(
          text: 'Session expired. Please log in again.',
          isUser: false,
          isError: true,
        );
      }

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return ChatMessage.fromBotResponse(data);
      }
      return ChatMessage(
        text: 'Error communicating with the server: ${response.statusCode}',
        isUser: false,
        isError: true,
      );
    } catch (e) {
      return ChatMessage(
        text:
            'Cannot reach the backend at $baseUrl. Start the API server and try again.\n$e',
        isUser: false,
        isError: true,
      );
    }
  }
}
