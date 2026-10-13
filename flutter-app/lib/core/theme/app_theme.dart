import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_fonts/google_fonts.dart';

final themeProvider = StateNotifierProvider<ThemeNotifier, ThemeData>((ref) {
  return ThemeNotifier();
});

class ThemeNotifier extends StateNotifier<ThemeData> {
  ThemeNotifier() : super(_lightTheme);

  static final ThemeData _lightTheme = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: const ColorScheme.light(
      primary: Color(0xFFD4AF37), // Gold
      primaryContainer: Color(0xFFB8941F),
      secondary: Color(0xFFF1CA52),
      surface: Color(0xFF0F1A2E),
      background: Color(0xFF07111F),
      error: Color(0xFFEF4444),
      onPrimary: Color(0xFF111111),
      onSurface: Color(0xFFFFFFFF),
      onBackground: Color(0xFFFFFFFF),
      onError: Color(0xFFFFFFFF),
    ),
    scaffoldBackgroundColor: const Color(0xFF07111F),
    appBarTheme: AppBarTheme(
      backgroundColor: const Color(0xFF07111F),
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: true,
      titleTextStyle: GoogleFonts.cinzel(
        fontSize: 20,
        fontWeight: FontWeight.w700,
        color: const Color(0xFFD4AF37),
      ),
    ),
    cardTheme: CardTheme(
      color: const Color(0xFF0F1A2E),
      elevation: 4,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: Color(0xFFD4AF37), width: 1),
      ),
      margin: const EdgeInsets.all(12),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFFD4AF37),
        foregroundColor: const Color(0xFF111111),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(28),
        ),
        textStyle: GoogleFonts.poppins(
          fontSize: 16,
          fontWeight: FontWeight.w700,
        ),
        elevation: 4,
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: const Color(0xFFD4AF37),
        side: const BorderSide(color: Color(0xFFD4AF37), width: 2),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(28),
        ),
        textStyle: GoogleFonts.poppins(
          fontSize: 16,
          fontWeight: FontWeight.w600,
        ),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: const Color(0xFF08111F),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF39485F)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFF39485F)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFFD4AF37), width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: Color(0xFFEF4444)),
      ),
      labelStyle: GoogleFonts.poppins(
        color: const Color(0xFFD4AF37),
        fontSize: 14,
        fontWeight: FontWeight.w500,
      ),
      hintStyle: GoogleFonts.poppins(
        color: const Color(0xFF888888),
        fontSize: 14,
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
    ),
    bottomNavigationBarTheme: BottomNavigationBarThemeData(
      backgroundColor: const Color(0xFF0F1A2E),
      selectedItemColor: const Color(0xFFD4AF37),
      unselectedItemColor: const Color(0xFFA0B0C9),
      selectedLabelStyle: GoogleFonts.poppins(fontSize: 11, fontWeight: FontWeight.w600),
      unselectedLabelStyle: GoogleFonts.poppins(fontSize: 11, fontWeight: FontWeight.w500),
      type: BottomNavigationBarType.fixed,
      elevation: 20,
    ),
    bottomSheetTheme: const BottomSheetThemeData(
      backgroundColor: Color(0xFF0F1A2E),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
    ),
    dialogTheme: DialogTheme(
      backgroundColor: const Color(0xFF142238),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: Color(0xFFD4AF37)),
      ),
      titleTextStyle: GoogleFonts.cinzel(
        color: Color(0xFFD4AF37),
        fontSize: 20,
        fontWeight: FontWeight.w700,
      ),
      contentTextStyle: GoogleFonts.poppins(
        color: Colors.white,
        fontSize: 14,
      ),
    ),
    snackBarTheme: SnackBarThemeData(
      backgroundColor: const Color(0xFF142238),
      contentTextStyle: GoogleFonts.poppins(color: Colors.white),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      behavior: SnackBarBehavior.floating,
      actionTextColor: const Color(0xFFD4AF37),
    ),
    floatingActionButtonTheme: FloatingActionButtonThemeData(
      backgroundColor: const Color(0xFFD4AF37),
      foregroundColor: const Color(0xFF111111),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: const Color(0xFF0F1A2E),
      selectedColor: const Color(0xFFD4AF37),
      labelStyle: GoogleFonts.poppins(color: Colors.white),
      secondaryLabelStyle: GoogleFonts.poppins(color: Color(0xFF111111)),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: Color(0xFFD4AF37)),
      ),
    ),
    dividerTheme: const DividerThemeData(
      color: Color(0xFF1E2E4F),
      thickness: 1,
    ),
    textTheme: TextTheme(
      displayLarge: GoogleFonts.cinzel(
        fontSize: 55, fontWeight: FontWeight.w700, color: Color(0xFFD4AF37),
      ),
      displayMedium: GoogleFonts.cinzel(
        fontSize: 44, fontWeight: FontWeight.w700, color: Color(0xFFD4AF37),
      ),
      displaySmall: GoogleFonts.cinzel(
        fontSize: 36, fontWeight: FontWeight.w700, color: Color(0xFFD4AF37),
      ),
      headlineLarge: GoogleFonts.cinzel(
        fontSize: 32, fontWeight: FontWeight.w700, color: Colors.white,
      ),
      headlineMedium: GoogleFonts.cinzel(
        fontSize: 28, fontWeight: FontWeight.w700, color: Colors.white,
      ),
      headlineSmall: GoogleFonts.cinzel(
        fontSize: 24, fontWeight: FontWeight.w700, color: Colors.white,
      ),
      titleLarge: GoogleFonts.poppins(
        fontSize: 22, fontWeight: FontWeight.w600, color: Colors.white,
      ),
      titleMedium: GoogleFonts.poppins(
        fontSize: 18, fontWeight: FontWeight.w600, color: Colors.white,
      ),
      titleSmall: GoogleFonts.poppins(
        fontSize: 16, fontWeight: FontWeight.w600, color: Colors.white,
      ),
      bodyLarge: GoogleFonts.poppins(
        fontSize: 16, fontWeight: FontWeight.w400, color: Colors.white,
      ),
      bodyMedium: GoogleFonts.poppins(
        fontSize: 14, fontWeight: FontWeight.w400, color: Color(0xFFA0B0C9),
      ),
      bodySmall: GoogleFonts.poppins(
        fontSize: 12, fontWeight: FontWeight.w400, color: Color(0xFF8A9BB0),
      ),
      labelLarge: GoogleFonts.poppins(
        fontSize: 14, fontWeight: FontWeight.w600, color: Colors.white,
      ),
      labelMedium: GoogleFonts.poppins(
        fontSize: 12, fontWeight: FontWeight.w500, color: Colors.white,
      ),
      labelSmall: GoogleFonts.poppins(
        fontSize: 11, fontWeight: FontWeight.w500, color: Colors.white,
      ),
    ),
  );

  void toggleTheme() {
    // For now, we only have dark theme (the app is dark-themed by design)
    // Future: add light theme support
  }
}