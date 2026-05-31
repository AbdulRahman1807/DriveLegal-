import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

enum ShieldAvatarSize { hero, compact, auth }

class ShieldAvatar extends StatelessWidget {
  const ShieldAvatar({super.key, this.size = ShieldAvatarSize.hero, this.showDragHint = false, this.isTalking = false, this.isListening = false, this.isThinking = false});

  final ShieldAvatarSize size;
  final bool showDragHint;
  final bool isTalking;
  final bool isListening;
  final bool isThinking;

  double get _width => switch (size) {
        ShieldAvatarSize.hero => 140,
        ShieldAvatarSize.compact => 72,
        ShieldAvatarSize.auth => 240,
      };

  double get _height => switch (size) {
        ShieldAvatarSize.hero => 150,
        ShieldAvatarSize.compact => 78,
        ShieldAvatarSize.auth => 260,
      };

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        SizedBox(
          width: _width,
          height: _height,
          child: Image.asset(
            'assets/images/shield-mascot.png',
            fit: BoxFit.contain,
            errorBuilder: (_, __, ___) => Icon(Icons.shield_rounded, size: _width * 0.65, color: DriveLegalColors.primary),
          ),
        ),
        if (showDragHint) ...[
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.95),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: DriveLegalColors.borderPrimary),
              boxShadow: [
                BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 16, offset: const Offset(0, 4)),
              ],
            ),
            child: Text(
              '↻ Drag Shield to look around',
              style: DriveLegalTheme.text(11, weight: FontWeight.w600, color: DriveLegalColors.textSoft),
            ),
          ),
        ],
      ],
    );
  }
}
