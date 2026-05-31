import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Use localhost since we are targeting Chrome Web / macOS desktop
  static const String baseUrl = 'http://127.0.0.1:8000/api/v1';
  static const String authToken = 'drivelegal-secret-dev-key';

  Future<Map<String, dynamic>> sendQuery(String query, String sessionId) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/chat'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $authToken',
        },
        body: jsonEncode({
          'query': query,
          'session_id': sessionId,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load response: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> analyzeTicket(String base64Image, String mimeType) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/analyze_ticket'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $authToken',
        },
        body: jsonEncode({
          'image_base64': base64Image,
          'mime_type': mimeType,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to analyze ticket: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<Map<String, dynamic>> getCalculatorMetadata() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/calculator/metadata'),
        headers: {
          'Authorization': 'Bearer $authToken',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load metadata: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }

  Future<List<dynamic>> calculateFine(String violationId, String jurisdictionId, String vehicleCategory, bool isRepeat) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/calculator/calculate'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $authToken',
        },
        body: jsonEncode({
          'violation_id': violationId,
          'jurisdiction_id': jurisdictionId,
          'vehicle_category': vehicleCategory,
          'is_repeat_offence': isRepeat,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to calculate fine: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Network error: $e');
    }
  }
}
