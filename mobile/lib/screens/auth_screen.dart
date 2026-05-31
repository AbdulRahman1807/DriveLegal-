import 'package:flutter/material.dart';

import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/road_safety_simulator.dart';
import '../widgets/shield_avatar.dart';
import 'chat_screen.dart';

enum _AuthMode { signIn, signUp }

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _fullNameController = TextEditingController();
  final _api = ApiService();

  _AuthMode _mode = _AuthMode.signIn;
  bool _loading = false;
  bool _agreePolicy = false;
  bool _rememberMe = false;
  String? _error;
  String? _roadComment;
  _FocusField _focus = _FocusField.none;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _fullNameController.dispose();
    super.dispose();
  }

  bool get _isSignup => _mode == _AuthMode.signUp;

  String get _shieldDisplay {
    if (_roadComment != null) return _roadComment!;
    if (_focus == _FocusField.email) return 'Enter your registered email.';
    if (_focus == _FocusField.password) {
      return _isSignup ? 'Use at least 8 characters for a strong password.' : 'Your account is protected.';
    }
    return _isSignup ? "Let's get you set up — I'll help with traffic laws from day one." : 'Ready to help you drive legally.';
  }

  void _switchMode(_AuthMode mode) {
    setState(() {
      _mode = mode;
      _error = null;
      _passwordController.clear();
      _confirmPasswordController.clear();
      _focus = _FocusField.none;
    });
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_isSignup && !_agreePolicy) {
      setState(() => _error = 'Please agree to the privacy policy.');
      return;
    }
    if (_isSignup && _passwordController.text != _confirmPasswordController.text) {
      setState(() => _error = 'Passwords do not match.');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final email = _emailController.text.trim();
      if (_isSignup) {
        await _api.register(email, _passwordController.text);
      } else {
        await _api.login(email, _passwordController.text);
      }
      if (mounted) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const ChatScreen()));
      }
    } catch (e) {
      setState(() => _error = e.toString().replaceAll('Exception: ', ''));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DriveLegalColors.background,
      body: Container(
        decoration: DriveLegalDecor.authShell(),
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, c) {
              final wide = c.maxWidth >= 960;
              if (wide) {
                return Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(child: _heroSide()),
                    Expanded(child: _formSide()),
                  ],
                );
              }
              return SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    _heroSide(),
                    _formSide(),
                  ],
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _heroSide() {
    final wide = MediaQuery.sizeOf(context).width >= 960;
    return Container(
      decoration: BoxDecoration(
        border: Border(
          bottom: wide ? BorderSide.none : const BorderSide(color: DriveLegalColors.border),
          right: wide ? const BorderSide(color: DriveLegalColors.border) : BorderSide.none,
        ),
      ),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Positioned(
            top: MediaQuery.sizeOf(context).height * 0.12,
            left: 0,
            right: 0,
            child: Center(
              child: Container(
                width: 280,
                height: 280,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  boxShadow: [BoxShadow(color: DriveLegalColors.primary.withValues(alpha: 0.25), blurRadius: 80, spreadRadius: 20)],
                ),
              ),
            ),
          ),
          Positioned(left: 0, right: 0, bottom: 0, child: RoadSafetySimulator(variant: RoadSimulatorVariant.login, onShieldComment: (m) => setState(() => _roadComment = m))),
          Padding(
            padding: const EdgeInsets.fromLTRB(24, 32, 24, 168),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                DriveLegalDecor.brandText(fontSize: 28),
                const SizedBox(height: 6),
                Text('Know the law before you pay the fine.', style: DriveLegalTheme.text(16, weight: FontWeight.w600)),
                const SizedBox(height: 4),
                Text("India's AI-powered traffic law assistant.", style: DriveLegalTheme.text(13.1, color: DriveLegalColors.muted)),
                const SizedBox(height: 24),
                _mascotBlock(),
                const SizedBox(height: 20),
                Text('"Ready to help you drive legally."', style: DriveLegalTheme.text(15.2, weight: FontWeight.w600, color: DriveLegalColors.label).copyWith(fontStyle: FontStyle.italic)),
                const SizedBox(height: 10),
                ...['Know your rights.', 'Know your fines.', 'Drive safely.'].map(_heroListItem),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _heroListItem(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 5.6),
      child: Row(
        children: [
          const Text('✓ ', style: TextStyle(fontSize: 13.6, fontWeight: FontWeight.w700, color: DriveLegalColors.accent)),
          Expanded(child: Text(text, style: DriveLegalTheme.text(13.6, color: DriveLegalColors.muted))),
        ],
      ),
    );
  }

  Widget _mascotBlock() {
    return LayoutBuilder(
      builder: (context, c) {
        final narrow = c.maxWidth < 520;
        final children = [
          Expanded(child: _heroSpeechBubble()),
          const SizedBox(width: 12),
          const ShieldAvatar(size: ShieldAvatarSize.auth, showDragHint: true),
        ];
        if (narrow) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              const ShieldAvatar(size: ShieldAvatarSize.auth, showDragHint: true),
              const SizedBox(height: 12),
              _heroSpeechBubble(),
            ],
          );
        }
        return Row(crossAxisAlignment: CrossAxisAlignment.end, children: children.reversed.toList());
      },
    );
  }

  Widget _heroSpeechBubble() {
    final parts = _shieldDisplay.split('. ');
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 350),
      child: Container(
        key: ValueKey(_shieldDisplay),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13.6),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: DriveLegalColors.borderStrong),
          boxShadow: const [BoxShadow(color: Color(0x0A0F172A), blurRadius: 8, offset: Offset(0, 2))],
        ),
        child: RichText(
          text: TextSpan(
            style: DriveLegalTheme.text(13.1, color: DriveLegalColors.textSoft, height: 1.45),
            children: [
              const TextSpan(text: 'Shield: ', style: TextStyle(color: DriveLegalColors.primary, fontWeight: FontWeight.w700)),
              TextSpan(text: parts.first),
              if (parts.length > 1)
                TextSpan(text: '\n${parts.sublist(1).join('. ')}', style: DriveLegalTheme.text(12, color: DriveLegalColors.muted, height: 1.45)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _formSide() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Container(
            padding: const EdgeInsets.fromLTRB(28, 32, 28, 32),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: DriveLegalColors.borderStrong),
              boxShadow: const [BoxShadow(color: Color(0x0A0F172A), blurRadius: 32, offset: Offset(0, 8))],
            ),
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  _modeTabs(),
                  const SizedBox(height: 24),
                  Text(_isSignup ? 'Create your account' : 'Welcome back', style: DriveLegalTheme.text(24, weight: FontWeight.w700)),
                  const SizedBox(height: 8),
                  const Text(
                    'Shield is ready to assist you with traffic laws, challans, vehicle documents, and road safety guidance.',
                    style: TextStyle(fontSize: 14.1, height: 1.55, color: DriveLegalColors.muted),
                  ),
                  if (_error != null) ...[const SizedBox(height: 16), _errorBox()],
                  const SizedBox(height: 20),
                  if (_isSignup) ...[
                    _field('Full Name', _fullNameController, hint: 'John Doe'),
                    const SizedBox(height: 16),
                  ],
                  _field('Email', _emailController, hint: 'you@email.com', keyboard: TextInputType.emailAddress, onFocus: (f) => setState(() => _focus = f ? _FocusField.email : _FocusField.none)),
                  const SizedBox(height: 16),
                  _field('Password', _passwordController, hint: 'Enter your password', obscure: true, onFocus: (f) => setState(() => _focus = f ? _FocusField.password : _FocusField.none)),
                  if (_isSignup) ...[
                    const SizedBox(height: 16),
                    _field('Confirm Password', _confirmPasswordController, hint: 'Confirm your password', obscure: true, onFocus: (f) => setState(() => _focus = f ? _FocusField.password : _FocusField.none)),
                  ],
                  const SizedBox(height: 12),
                  if (_isSignup) _policyRow() else _rememberRow(),
                  const SizedBox(height: 16),
                  _submitBtn(),
                  const SizedBox(height: 20),
                  _switchFooter(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _modeTabs() {
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(color: const Color(0xFFF8F9FA), borderRadius: BorderRadius.circular(12), border: Border.all(color: DriveLegalColors.borderStrong)),
      child: Row(
        children: [
          _tab('Sign In', !_isSignup, () => _switchMode(_AuthMode.signIn)),
          _tab('Sign Up', _isSignup, () => _switchMode(_AuthMode.signUp)),
        ],
      ),
    );
  }

  Widget _tab(String label, bool active, VoidCallback onTap) {
    return Expanded(
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 8.8),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            color: active ? Colors.white : null,
            border: active ? Border.all(color: DriveLegalColors.borderStrong) : null,
            boxShadow: active
                ? const [BoxShadow(color: Color(0x0A0F172A), blurRadius: 4, offset: Offset(0, 2))]
                : null,
          ),
          alignment: Alignment.center,
          child: Text(label, style: DriveLegalTheme.text(13.6, weight: FontWeight.w600, color: active ? DriveLegalColors.text : DriveLegalColors.muted)),
        ),
      ),
    );
  }

  Widget _field(
    String label,
    TextEditingController c, {
    String? hint,
    bool obscure = false,
    TextInputType? keyboard,
    void Function(bool)? onFocus,
    String? Function(String?)? validator,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: DriveLegalTheme.text(12.5, weight: FontWeight.w600, color: DriveLegalColors.label)),
        const SizedBox(height: 6),
        Focus(
          onFocusChange: onFocus,
          child: TextFormField(
            controller: c,
            obscureText: obscure,
            keyboardType: keyboard,
            validator: validator ??
                (v) {
                  if (v == null || v.isEmpty) return '$label is required';
                  if (label == 'Email' && !RegExp(r'^[^@]+@[^@]+\.[^@]+$').hasMatch(v.trim())) return 'Enter a valid email';
                  if ((label == 'Password' || label == 'Confirm Password') && _isSignup && v.length < 8) return 'At least 8 characters';
                  return null;
                },
            style: DriveLegalTheme.text(14.7),
            decoration: InputDecoration(hintText: hint),
          ),
        ),
      ],
    );
  }

  Widget _policyRow() => Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Checkbox(value: _agreePolicy, onChanged: (v) => setState(() => _agreePolicy = v ?? false)),
          Expanded(
            child: Text('I agree to the privacy policy and terms of use', style: DriveLegalTheme.text(12.5, color: DriveLegalColors.muted, height: 1.4)),
          ),
        ],
      );

  Widget _rememberRow() => Row(
        children: [
          Checkbox(value: _rememberMe, onChanged: (v) => setState(() => _rememberMe = v ?? false)),
          Text('Remember me', style: DriveLegalTheme.text(12.5, color: DriveLegalColors.muted)),
          const Spacer(),
          Text('Forgot password?', style: DriveLegalTheme.text(12.5, color: DriveLegalColors.primary)),
        ],
      );

  Widget _submitBtn() => ElevatedButton(
        onPressed: _loading ? null : _submit,
        style: ElevatedButton.styleFrom(
          backgroundColor: DriveLegalColors.primary,
          shadowColor: Colors.transparent,
          minimumSize: const Size.fromHeight(48),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: _loading
            ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
            : Text(_isSignup ? 'Create Account' : 'Sign In', style: DriveLegalTheme.text(15.2, weight: FontWeight.w600, color: Colors.white)),
      );

  Widget _switchFooter() {
    return Center(
      child: Wrap(
        alignment: WrapAlignment.center,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          Text(_isSignup ? 'Already have an account? ' : "Don't have an account? ", style: DriveLegalTheme.text(13.6, color: DriveLegalColors.muted)),
          GestureDetector(
            onTap: () => _switchMode(_isSignup ? _AuthMode.signIn : _AuthMode.signUp),
            child: Text(_isSignup ? 'Sign in' : 'Sign up', style: DriveLegalTheme.text(13.6, weight: FontWeight.w600, color: DriveLegalColors.primary)),
          ),
        ],
      ),
    );
  }

  Widget _errorBox() => Container(
        padding: const EdgeInsets.symmetric(horizontal: 13.6, vertical: 10.4),
        decoration: BoxDecoration(
          color: DriveLegalColors.errorBg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0x4DF59E0B)),
        ),
        child: Text(_error!, style: DriveLegalTheme.text(13.1, color: DriveLegalColors.errorText)),
      );
}

enum _FocusField { email, password, none }
