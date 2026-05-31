import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'shield_avatar.dart';

/// Matches web ShieldMascot compact variant in chat view.
class ShieldMascotBar extends StatelessWidget {
  const ShieldMascotBar({
    super.key,
    required this.speech,
    this.isTalking = false,
    this.isListening = false,
  });

  final String speech;
  final bool isTalking;
  final bool isListening;

  @override
  Widget build(BuildContext context) {
    final display = isListening
        ? "I'm listening… go ahead and ask your question."
        : (speech.isNotEmpty ? speech : "Hi! I'm Shield — your AI Road Law Assistant.");

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13.6),
      decoration: BoxDecoration(
        gradient: DriveLegalColors.mascotBarGradient,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: DriveLegalColors.borderStrong),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          const ShieldAvatar(size: ShieldAvatarSize.compact),
          const SizedBox(width: 13.6),
          Expanded(child: _SpeechBubble(text: display, highlightShield: display.startsWith("Hi! I'm Shield"))),
        ],
      ),
    );
  }
}

class _SpeechBubble extends StatelessWidget {
  const _SpeechBubble({required this.text, this.highlightShield = false});

  final String text;
  final bool highlightShield;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18.4, vertical: 16),
      decoration: BoxDecoration(
        color: DriveLegalColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: DriveLegalColors.borderPrimary),
        boxShadow: const [BoxShadow(color: Color(0x59000000), blurRadius: 32, offset: Offset(0, 12))],
      ),
      child: highlightShield
          ? RichText(
              text: TextSpan(
                style: DriveLegalTheme.text(13.1, color: DriveLegalColors.textSoft, height: 1.5),
                children: [
                  const TextSpan(text: "Hi! I'm ", style: TextStyle(color: DriveLegalColors.textSoft)),
                  const TextSpan(text: 'Shield', style: TextStyle(color: DriveLegalColors.primary, fontWeight: FontWeight.w700)),
                  TextSpan(text: text.substring("Hi! I'm Shield".length)),
                ],
              ),
            )
          : Text(text, style: DriveLegalTheme.text(13.1, color: DriveLegalColors.textSoft, height: 1.5)),
    );
  }
}
