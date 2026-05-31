import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import '../services/api_service.dart';
import '../theme/auth_theme.dart';
import 'chat_screen.dart';

enum _AuthView { welcome, signUp, signIn }

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
  final _apiService = ApiService();

  _AuthView _view = _AuthView.welcome;
  bool _isLoading = false;
  bool _agreePolicy = false;
  bool _rememberMe = false;
  String? _errorMessage;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  void _goTo(_AuthView view) {
    setState(() {
      _view = view;
      _errorMessage = null;
      _passwordController.clear();
      _confirmPasswordController.clear();
    });
  }

  Future<void> _submit({required bool isRegister}) async {
    if (!_formKey.currentState!.validate()) return;
    if (isRegister && !_agreePolicy) {
      setState(() => _errorMessage = 'Please agree to the privacy policy.');
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final email = _emailController.text.trim();
      if (isRegister) {
        if (_passwordController.text != _confirmPasswordController.text) {
          throw Exception('Passwords do not match.');
        }
        await _apiService.register(email, _passwordController.text);
      } else {
        await _apiService.login(email, _passwordController.text);
      }
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const ChatScreen()),
        );
      }
    } catch (e) {
      setState(() {
        _errorMessage = e.toString().replaceAll('Exception: ', '');
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AuthColors.background,
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
              child: _buildContent(),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildContent() {
    switch (_view) {
      case _AuthView.welcome:
        return _welcomeContent();
      case _AuthView.signUp:
        return _formContent(
          title: 'Create your account',
          subtitle: "Let's get you set up — I'll help with traffic laws from day one.",
          isRegister: true,
          footer: 'Already have an account? Sign in',
          onFooter: () => _goTo(_AuthView.signIn),
        );
      case _AuthView.signIn:
        return _formContent(
          title: 'Welcome back',
          subtitle: 'Shield is ready to assist you with traffic laws, challans, vehicle documents, and road safety guidance.',
          isRegister: false,
          footer: "Don't have an account? Sign up",
          onFooter: () => _goTo(_AuthView.signUp),
        );
    }
  }

  Widget _formContent({
    required String title,
    required String subtitle,
    required bool isRegister,
    required String footer,
    required VoidCallback onFooter,
  }) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          IconButton(
            onPressed: () => _goTo(_AuthView.welcome),
            icon: const Icon(Icons.arrow_back_ios_new, size: 20),
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(),
          ),
          const SizedBox(height: 20),
          Text(title, style: _titleStyle()),
          const SizedBox(height: 8),
          Text(subtitle, style: _subtitleStyle()),
          if (_errorMessage != null) ...[
            const SizedBox(height: 16),
            _errorBox(),
          ],
          const SizedBox(height: 24),
          _field(_emailController, 'Email', Icons.mail_outline, keyboard: TextInputType.emailAddress),
          const SizedBox(height: 16),
          _field(_passwordController, 'Password', Icons.vpn_key_outlined, obscure: true),
          if (isRegister) ...[
            const SizedBox(height: 16),
            _field(_confirmPasswordController, 'Confirm Password', Icons.vpn_key_outlined, obscure: true),
            const SizedBox(height: 16),
            Row(
              children: [
                Checkbox(
                  value: _agreePolicy,
                  activeColor: AuthColors.primary,
                  onChanged: (v) => setState(() => _agreePolicy = v ?? false),
                ),
                Expanded(
                  child: Text('I agree to the privacy policy and terms of use', style: _subtitleStyle()),
                ),
              ],
            ),
          ] else ...[
            const SizedBox(height: 16),
            Row(
              children: [
                Checkbox(
                  value: _rememberMe,
                  activeColor: AuthColors.primary,
                  onChanged: (v) => setState(() => _rememberMe = v ?? false),
                ),
                Text('Remember me', style: _subtitleStyle()),
                const Spacer(),
                Text('Forgot password?', style: _linkStyle()),
              ],
            ),
          ],
          const SizedBox(height: 24),
          _submitButton(isRegister ? 'Create Account' : 'Sign In'),
          const SizedBox(height: 20),
          Center(
            child: TextButton(onPressed: onFooter, child: Text(footer, style: _linkStyle())),
          ),
        ],
      ),
    );
  }

  Widget _welcomeContent() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 40),
        Text('DriveLegal', style: _brandStyle()),
        const SizedBox(height: 8),
        Text('Know the law before you pay the fine.', style: _subtitleStyle()),
        const SizedBox(height: 4),
        Text("India's AI-powered traffic law assistant.", style: _subtitleStyle()),
        const SizedBox(height: 48),
        Text('Get Started', style: _titleStyle()),
        const SizedBox(height: 8),
        Text('Start with sign up or sign in', style: _subtitleStyle()),
        const SizedBox(height: 32),
        _pillButton('Sign Up', () => _goTo(_AuthView.signUp)),
        const SizedBox(height: 16),
        _pillButton('Sign In', () => _goTo(_AuthView.signIn)),
      ],
    );
  }

  TextStyle _brandStyle() => GoogleFonts.inter(
        fontSize: 32,
        fontWeight: FontWeight.w700,
        color: AuthColors.textPrimary,
        letterSpacing: -0.5,
      );

  TextStyle _titleStyle() => GoogleFonts.inter(
        fontSize: 32,
        fontWeight: FontWeight.w600,
        color: AuthColors.textPrimary,
        letterSpacing: -0.5,
      );

  TextStyle _subtitleStyle() => GoogleFonts.inter(
        fontSize: 15,
        color: AuthColors.textSecondary,
        height: 1.5,
      );

  TextStyle _linkStyle() => GoogleFonts.inter(
        color: AuthColors.textPrimary,
        fontWeight: FontWeight.w600,
        fontSize: 14,
      );

  Widget _errorBox() => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AuthColors.errorBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFFFECACA)),
        ),
        child: Text(_errorMessage!, style: GoogleFonts.inter(color: AuthColors.errorText, fontSize: 13)),
      );

  Widget _field(
    TextEditingController controller,
    String hint,
    IconData icon, {
    bool obscure = false,
    TextInputType? keyboard,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(hint, style: GoogleFonts.inter(fontSize: 13, fontWeight: FontWeight.w500, color: AuthColors.label)),
        const SizedBox(height: 8),
        TextFormField(
          controller: controller,
          obscureText: obscure,
          keyboardType: keyboard,
          validator: (v) {
            if (v == null || v.isEmpty) return '$hint is required';
            if (hint == 'Email' && !RegExp(r'^[^@]+@[^@]+\.[^@]+$').hasMatch(v.trim())) {
              return 'Enter a valid email';
            }
            if ((hint == 'Password' || hint == 'Confirm Password') && v.length < 8) {
              return 'At least 8 characters';
            }
            if (hint == 'Confirm Password' && v != _passwordController.text) {
              return 'Passwords do not match';
            }
            return null;
          },
          decoration: InputDecoration(
            hintText: hint,
            filled: true,
            fillColor: Colors.white,
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AuthColors.borderStrong),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AuthColors.borderStrong),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AuthColors.primary),
            ),
          ),
        ),
      ],
    );
  }

  Widget _pillButton(String label, VoidCallback? onPressed) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: AuthColors.primary,
          foregroundColor: Colors.white,
          elevation: 0,
          shadowColor: Colors.transparent,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: Text(
          label,
          style: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 15),
        ),
      ),
    );
  }

  Widget _submitButton(String label) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: _isLoading ? null : () => _submit(isRegister: _view == _AuthView.signUp),
        style: ElevatedButton.styleFrom(
          backgroundColor: AuthColors.primary,
          foregroundColor: Colors.white,
          elevation: 0,
          shadowColor: Colors.transparent,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
        child: _isLoading
            ? const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
              )
            : Text(
                label,
                style: GoogleFonts.inter(fontWeight: FontWeight.w600, fontSize: 15),
              ),
      ),
    );
  }
}

