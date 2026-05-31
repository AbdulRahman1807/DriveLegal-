import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/chat_input_dock.dart';
import '../widgets/citation_chip.dart';
import '../widgets/road_safety_simulator.dart';
import '../widgets/shield_avatar.dart';
import '../widgets/shield_mascot_bar.dart';
import 'account_screen.dart';
import 'auth_screen.dart';

class ChatMessage {
  ChatMessage({required this.text, required this.isUser, this.citations, this.fines, this.isError = false});
  final String text;
  final bool isUser;
  final List<dynamic>? citations;
  final List<dynamic>? fines;
  final bool isError;
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  static const _quickTopics = <({IconData icon, String label, String query})>[
    (icon: Icons.safety_check_outlined, label: 'Helmet', query: 'What is the fine for riding without a helmet in India?'),
    (icon: Icons.description_outlined, label: 'Documents', query: 'What documents should I carry while driving?'),
    (icon: Icons.speed_outlined, label: 'Speed', query: 'What are the speed limits and fines for overspeeding?'),
    (icon: Icons.wine_bar_outlined, label: 'Alcohol', query: 'What is the penalty for drunk driving under Section 185?'),
  ];

  static const _popularQuestions = [
    'What documents should I carry?',
    'Fine for riding without helmet?',
    'Can I use DigiLocker?',
    'What is Section 185?',
  ];

  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  final _api = ApiService();
  final _picker = ImagePicker();

  final List<ChatMessage> _messages = [];
  bool _isLoading = false;
  bool _isListening = false;

  String get _userName {
    final email = ApiService.userEmail;
    if (email == null || !email.contains('@')) return 'there';
    final local = email.split('@').first;
    if (local.isEmpty) return 'there';
    return local[0].toUpperCase() + local.substring(1);
  }

  bool get _hasStartedChat => _messages.isNotEmpty;

  ChatMessage? get _lastBot {
    for (var i = _messages.length - 1; i >= 0; i--) {
      if (!_messages[i].isUser) return _messages[i];
    }
    return null;
  }

