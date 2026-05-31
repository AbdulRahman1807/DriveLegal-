import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Visual match for web RoadSafetySimulator (login / footer variants).
class RoadSafetySimulator extends StatefulWidget {
  const RoadSafetySimulator({super.key, this.variant = RoadSimulatorVariant.login, this.onShieldComment});

  final RoadSimulatorVariant variant;
  final ValueChanged<String>? onShieldComment;

  @override
  State<RoadSafetySimulator> createState() => _RoadSafetySimulatorState();
}

enum RoadSimulatorVariant { login, footer }

class _RoadSafetySimulatorState extends State<RoadSafetySimulator> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  int _phase = 0; // 0 green, 1 amber, 2 red
  Timer? _phaseTimer;

  double get _height => widget.variant == RoadSimulatorVariant.login ? 158 : 118;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(vsync: this, duration: const Duration(milliseconds: 2200))..repeat();
    _phaseTimer = Timer.periodic(const Duration(seconds: 4), (_) {
      setState(() => _phase = (_phase + 1) % 3);
    });
  }

  @override
  void dispose() {
    _phaseTimer?.cancel();
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: _height,
      width: double.infinity,
      child: ClipRect(
        child: AnimatedBuilder(
          animation: _ctrl,
          builder: (context, _) => CustomPaint(
            painter: _RoadScenePainter(phase: _phase, t: _ctrl.value, compact: widget.variant == RoadSimulatorVariant.footer),
            child: Stack(
              children: [
                Positioned(
                  top: 6,
                  left: 8,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Chennai, Tamil Nadu', style: DriveLegalTheme.text(8.3, weight: FontWeight.w700, color: DriveLegalColors.textSoft)),
                      const SizedBox(height: 2),
                      if (widget.variant == RoadSimulatorVariant.login)
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: const Color(0xFF1A1A23),
                            borderRadius: BorderRadius.circular(4),
                            border: Border.all(color: DriveLegalColors.borderStrong),
                            boxShadow: const [BoxShadow(color: Color(0x0A0F172A), blurRadius: 4, offset: Offset(0, 2))],
                          ),
                          child: Text('MV Act · Chennai', style: DriveLegalTheme.text(7.7, weight: FontWeight.w600, color: DriveLegalColors.muted)),
                        ),
                    ],
                  ),
                ),
                Positioned(
                  top: 48,
                  right: 16,
                  child: _TrafficLight(phase: _phase),
                ),
                Positioned(
                  left: 8,
                  right: 8,
                  bottom: 6,
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF1A1A23),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: DriveLegalColors.borderStrong),
                      boxShadow: const [BoxShadow(color: Color(0x0A0F172A), blurRadius: 4, offset: Offset(0, 2))],
                    ),
                    child: Row(
                      children: [
                        Container(
                          width: 6,
                          height: 6,
                          decoration: const BoxDecoration(color: DriveLegalColors.primary, shape: BoxShape.circle),
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: RichText(
                            text: TextSpan(
                              style: DriveLegalTheme.text(8.6, color: DriveLegalColors.textSoft, height: 1.35),
                              children: const [
                                TextSpan(text: 'Shield: ', style: TextStyle(color: DriveLegalColors.primary, fontWeight: FontWeight.w700)),
                                TextSpan(text: 'Stop at red. Helmet saves lives.'),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TrafficLight extends StatelessWidget {
  const _TrafficLight({required this.phase});
  final int phase;

  @override
  Widget build(BuildContext context) {
    Widget bulb(Color c, bool on) => Container(
          width: 11,
          height: 11,
          margin: const EdgeInsets.symmetric(vertical: 2.5),
          decoration: BoxDecoration(
            color: c.withValues(alpha: on ? 1 : 0.18),
            shape: BoxShape.circle,
            boxShadow: on ? [BoxShadow(color: c.withValues(alpha: 0.6), blurRadius: 6)] : null,
          ),
        );
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1A23),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0x1FFFFFFF)),
        boxShadow: const [BoxShadow(color: Color(0x0A0F172A), blurRadius: 4, offset: Offset(0, 2))],
      ),
      child: Column(
        children: [
          bulb(const Color(0xFFEF4444), phase == 2),
          bulb(const Color(0xFFF59E0B), phase == 1),
          bulb(const Color(0xFF22C55E), phase == 0),
        ],
      ),
    );
  }
}

class _RoadScenePainter extends CustomPainter {
  _RoadScenePainter({required this.phase, required this.t, required this.compact});

  final int phase;
  final double t;
  final bool compact;

  @override
  void paint(Canvas canvas, Size size) {
    final bg = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color(0xFFEEF1F5), Color(0xFFE2E6EC), Color(0xFFD4DAE2)],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));
    canvas.drawRect(Offset.zero & size, bg);

    final roadTop = size.height * 0.54;
    final road = Paint()
      ..shader = const LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [Color(0xFF3D4F63), Color(0xFF283040)],
      ).createShader(Rect.fromLTWH(0, roadTop, size.width, size.height - roadTop));
    final path = Path()
      ..moveTo(size.width * 0.04, roadTop)
      ..lineTo(size.width * 0.96, roadTop)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    canvas.drawPath(path, road);

    final stripe = Paint()..color = const Color(0xFFFFFFFF).withValues(alpha: 0.7);
    for (var x = -40.0 + (t * 40) % 40; x < size.width; x += 40) {
      canvas.drawRect(Rect.fromLTWH(x, roadTop + 28, 20, 3), stripe);
    }

    final bikeX = size.width * (0.1 + (phase == 2 ? 0.15 : (t * 0.5) % 0.55));
    _drawVehicle(canvas, bikeX, size.height * 0.62, 40, 28, const Color(0xFF64748B));
    if (!compact) {
      _drawVehicle(canvas, size.width * (0.2 + t * 0.4), size.height * 0.72, 48, 24, const Color(0xFF4F46E5));
    }
  }

  void _drawVehicle(Canvas canvas, double x, double y, double w, double h, Color color) {
    final r = RRect.fromRectAndRadius(Rect.fromLTWH(x, y, w, h), const Radius.circular(6));
    canvas.drawRRect(r, Paint()..color = color.withValues(alpha: 0.85));
    canvas.drawRRect(r, Paint()..color = Colors.black26..style = PaintingStyle.stroke..strokeWidth = 1);
  }

  @override
  bool shouldRepaint(covariant _RoadScenePainter old) => old.phase != phase || old.t != t;
}
