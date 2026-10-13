import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:familyman/core/auth/token_manager.dart';
import 'package:familyman/core/network/dio_client.dart';
import 'package:familyman/shared/models/user_model.dart';

final authStateProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref);
});

class AuthState {
  final bool isLoggedIn;
  final bool isLoading;
  final UserModel? user;
  final String? error;

  const AuthState({
    this.isLoggedIn = false,
    this.isLoading = false,
    this.user,
    this.error,
  });

  AuthState copyWith({
    bool? isLoggedIn,
    bool? isLoading,
    UserModel? user,
    String? error,
  }) {
    return AuthState(
      isLoggedIn: isLoggedIn ?? this.isLoggedIn,
      isLoading: isLoading ?? this.isLoading,
      user: user ?? this.user,
      error: error ?? this.error,
    );
  }
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier(this.ref) : super(const AuthState()) {
    _checkAuthStatus();
  }

  final Ref ref;

  Future<void> _checkAuthStatus() async {
    state = state.copyWith(isLoading: true);

    try {
      final isLoggedIn = await TokenManager.isLoggedIn();
      if (isLoggedIn) {
        // Load user profile
        // final user = await _loadUserProfile();
        // state = state.copyWith(isLoggedIn: true, user: user, isLoading: false);
        // For now, just set logged in
        state = state.copyWith(isLoggedIn: true, isLoading: false);
      } else {
        state = state.copyWith(isLoggedIn: false, isLoading: false);
      }
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
    }
  }

  Future<void> login({
    required String email,
    required String password,
    bool rememberMe = false,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final dio = DioClient.instance;
      final response = await dio.post('/auth/login', data: {
        'email': email,
        'password': password,
        'remember_me': true,
      });

      final data = response.data;
      await _saveAuthData(
        accessToken: data['access_token'],
        refreshToken: data['refresh_token'],
        user: data['user'],
      );

      state = state.copyWith(isLoggedIn: true, isLoading: false, error: null);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      rethrow;
    }
  }

  Future<void> register({
    required String email,
    required String password,
    required String fullName,
    required String lodgeCode,
    required String country,
    required String phone,
    required String countryCode,
    Map<String, dynamic>? extraData,
  }) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final dio = DioClient.instance;
      final response = await dio.post('/auth/register', data: {
        'email': email,
        'password': password,
        'full_name': fullName,
        'lodge_code': lodgeCode,
        'country': country,
        'phone': phone,
        'country_code': countryCode,
        ...?extraData,
      });

      final data = response.data;
      await _saveAuthData(
        accessToken: data['access_token'],
        refreshToken: data['refresh_token'],
        user: data['user'],
      );

      state = state.copyWith(isLoggedIn: true, isLoading: false, error: null);
    } catch (e) {
      state = state.copyWith(isLoading: false, error: e.toString());
      rethrow;
    }
  }

  Future<void> logout() async {
    state = state.copyWith(isLoading: true);

    try {
      final dio = DioClient.instance;
      await dio.post('/auth/logout');
    } catch (e) {
      // Ignore logout errors
    }

    await TokenManager.clearAll();
    state = const AuthState(isLoggedIn: false, isLoading: false);
  }

  Future<void> refreshToken() async {
    try {
      final dio = DioClient.instance;
      final response = await dio.post('/auth/refresh', data: {
        'refresh_token': await TokenManager.getRefreshToken(),
      });

      final data = response.data;
      await _saveAuthData(
        accessToken: data['access_token'],
        refreshToken: data['refresh_token'],
      );
    } catch (e) {
      await logout();
      rethrow;
    }
  }

  Future<void> _saveAuthData({
    required String accessToken,
    required String refreshToken,
    Map<String, dynamic>? user,
  }) async {
    await TokenManager.saveAccessToken(accessToken);
    await TokenManager.saveRefreshToken(refreshToken);

    // TODO: Save user data when UserModel is implemented
  }
}