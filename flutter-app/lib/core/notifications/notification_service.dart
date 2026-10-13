import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:timezone/data/latest.dart' as tz;
import 'package:timezone/timezone.dart' as tz;
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();
  static final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;

  static Future<void> initialize() async {
    // Initialize timezone
    tz.initializeTimeZones();
    tz.setLocalLocation(tz.getLocation('Africa/Nairobi'));

    // Initialize local notifications
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosInit = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    const initSettings = InitializationSettings(android: androidInit, iOS: iosInit);
    await _localNotifications.initialize(initSettings);

    // Create notification channels
    await _createChannels();

    // Initialize Firebase Messaging
    await _initFirebaseMessaging();

    // Request permissions
    await _requestPermissions();
  }

  static Future<void> _createChannels() async {
    const androidChannel = AndroidNotificationChannel(
      'mff_chat',
      'MFF Chat Messages',
      description: 'Notifications for chat messages',
      importance: Importance.high,
      playSound: true,
      enableVibration: true,
      vibrationPattern: Int64List.fromList([200, 100, 200]),
    );

    const androidAnnouncement = AndroidNotificationChannel(
      'mff_announcements',
      'MFF Announcements',
      description: 'Notifications for lodge announcements',
      importance: Importance.high,
      playSound: true,
      enableVibration: true,
    );

    const androidSystem = AndroidNotificationChannel(
      'mff_system',
      'MFF System',
      description: 'System notifications',
      importance: Importance.defaultImportance,
    );

    await _localNotifications.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>()?.createNotificationChannel(androidChannel);
    await _localNotifications.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>()?.createNotificationChannel(androidAnnouncement);
    await _localNotifications.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>()?.createNotificationChannel(androidSystem);
  }

  static Future<void> _initFirebaseMessaging() async {
    // Handle background messages
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Handle notification taps
    FirebaseMessaging.onMessageOpenedApp.listen(_handleMessageOpenedApp);

    // Get initial message if app opened from terminated state
    final initialMessage = await FirebaseMessaging.instance.getInitialMessage();
    if (initialMessage != null) {
      _handleMessageOpenedApp(initialMessage);
    }
  }

  static Future<void> _requestPermissions() async {
    await _firebaseMessaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
    );

    await _localNotifications
        .resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>()
        ?.requestPermissions(alert: true, badge: true, sound: true);
  }

  @pragma('vm:entry-point')
  static Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
    // Handle background message
    await _showLocalNotification(message);
  }

  static void _handleForegroundMessage(RemoteMessage message) {
    _showLocalNotification(message);
  }

  static void _handleMessageOpenedApp(RemoteMessage message) {
    // Navigate based on message data
    final data = message.data;
    // TODO: Navigate to appropriate screen
  }

  static Future<void> _showLocalNotification(RemoteMessage message) async {
    final notification = message.notification;
    final data = message.data;

    if (notification == null) return;

    final androidDetails = AndroidNotificationDetails(
      _getChannelId(data['type']),
      _getChannelName(data['type']),
      channelDescription: _getChannelDescription(data['type']),
      importance: Importance.high,
      priority: Priority.high,
      playSound: true,
      enableVibration: true,
      vibrationPattern: Int64List.fromList([200, 100, 200]),
      icon: '@mipmap/ic_launcher',
      largeIcon: const DrawableResourceAndroidBitmap('@mipmap/ic_launcher'),
      styleInformation: BigTextStyleInformation(
        message.notification?.body ?? '',
        contentTitle: message.notification?.title,
        summaryText: data['sender_name'],
      ),
      actions: [
        AndroidNotificationAction('reply', 'Reply'),
        AndroidNotificationAction('dismiss', 'Dismiss'),
      ],
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
      subtitle: data['sender_name'],
    );

    const details = NotificationDetails(android: androidDetails, iOS: iosDetails);

    await _localNotifications.show(
      message.hashCode,
      message.notification?.title,
      message.notification?.body,
      details,
      payload: jsonEncode(data),
    );
  }

  static String _getChannelId(String? type) {
    switch (type) {
      case 'chat':
        return 'mff_chat';
      case 'announcement':
        return 'mff_announcements';
      default:
        return 'mff_system';
    }
  }

  static String _getChannelName(String? type) {
    switch (type) {
      case 'chat':
        return 'MFF Chat Messages';
      case 'announcement':
        return 'MFF Announcements';
      default:
        return 'MFF System';
    }
  }

  static String _getChannelDescription(String? type) {
    switch (type) {
      case 'chat':
        return 'Notifications for chat messages';
      case 'announcement':
        return 'Notifications for lodge announcements';
      default:
        return 'System notifications';
    }
  }

  // Show local notification directly
  static Future<void> showNotification({
    required String title,
    required String body,
    String type = 'system',
    Map<String, dynamic>? data,
    int id = 0,
  }) async {
    final androidDetails = AndroidNotificationDetails(
      _getChannelId(type),
      _getChannelName(type),
      channelDescription: _getChannelDescription(type),
      importance: Importance.high,
      priority: Priority.high,
      playSound: true,
      enableVibration: true,
    );

    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );

    const details = NotificationDetails(android: androidDetails, iOS: iosDetails);

    await _localNotifications.show(
      id,
      title,
      body,
      details,
      payload: data != null ? jsonEncode(data) : null,
    );
  }

  // Set app badge
  static Future<void> setAppBadge(int count) async {
    // Android
    await _localNotifications
        .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
        ?.setBadgeCount(count);

    // iOS
    await _localNotifications
        .resolvePlatformSpecificImplementation<IOSFlutterLocalNotificationsPlugin>()
        ?.setBadgeNumber(count);
  }

  // Cancel notification
  static Future<void> cancelNotification(int id) async {
    await _localNotifications.cancel(id);
  }

  // Cancel all notifications
  static Future<void> cancelAllNotifications() async {
    await _localNotifications.cancelAll();
  }
}