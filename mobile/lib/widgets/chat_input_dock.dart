import 'package:flutter/material.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;

import '../theme/app_theme.dart';

typedef SendCallback = void Function(String text);

class ChatInputDock extends StatefulWidget {
  const ChatInputDock({
    super.key,
    required this.controller,
    required this.onSend,
    required this.onScanTicket,
    this.disabled = false,
    this.onListeningChange,
  });

  final TextEditingController controller;
  final SendCallback onSend;
  final Future<void> Function() onScanTicket;
  final bool disabled;
  final ValueChanged<bool>? onListeningChange;

  @override
  State<ChatInputDock> createState() => _ChatInputDockState();
}

class _ChatInputDockState extends State<ChatInputDock> {
  final stt.SpeechToText _speech = stt.SpeechToText();
  bool _listening = false;
  bool _speechReady = false;

  @override
  void initState() {
    super.initState();
    widget.controller.addListener(_onTextChanged);
    _initSpeech();
  }

  @override
  void dispose() {
    widget.controller.removeListener(_onTextChanged);
    super.dispose();
  }

  void _onTextChanged() => setState(() {});

  Future<void> _initSpeech() async {
    _speechReady = await _speech.initialize();
    if (mounted) setState(() {});
  }

  Future<void> _toggleMic() async {
    if (!_speechReady) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Voice input is not available on this device.')),
      );
      return;
    }
    if (_listening) {
      await _speech.stop();
      setState(() => _listening = false);
      widget.onListeningChange?.call(false);
      return;
    }
    setState(() => _listening = true);
    widget.onListeningChange?.call(true);
    await _speech.listen(
      onResult: (r) {
        widget.controller.text = r.recognizedWords;
      },
      localeId: 'en_IN',
    );
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(13.6),
      decoration: BoxDecoration(
        color: DriveLegalColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: DriveLegalColors.border),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          _prominentMic(),
          const SizedBox(width: 10.4),
          _scanBtn(),
          const SizedBox(width: 10.4),
          Expanded(child: _textarea()),
          const SizedBox(width: 10.4),
          _sendBtn(),
        ],
      ),
    );
  }

  Widget _prominentMic() {
    final active = _listening;
    return Material(
      color: active ? const Color(0x1ADC2626) : DriveLegalColors.inputBg,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: widget.disabled ? null : _toggleMic,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          height: 48,
          padding: const EdgeInsets.symmetric(horizontal: 14),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: active ? const Color(0x80F87171) : DriveLegalColors.borderPrimary),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(active ? Icons.mic_off : Icons.mic, size: 18, color: active ? const Color(0xFFFCA5A5) : const Color(0xFFE879F9)),
              const SizedBox(width: 6),
              Text('Mic', style: DriveLegalTheme.text(13.6, weight: FontWeight.w600, color: active ? const Color(0xFFFCA5A5) : const Color(0xFFE879F9))),
            ],
          ),
        ),
      ),
    );
  }

  Widget _scanBtn() {
    return Material(
      color: DriveLegalColors.card,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: widget.disabled ? null : widget.onScanTicket,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          width: 48,
          height: 48,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: DriveLegalColors.border),
          ),
          child: const Icon(Icons.document_scanner_outlined, size: 20, color: DriveLegalColors.muted),
        ),
      ),
    );
  }

  Widget _textarea() {
    return TextField(
      controller: widget.controller,
      enabled: !widget.disabled,
      maxLines: 4,
      minLines: 1,
      style: DriveLegalTheme.text(14.7),
      decoration: const InputDecoration(
        hintText: 'Ask Shield anything about traffic laws, fines, or challans…',
        border: OutlineInputBorder(borderRadius: BorderRadius.all(Radius.circular(12))),
      ),
      onSubmitted: widget.disabled ? null : (_) => _submit(),
    );
  }

  Widget _sendBtn() {
    final enabled = !widget.disabled && widget.controller.text.trim().isNotEmpty;
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: enabled ? DriveLegalColors.primaryGradient : null,
        color: enabled ? null : DriveLegalColors.inputBg,
        borderRadius: BorderRadius.circular(12),
      ),
      child: SizedBox(
        width: 48,
        height: 48,
        child: IconButton(
          onPressed: enabled ? _submit : null,
          icon: Icon(Icons.send_rounded, color: enabled ? Colors.white : DriveLegalColors.muted, size: 18),
        ),
      ),
    );
  }

  void _submit() {
    final t = widget.controller.text.trim();
    if (t.isEmpty) return;
    widget.onSend(t);
    widget.controller.clear();
    setState(() {});
  }
}
