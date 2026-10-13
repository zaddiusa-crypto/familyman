import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:familyman/core/auth/token_manager.dart';
import 'package:familyman/core/auth/auth_provider.dart';
import 'package:familyman/core/network/dio_client.dart';
import 'package:familyman/core/database/database.dart';
import 'package:familyman/core/sync/sync_engine.dart';
import 'package:familyman/core/notifications/notification_service.dart';

// Auth
final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref);
});

// Dio Client
final dioProvider = Provider<Dio>((ref) {
  return DioClient.create();
});

// Database
final databaseProvider = Provider<AppDatabase>((ref) {
  return AppDatabase.instance;
});

// Token Manager
final tokenManagerProvider = Provider<TokenManager>((ref) {
  return TokenManager();
});

// Sync Engine
final syncEngineProvider = Provider<SyncEngine>((ref) {
  return SyncEngine(ref);
});

// Notification Service
final notificationServiceProvider = Provider<NotificationService>((ref) {
  return NotificationService();
});

// Auth State Provider (for router)
final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref);
});

// Current User Provider
final currentUserProvider = Provider<UserModel?>((ref) {
  final authState = ref.watch(authStateProvider);
  return authState.user;
});

// Is Admin Provider
final isAdminProvider = Provider<bool>((ref) {
  final user = ref.watch(currentUserProvider);
  return user?.isAdmin ?? false;
});

// Is Logged In Provider
final isLoggedInProvider = Provider<bool>((ref) {
  final authState = ref.watch(authStateProvider);
  return authState.isLoggedIn;
});

// Theme Provider
final themeProvider = StateNotifierProvider<ThemeNotifier, ThemeData>((ref) {
  return ThemeNotifier();
});