  String get _mascotSpeech {
    if (_isListening) return "I'm listening… go ahead and ask your question.";
    if (_isLoading) return 'Let me check the Motor Vehicles Act for you…';
    final last = _lastBot;
    if (last != null && last.text.isNotEmpty) {
      final clean = last.text.replaceAll(RegExp(r'\s+'), ' ').trim();
      return clean.length <= 140 ? clean : '${clean.substring(0, 140).trim()}…';
    }
    if (_messages.any((m) => m.isUser)) return 'Searching Indian traffic laws…';
    return '';
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!ApiService.isAuthenticated && mounted) {
        Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const AuthScreen()));
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage(String text) async {
    final trimmed = text.trim();
    if (trimmed.isEmpty || _isLoading) return;

    setState(() {
      _messages.add(ChatMessage(text: trimmed, isUser: true));
      _isLoading = true;
    });
    _scrollToBottom();

    try {
      final sessionId = ApiService.userEmail ?? 'mobile_session';
      final response = await _api.sendQuery(trimmed, sessionId);
      setState(() {
        _messages.add(ChatMessage(
          text: response['reply']?.toString() ?? 'No response',
          isUser: false,
          citations: response['citations'] as List<dynamic>?,
          fines: response['fines'] as List<dynamic>?,
        ));
      });
    } catch (_) {
      setState(() {
        _messages.add(ChatMessage(
          text: 'Shield is temporarily unavailable. Please try again.',
          isUser: false,
          isError: true,
        ));
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
      _scrollToBottom();
    }
  }

  Future<void> _scanTicket() async {
    final image = await _picker.pickImage(source: ImageSource.gallery);
    if (image == null) return;
    setState(() => _isLoading = true);
    try {
      final bytes = await image.readAsBytes();
      final mime = image.name.toLowerCase().endsWith('.png') ? 'image/png' : 'image/jpeg';
      final response = await _api.analyzeTicket(base64Encode(bytes), mime);
      final extracted = response['extracted_text'] ?? '';
      final violation = response['inferred_violation'] ?? 'Unknown';
      final fine = response['detected_fine'] ?? 0;
      setState(() {
        _messages.add(ChatMessage(text: '📸 Uploaded a traffic ticket for analysis.', isUser: true));
        _isLoading = false;
      });
      await _sendMessage(
        'I received a ticket. The scanner extracted this text: "$extracted". It thinks the violation is "$violation" with a fine of ₹$fine. Can you confirm if this is correct under the law?',
      );
    } catch (e) {
      setState(() {
        _messages.add(ChatMessage(text: 'Error scanning ticket: $e', isUser: false, isError: true));
        _isLoading = false;
      });
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
              _locationBar(),
              Expanded(
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 720),
                    child: _hasStartedChat ? _chatView() : _emptyLayout(),
                  ),
                ),
              ),
              Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 720),
                  child: const Padding(
                    padding: EdgeInsets.fromLTRB(16, 0, 16, 12),
                    child: SizedBox.shrink(),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _locationBar() {
    final showMeta = MediaQuery.sizeOf(context).width > 768;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10.4),
      decoration: const BoxDecoration(
        color: DriveLegalColors.locationBarBg,
        border: Border(bottom: BorderSide(color: DriveLegalColors.border)),
      ),
      child: Row(
        children: [
          DriveLegalDecor.brandText(fontSize: 15.2),
          if (showMeta) ...[
            Expanded(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.location_on_outlined, size: 13, color: DriveLegalColors.muted),
                  const SizedBox(width: 4),
                  Text('Chennai, Tamil Nadu', style: DriveLegalTheme.text(11.5, color: DriveLegalColors.muted)),
                  Container(
                    margin: const EdgeInsets.symmetric(horizontal: 8),
                    width: 1,
                    height: 12,
                    color: DriveLegalColors.border,
                  ),
                  const Icon(Icons.verified_user_outlined, size: 13, color: DriveLegalColors.muted),
                  const SizedBox(width: 4),
                  Text('Verified Dataset', style: DriveLegalTheme.text(11.5, color: DriveLegalColors.muted)),
                ],
              ),
            ),
          ] else
            const Spacer(),
          _locBtn(Icons.settings_outlined, () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AccountScreen()))),
          _locBtn(Icons.logout_rounded, () async {
            await _api.logout();
            if (!mounted) return;
            Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => const AuthScreen()));
          }),
        ],
      ),
    );
  }

  Widget _locBtn(IconData icon, VoidCallback onTap) {
    return Padding(
      padding: const EdgeInsets.only(left: 6),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          width: 34,
          height: 34,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: DriveLegalColors.card,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: DriveLegalColors.border),
          ),
          child: Icon(icon, size: 16, color: DriveLegalColors.muted),
        ),
      ),
    );
  }

  Widget _emptyLayout() {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
      children: [
        _heroCard(),
        const SizedBox(height: 13.6),
        ChatInputDock(
          controller: _controller,
          disabled: _isLoading,
          onSend: _sendMessage,
          onScanTicket: _scanTicket,
          onListeningChange: (v) => setState(() => _isListening = v),
        ),
        const SizedBox(height: 13.6),
        _popularSection(),
      ],
    );
  }

  Widget _chatView() {
    return Column(
      children: [
        Expanded(
          child: ListView(
            controller: _scrollController,
            padding: const EdgeInsets.fromLTRB(20, 16, 20, 8),
            children: [
              ShieldMascotBar(
                speech: _mascotSpeech,
                isTalking: _isLoading || _isListening || _lastBot != null,
                isListening: _isListening,
              ),
              const SizedBox(height: 12),
              ..._messages.map(_bubble),
              if (_isLoading) _typing(),
            ],
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
          child: Column(
            children: [
              ChatInputDock(
                controller: _controller,
                disabled: _isLoading,
                onSend: _sendMessage,
                onScanTicket: _scanTicket,
                onListeningChange: (v) => setState(() => _isListening = v),
              ),
              const SizedBox(height: 13.6),
              _popularSection(),
            ],
          ),
        ),
      ],
    );
  }

  Widget _heroCard() {
    final narrow = MediaQuery.sizeOf(context).width <= 768;
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 18.4, 20, 18.4),
      decoration: BoxDecoration(
        color: DriveLegalColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: DriveLegalColors.border),
        boxShadow: const [BoxShadow(color: Color(0x33000000), blurRadius: 40, offset: Offset(0, 12))],
      ),
      child: narrow
          ? Column(
              children: [
                const ShieldAvatar(size: ShieldAvatarSize.hero),
                const SizedBox(height: 16),
                _heroText(),
              ],
            )
          : Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const ShieldAvatar(size: ShieldAvatarSize.hero),
                const SizedBox(width: 20),
                Expanded(child: _heroText()),
              ],
            ),
    );
  }

  Widget _heroText() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Hi $_userName', style: DriveLegalTheme.text(18.4, weight: FontWeight.w700)),
        const SizedBox(height: 6),
        Text(
          'Ask me about traffic laws, fines, challans and required documents.',
          style: DriveLegalTheme.text(14.1, color: DriveLegalColors.muted, height: 1.5),
        ),
        const SizedBox(height: 13.6),
        LayoutBuilder(
          builder: (context, c) {
            final cols = c.maxWidth < 480 ? 1 : 2;
            return GridView.count(
              crossAxisCount: cols,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 8,
              crossAxisSpacing: 8,
              childAspectRatio: cols == 1 ? 4.5 : 2.4,
              children: _quickTopics.map((t) => _topicBtn(t.icon, t.label, t.query)).toList(),
            );
          },
        ),
      ],
    );
  }

  Widget _topicBtn(IconData icon, String label, String query) {
    return Material(
      color: DriveLegalColors.inputBg,
      borderRadius: BorderRadius.circular(10),
      child: InkWell(
        onTap: _isLoading ? null : () => _sendMessage(query),
        borderRadius: BorderRadius.circular(10),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8.8),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: DriveLegalColors.border),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 15, color: DriveLegalColors.accent),
              const SizedBox(width: 6),
              Flexible(child: Text(label, style: DriveLegalTheme.text(12.8, weight: FontWeight.w600), overflow: TextOverflow.ellipsis)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _popularSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(Icons.lightbulb_outline, size: 14, color: DriveLegalColors.accent),
            const SizedBox(width: 5.6),
            Text('Popular Questions', style: DriveLegalTheme.text(12, weight: FontWeight.w600, color: DriveLegalColors.accent)),
          ],
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: _popularQuestions.map((q) {
            return Material(
              color: DriveLegalColors.inputBg,
              borderRadius: BorderRadius.circular(999),
              child: InkWell(
                onTap: _isLoading ? null : () => _sendMessage(q),
                borderRadius: BorderRadius.circular(999),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 13.6, vertical: 7.2),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(999),
                    border: Border.all(color: DriveLegalColors.border),
                  ),
                  child: Text(q, style: DriveLegalTheme.text(12.5, color: DriveLegalColors.label)),
                ),
              ),
            );
          }).toList(),
        ),
      ],
    );
  }

  Widget _bubble(ChatMessage msg) {
    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        constraints: BoxConstraints(maxWidth: MediaQuery.sizeOf(context).width * 0.88),
        margin: const EdgeInsets.only(bottom: 13.6),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13.6),
        decoration: BoxDecoration(
          gradient: msg.isUser ? DriveLegalColors.userBubbleGradient : null,
          color: msg.isUser
              ? null
              : (msg.isError ? DriveLegalColors.errorBg : DriveLegalColors.card),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(14),
            topRight: const Radius.circular(14),
            bottomLeft: Radius.circular(msg.isUser ? 14 : 4),
            bottomRight: Radius.circular(msg.isUser ? 4 : 14),
          ),
          border: Border.all(
            color: msg.isError
                ? const Color(0x59F59E0B)
                : (msg.isUser ? DriveLegalColors.borderStrong : DriveLegalColors.border),
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              msg.text,
              style: DriveLegalTheme.text(14.7, height: 1.55, color: msg.isError ? DriveLegalColors.errorText : DriveLegalColors.text),
            ),
            if (msg.fines != null && msg.fines!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(10.4),
                decoration: const BoxDecoration(
                  color: Color(0x14EF4444),
                  borderRadius: BorderRadius.only(topRight: Radius.circular(8), bottomRight: Radius.circular(8)),
                  border: Border(left: BorderSide(color: Color(0xFFEF4444), width: 3)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.warning_amber_rounded, size: 16, color: Color(0xFFF87171)),
                        const SizedBox(width: 6),
                        Text('Applicable Fines', style: DriveLegalTheme.text(13.6, weight: FontWeight.w600, color: Color(0xFFF87171))),
                      ],
                    ),
                    ...msg.fines!.map((f) {
                      return Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text('• ${f['violation_name']}: ₹${f['total_fine']} (${f['jurisdiction_name']})', style: DriveLegalTheme.text(13.6)),
                      );
                    }),
                  ],
                ),
              ),
            ],
            if (msg.citations != null && msg.citations!.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Divider(color: DriveLegalColors.border, height: 1),
              const SizedBox(height: 10),
              Row(
                children: [
                  const Icon(Icons.menu_book_outlined, size: 14, color: DriveLegalColors.label),
                  const SizedBox(width: 6),
                  Text('Legal Citations', style: DriveLegalTheme.text(13.1, weight: FontWeight.w600, color: DriveLegalColors.label)),
                ],
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 7.2,
                runSpacing: 7.2,
                children: msg.citations!.map((c) => CitationChip(citation: Map<String, dynamic>.from(c as Map), api: _api)).toList(),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _typing() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 13.6),
        padding: const EdgeInsets.symmetric(horizontal: 14.4, vertical: 10.4),
        decoration: BoxDecoration(
          color: DriveLegalColors.card,
          borderRadius: const BorderRadius.only(topLeft: Radius.circular(14), topRight: Radius.circular(14), bottomLeft: Radius.circular(4), bottomRight: Radius.circular(14)),
          border: Border.all(color: DriveLegalColors.border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (i) => Container(
                margin: EdgeInsets.only(right: i < 2 ? 4 : 0),
                width: 6,
                height: 6,
                decoration: const BoxDecoration(color: DriveLegalColors.primary, shape: BoxShape.circle),
              )),
        ),
      ),
    );
  }
}
