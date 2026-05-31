import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Pearl / platinum design tokens (aligned with web_app tokens.css)
class DriveLegalColors {
  static const background = Color(0xFFFAFBFC);
  static const backgroundSoft = Color(0xFFF4F5F7);
  static const cardAuth = Color(0xFFFFFFFF);
  static const card = Color(0xFFFFFFFF);
  static const primary = Color(0xFF18181B);
  static const secondary = Color(0xFF3F3F46);
  static const accent = Color(0xFF64748B);
  static const text = Color(0xFF18181B);
  static const textSoft = Color(0xFF3F3F46);
  static const label = Color(0xFF52525B);
  static const muted = Color(0xFF71717A);
  static const placeholder = Color(0xFFA1A1AA);
  static const inputBg = Color(0xFFF8F9FA);
  static const border = Color(0x140F172A);
  static const borderStrong = Color(0x1F0F172A);
  static const borderPrimary = Color(0x1F0F172A);
  static const errorBg = Color(0x14DC2626);
  static const errorText = Color(0xFFB91C1C);
  static const success = Color(0xFF16A34A);
  static const danger = Color(0xFFDC2626);
  static const chipText = Color(0xFF3F3F46);
  static const locationBarBg = Color(0xB8FFFFFF);

  static const primaryGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xFF27272A), Color(0xFF18181B)],
  );

  static const userBubbleGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xF5FFFFFF), Color(0xE8FFFFFF)],
  );

  static const mascotBarGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [Color(0xE8FFFFFF), Color(0xD8FFFFFF)],
  );
}

class DriveLegalTheme {
  static TextStyle text(double size, {FontWeight weight = FontWeight.w400, Color? color, double? height}) {
    return GoogleFonts.inter(fontSize: size, fontWeight: weight, color: color ?? DriveLegalColors.text, height: height);
  }

  static ThemeData dark() {
    return ThemeData(
      brightness: Brightness.light,
      useMaterial3: true,
      scaffoldBackgroundColor: DriveLegalColors.background,
      fontFamily: GoogleFonts.inter().fontFamily,
      colorScheme: const ColorScheme.light(
        primary: DriveLegalColors.primary,
        secondary: DriveLegalColors.secondary,
        surface: DriveLegalColors.card,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        hintStyle: DriveLegalTheme.text(14.7, color: DriveLegalColors.placeholder),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13.6),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: DriveLegalColors.borderStrong)),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: const BorderSide(color: DriveLegalColors.borderStrong)),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: DriveLegalColors.primary),
        ),
      ),
      checkboxTheme: CheckboxThemeData(
        fillColor: WidgetStateProperty.resolveWith((_) => DriveLegalColors.primary),
      ),
    );
  }
}

class DriveLegalDecor {
  static BoxDecoration authShell() => const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFAFBFC), Color(0xFFEEF1F5), Color(0xFFE8EAEF)],
        ),
      );

  static BoxDecoration chatShell() => const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: [Color(0xFFFAFBFC), Color(0xFFEEF1F5)],
        ),
      );

  static Widget brandText({double fontSize = 28}) => Text(
        'DriveLegal',
        style: DriveLegalTheme.text(fontSize, weight: FontWeight.w700, color: DriveLegalColors.text).copyWith(letterSpacing: -0.5),
      );
}
