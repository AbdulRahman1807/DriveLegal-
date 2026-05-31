import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'auth_screen.dart';
import 'chat_screen.dart';

class AccountScreen extends StatefulWidget {
  const AccountScreen({super.key});

  @override
  State<AccountScreen> createState() => _AccountScreenState();
}

class _AccountScreenState extends State<AccountScreen> {
  final _api = ApiService();
  final _email = TextEditingController();
  final _currentPw = TextEditingController();
  final _newPw = TextEditingController();

  String _language = 'en';
  String? _userId;
  bool _loading = true;
  bool _busy = false;
  String? _message;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _email.dispose();
    _currentPw.dispose();
    _newPw.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    final profile = await _api.getProfile();
    if (!mounted) return;
    if (profile == null) {
      Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const AuthScreen()));
      return;
    }
    setState(() {
      _userId = profile['id']?.toString();
      _email.text = profile['email'] as String? ?? '';
      _language = profile['language_preference'] as String? ?? 'en';
      _loading = false;
    });
  }

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _message = null;
      _error = null;
    });
    try {
      await _api.updateProfile(
        email: _email.text.trim(),
        languagePreference: _language,
        currentPassword: _newPw.text.isNotEmpty ? _currentPw.text : null,
        newPassword: _newPw.text.isNotEmpty ? _newPw.text : null,
      );
      setState(() {
        _message = 'Profile saved successfully.';
        _currentPw.clear();
        _newPw.clear();
      });
    } catch (e) {
      setState(() => _error = e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _deactivate() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: DriveLegalColors.card,
        title: Text('Deactivate your account?', style: DriveLegalTheme.text(18, weight: FontWeight.w700)),
        content: Text('You will not be able to sign in again.', style: DriveLegalTheme.text(14, color: DriveLegalColors.muted)),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(ctx, true), child: Text('Deactivate', style: DriveLegalTheme.text(14, color: DriveLegalColors.danger))),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    setState(() => _busy = true);
    try {
      await _api.deleteAccount();
      if (mounted) {
        Navigator.pushAndRemoveUntil(context, MaterialPageRoute(builder: (_) => const AuthScreen()), (_) => false);
      }
    } catch (e) {
      setState(() => _error = e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DriveLegalColors.background,
      body: Container(
        decoration: DriveLegalDecor.chatShell(),
        child: SafeArea(
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                decoration: const BoxDecoration(border: Border(bottom: BorderSide(color: DriveLegalColors.border))),
                child: Row(
                  children: [
                    Expanded(child: DriveLegalDecor.brandText(fontSize: 15.2)),
                    TextButton(
                      onPressed: () => Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const ChatScreen())),
                      child: Text('Back to chat', style: DriveLegalTheme.text(13.6, weight: FontWeight.w600, color: DriveLegalColors.primary)),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: _loading
                    ? const Center(child: CircularProgressIndicator(color: DriveLegalColors.primary))
                    : Center(
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.all(20),
                          child: ConstrainedBox(
                            constraints: const BoxConstraints(maxWidth: 480),
                            child: Container(
                              padding: const EdgeInsets.all(32),
                              decoration: BoxDecoration(
                                color: DriveLegalColors.card,
                                borderRadius: BorderRadius.circular(16),
                                border: Border.all(color: DriveLegalColors.border),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Text('Your account', style: DriveLegalTheme.text(26.4, weight: FontWeight.w700, color: DriveLegalColors.primary)),
                                  if (_userId != null) ...[
                                    const SizedBox(height: 8),
                                    Text('User ID $_userId', style: DriveLegalTheme.text(13.6, color: DriveLegalColors.muted)),
                                  ],
                                  if (_message != null) ...[
                                    const SizedBox(height: 12),
                                    Text(_message!, style: DriveLegalTheme.text(14.1, color: DriveLegalColors.success)),
                                  ],
                                  if (_error != null) ...[
                                    const SizedBox(height: 12),
                                    Text(_error!, style: DriveLegalTheme.text(14.1, color: DriveLegalColors.danger)),
                                  ],
                                  const SizedBox(height: 20),
                                  _labelField('Email', _email, keyboard: TextInputType.emailAddress),
                                  const SizedBox(height: 16),
                                  _langField(),
                                  const SizedBox(height: 16),
                                  _labelField('Current password (only if changing password)', _currentPw, obscure: true),
                                  const SizedBox(height: 16),
                                  _labelField('New password', _newPw, obscure: true),
                                  const SizedBox(height: 20),
                                  _gradientBtn('Save changes', _busy ? null : _save),
                                  const SizedBox(height: 12),
                                  OutlinedButton(
                                    onPressed: _busy ? null : _deactivate,
                                    style: OutlinedButton.styleFrom(
                                      foregroundColor: DriveLegalColors.danger,
                                      side: const BorderSide(color: Color(0x59F87171)),
                                      padding: const EdgeInsets.symmetric(vertical: 12),
                                    ),
                                    child: const Text('Deactivate account'),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _labelField(String label, TextEditingController c, {bool obscure = false, TextInputType? keyboard}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: DriveLegalTheme.text(12.8, weight: FontWeight.w600, color: DriveLegalColors.label)),
        const SizedBox(height: 6),
        TextField(controller: c, obscureText: obscure, keyboardType: keyboard, style: DriveLegalTheme.text(14.7), decoration: const InputDecoration()),
      ],
    );
  }

  Widget _langField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Language', style: DriveLegalTheme.text(12.8, weight: FontWeight.w600, color: DriveLegalColors.label)),
        const SizedBox(height: 6),
        DropdownButtonFormField<String>(
          value: _language,
          dropdownColor: DriveLegalColors.inputBg,
          style: DriveLegalTheme.text(14.7),
          decoration: const InputDecoration(),
          items: const [
            DropdownMenuItem(value: 'en', child: Text('English')),
            DropdownMenuItem(value: 'hi', child: Text('Hindi')),
          ],
          onChanged: (v) => setState(() => _language = v ?? 'en'),
        ),
      ],
    );
  }

  Widget _gradientBtn(String label, VoidCallback? onTap) {
    return DecoratedBox(
      decoration: BoxDecoration(gradient: DriveLegalColors.primaryGradient, borderRadius: BorderRadius.circular(10)),
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          minimumSize: const Size.fromHeight(48),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
        child: Text(label, style: DriveLegalTheme.text(15.2, weight: FontWeight.w600, color: Colors.white)),
      ),
    );
  }
}
