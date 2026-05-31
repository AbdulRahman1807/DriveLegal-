import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

class SessionManager {
  static final SessionManager _instance = SessionManager._internal();
  factory SessionManager() => _instance;
  SessionManager._internal();

  String? _sessionId;

  Future<String> getSessionId() async {
    if (_sessionId != null) return _sessionId!;
    
    final prefs = await SharedPreferences.getInstance();
    _sessionId = prefs.getString('session_id');
    
    if (_sessionId == null) {
      _sessionId = const Uuid().v4();
      await prefs.setString('session_id', _sessionId!);
    }
    
    return _sessionId!;
  }

  Future<void> resetSession() async {
    final prefs = await SharedPreferences.getInstance();
    _sessionId = const Uuid().v4();
    await prefs.setString('session_id', _sessionId!);
  }
}
