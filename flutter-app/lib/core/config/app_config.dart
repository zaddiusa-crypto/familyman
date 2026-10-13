import 'package:flutter/foundation.dart';

class AppConfig {
  static const String appName = 'FamilyMan';
  static const String version = '1.0.0';

  // API Configuration
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: kReleaseMode
        ? 'https://api.familyman.app/api/v1'
        : 'http://10.0.2.2:8000/api/v1',
  );

  static const String wsUrl = String.fromEnvironment(
    'WS_BASE_URL',
    defaultValue: kReleaseMode
        ? 'wss://api.familyman.app/ws'
        : 'ws://10.0.2.2:8000/ws',
  );

  // Feature Flags
  static const bool enableAnalytics = kReleaseMode;
  static const bool enableCrashlytics = kReleaseMode;
  static const bool enableOfflineMode = true;
  static const bool enableBiometric = true;

  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 30);
  static const Duration sendTimeout = Duration(seconds: 30);

  // Storage
  static const int maxCacheSize = 100 * 1024 * 1024; // 100MB
  static const Duration cacheExpiry = Duration(days: 7);

  // Sync
  static const Duration syncInterval = Duration(minutes: 5);
  static const int maxSyncRetries = 5;
  static const Duration syncRetryBaseDelay = Duration(seconds: 10);

  // Notifications
  static const int maxNotificationRetries = 3;
  static const Duration notificationRetryDelay = Duration(minutes: 5);

  // Media
  static const int maxImageSize = 5 * 1024 * 1024; // 5MB
  static const int maxVideoSize = 50 * 1024 * 1024; // 50MB
  static const int imageCompressionQuality = 75;

  // Pagination
  static const int defaultPageSize = 20;
  static const int maxPageSize = 100;