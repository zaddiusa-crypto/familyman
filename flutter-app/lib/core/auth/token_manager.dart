import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:familyman/core/config/app_config.dart';

class TokenManager {
  static const _storage = FlutterSecureStorage();

  static const String _accessTokenKey = 'access_token';
  static const String _refreshTokenKey = 'refresh_token';
  static const String _lodgeIdKey = 'lodge_id';
  static const String _userIdKey = 'user_id';
  static const String _roleKey = 'role';
  static const String _autoLoginKey = 'auto_login';
  static const String _biometricEnabledKey = 'biometric_enabled';

  // Access Token
  static Future<void> saveAccessToken(String token) async {
    await _storage.write(key: _accessTokenKey, value: token);
  }

  static Future<String?> getAccessToken() async {
    return await _storage.read(key: _accessTokenKey);
  }

  static Future<void> clearAccessToken() async {
    await _storage.delete(key: _accessTokenKey);
  }

  // Refresh Token
  static Future<void> saveRefreshToken(String token) async {
    await _storage.write(key: _refreshTokenKey, value: token);
  }

  static Future<String?> getRefreshToken() async {
    return await _storage.read(key: _refreshTokenKey);
  }

  static Future<void> clearRefreshToken() async {
    await _storage.delete(key: _refreshTokenKey);
  }

  // Lodge ID
  static Future<void> saveLodgeId(String lodgeId) async {
    await _storage.write(key: _lodgeIdKey, value: lodgeId);
  }

  static Future<String?> getLodgeId() async {
    return await _storage.read(key: _lodgeIdKey);
  }

  // User ID
  static Future<void> saveUserId(String userId) async {
    await _storage.write(key: _userIdKey, value: userId);
  }

  static Future<String?> getUserId() async {
    return await _storage.read(key: _userIdKey);
  }

  // Role
  static Future<void> saveRole(String role) async {
    await _storage.write(key: _roleKey, value: role);
  }

  static Future<String?> getRole() async {
    return await _storage.read(key: _roleKey);
  }

  // Auto Login
  static Future<void> setAutoLogin(bool enabled) async {
    await _storage.write(key: _autoLoginKey, value: enabled.toString());
  }

  static Future<bool> getAutoLogin() async {
    final value = await _storage.read(key: _autoLoginKey);
    return value == 'true';
  }

  // Biometric
  static Future<void> setBiometricEnabled(bool enabled) async {
    await _storage.write(key: _biometricEnabledKey, value: enabled.toString());
  }

  static Future<bool> isBiometricEnabled() async {
    final value = await _storage.read(key: _biometricEnabledKey);
    return value == 'true';
  }

  // Clear All
  static Future<void> clearAll() async {
    await _storage.deleteAll();
  }

  // Check if logged in
  static Future<bool> isLoggedIn() async {
    final token = await getAccessToken();
    return token != null && token.isNotEmpty;
  }

  // Get all auth data
  static Future<Map<String, String?>> getAllAuthData() async {
    return {
      'access_token': await getAccessToken(),
      'refresh_token': await getRefreshToken(),
      'lodge_id': await getLodgeId(),
      'user_id': await getUserId(),
      'role': await getRole(),
    };
  }
}