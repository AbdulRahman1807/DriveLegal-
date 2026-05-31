import 'dart:convert';

import 'package:flutter/foundation.dart' show defaultTargetPlatform, kIsWeb, TargetPlatform;
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

class ApiService {
  static const _storage = FlutterSecureStorage();
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
    _accessToken = await _storage.read(key: _accessKey);
    _refreshToken = await _storage.read(key: _refreshKey);
    _userEmail = await _storage.read(key: _emailKey);
  }

  static Future<void> _persistTokens() async {
    if (_accessToken != null) {
      await _storage.write(key: _accessKey, value: _accessToken!);
      await _storage.write(key: _refreshKey, value: _refreshToken ?? '');
      await _storage.write(key: _emailKey, value: _userEmail ?? '');
    } else {
      await _storage.delete(key: _accessKey);
      await _storage.delete(key: _refreshKey);
      await _storage.delete(key: _emailKey);
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
      await logout();
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

  Future<Map<String, dynamic>> sendQuery(String query, String sessionId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat'),
      headers: _authHeaders,
      body: jsonEncode({'query': query, 'session_id': sessionId}),
    );

    if (response.statusCode == 401) {
      final success = await refreshTokens();
      if (success) return sendQuery(query, sessionId);
      throw Exception('Session expired. Please log in again.');
    }

    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception(_parseError(response));
  }

  Future<Map<String, dynamic>> analyzeTicket(
    String base64Image,
    String mimeType,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/analyze_ticket'),
      headers: _authHeaders,
      body: jsonEncode({
        'image_base64': base64Image,
        'mime_type': mimeType,
      }),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception(_parseError(response));
  }

  Future<Map<String, dynamic>> getLegalSection(String sectionId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/legal_sections/$sectionId'),
      headers: _authHeaders,
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body) as Map<String, dynamic>;
    }
    throw Exception(_parseError(response));
  }
}
