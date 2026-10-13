import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:badges/badges.dart' as badges;

import 'package:familyman/core/auth/auth_provider.dart';
import 'package:familyman/core/theme/app_theme.dart';
import 'package:familyman/shared/widgets/custom_button.dart';
import 'package:familyman/shared/widgets/custom_text_field.dart';
import 'package:familyman/features/auth/presentation/screens/login_screen.dart';
import 'package:familyman/features/auth/presentation/screens/register_screen.dart';
import 'package:familyman/features/dashboard/presentation/screens/dashboard_screen.dart';
import 'features/auth/presentation/screens/splash_screen.dart';
import 'features/application/presentation/screens/application_screen.dart';
import 'features/requirements/presentation/screens/requirements_screen.dart';
import 'features/chat/presentation/screens/chat_list_screen.dart';
import 'features/chat/presentation/screens/chat_screen.dart';
import 'features/notifications/presentation/screens/notifications_screen.dart';
import 'features/members/presentation/screens/members_screen.dart';
import 'features/requirements/presentation/screens/requirements_screen.dart';
import 'features/laws/presentation/screens/laws_screen.dart';
import 'features/help/presentation/screens/help_screen.dart';
import 'features/settings/presentation/screens/settings_screen.dart';
import 'features/admin/presentation/screens/admin_dashboard_screen.dart';
import 'shared/providers/app_providers.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize native services
  await initializeDateFormatting('en_US', null);

  // Initialize database
  await AppDatabase.initialize();

  // Initialize notifications
  await NotificationService.initialize();

  // Initialize Dio
  DioClient.initialize();

  runApp(const ProviderScope(child: FamilyManApp()));
}

final _router = GoRouter(
  initialLocation: '/splash',
  redirect: (context, state) {
    final authState = container.read(authStateProvider);
    final isLoggedIn = authState.isLoggedIn;
    final isAdmin = authState.user?.isAdmin ?? false;

    final publicPaths = ['/splash', '/login', '/register'];
    final isPublicPath = publicPaths.contains(state.matchedLocation);

    if (!isLoggedIn && !isPublicPath) {
      return '/login';
    }

    if (isLoggedIn && state.matchedLocation == '/login') {
      return '/dashboard';
    }

    // Admin routes
    final adminPaths = ['/admin', '/admin/*'];
    final isAdminPath = adminPaths.any((p) => state.matchedLocation.startsWith(p.replace('*', '')));
    if (isAdminPath && !isAdmin) {
      return '/dashboard';
    }

    return null;
  },
  routes: [
    GoRoute(path: '/splash', builder: (_, __) => const SplashScreen()),
    GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
    GoRoute(path: '/register', builder: (_, __) => const RegisterScreen()),
    GoRoute(path: '/dashboard', builder: (_, __) => const DashboardScreen()),
    GoRoute(path: '/requirements', builder: (_, __) => const RequirementsScreen()),
    GoRoute(path: '/application', builder: (_, __) => const ApplicationScreen()),
    GoRoute(
      path: '/chats',
      builder: (_, __) => const ChatListScreen(),
      routes: [
        GoRoute(
          path: ':chatId',
          builder: (context, state) => ChatScreen(chatId: state.pathParameters['chatId']!),
        ),
      ],
    ),
    GoRoute(path: '/notifications', builder: (_, __) => const NotificationsScreen()),
    GoRoute(path: '/members', builder: (_, __) => const MembersScreen()),
    GoRoute(path: '/laws', builder: (_, __) => const LawsScreen()),
    GoRoute(path: '/help', builder: (_, __) => const HelpScreen()),
    GoRoute(path: '/settings', builder: (_, __) => const SettingsScreen()),
    GoRoute(path: '/admin', builder: (_, __) => const AdminDashboardScreen()),
  ],
  errorBuilder: (context, state) => Scaffold(
    body: Center(child: Text('Page not found: ${state.error}')),
  ),
);

class FamilyManApp extends ConsumerWidget {
  const FamilyManApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = ref.watch(themeProvider);

    return MaterialApp.router(
      title: 'FamilyMan',
      routerConfig: _router,
      theme: theme,
      debugShowCheckedModeBanner: false,
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      supportedLocales: const [
        Locale('en', 'US'),
        Locale('sw', 'KE'),
        Locale('lg', 'UG'),
        Locale('rw', 'RW'),
        Locale('pt', 'BR'),
        Locale('fr', 'FR'),
        Locale('zu', 'ZA'),
        Locale('ha', 'NG'),
        Locale('tw', 'GH'),
        Locale('am', 'ET'),
        Locale('sn', 'ZW'),
        Locale('bem', 'ZM'),
        Locale('tn', 'BW'),
        Locale('ng', 'NA'),
        Locale('hi', 'IN'),
      ],
    );
  }
}