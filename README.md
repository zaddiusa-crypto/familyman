# FamilyMan - Masonry Family Fraternity Management System

A production-grade, multi-tenant lodge management system with offline-first Flutter mobile app and FastAPI backend.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUTTER APP (Android + iOS)              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Local SQLite │  │   Riverpod  │  │  Socket.io Client       │  │
│  │ (Drift)     │◄─►│  (State)    │◄─►│  (Real-time + FCM)      │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────────┬──────────┘  │
│         │                │                        │              │
│         │ Encrypted HTTPS (Dio + interceptors)   │              │
└─────────┼────────────────┼────────────────────────┼──────────────┘
          │                │                        │
          ▼                ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND (Render.com)                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   REST API  │  │  WebSocket  │  │  Background Workers       │  │
│  │  (JWT Auth) │  │  (Socket.io)│  │  (FCM, Sync, Cleanup)     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────────┬──────────┘  │
│         │                │                        │              │
│         ▼                ▼                        ▼              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              POSTGRESQL (Aiven) — Multi-tenant          │   │
│  │  users │ chats │ messages │ notifications │ apps │ etc  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   Cloudflare R2     │
                    │  (Media Storage)    │
                    └─────────────────────┘
```

## 🚀 Key Features

### 🏛️ Multi-Tenant Architecture (Lodge-Aware)
- **Row-Level Security** enforced at PostgreSQL level
- Each lodge isolated by `lodge_id` — zero data leakage
- Add new lodges without schema changes
- Super Admin manages all lodges; Lodge Admin manages own lodge

### 🔐 Authentication & Security
- **JWT RS256** with 15min access + 30d rotating refresh tokens
- Argon2id password hashing
- Biometric authentication (FaceID/TouchID/Fingerprint)
- Device fingerprinting & anomaly detection
- Admin impersonation with audit trail
- MFA support (TOTP + backup codes)

### 💬 Real-Time Chat
- Socket.io with tenant-scoped rooms (`lodge:{id}:chat:{id}`)
- Optimistic UI, read receipts, typing indicators
- Media support (images, videos, documents) via Cloudflare R2
- Swipe-to-reply, long-press menus, media gallery
- End-to-end encryption ready

### 🔔 Elite Notification System
- **FCM VAPID** direct (no OneSignal dependency)
- **Telegram Bot per admin** (direct DM for critical alerts)
- WhatsApp-style badges, preview, direct reply from notification
- Priority tiers: Critical → High → Normal
- Escalation: Unread > 15min → Telegram; > 1hr → Email
- Quiet hours per admin timezone

### 🌍 African-First Localization
- **15 languages**: English, Swahili, Luganda, Kinyarwanda, Portuguese, French, Zulu, Hausa, Twi, Amharic, Shona, Bemba, Tswana, Oshiwambo, Hindi
- **Country → Language auto-detection** (IP + SIM)
- Instant language switch, instant currency conversion
- RTL-ready for Arabic locales

### 📱 Offline-First Flutter App
- **Drift (SQLite)** local database with type-safe DAOs
- **Outbox pattern** for guaranteed sync
- Background isolate sync with WorkManager
- Conflict resolution: vector clocks + last-write-wins
- Full app works offline — chat, applications, announcements cached

### 🎨 Premium UI/UX
- **Design System**: Gold/Dark theme, Cinzel + Poppins fonts
- **Motion**: 200ms standard, 350ms complex animations
- **Accessibility**: Semantic labels, contrast, dynamic text, TalkBack/VoiceOver
- **Biometric login**, deep links, app shortcuts, widgets

## 📁 Project Structure

```
familyman/
├── .github/workflows/          # CI/CD pipelines
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── core/               # Config, security, database, RBAC
│   │   ├── modules/            # Feature modules
│   │   │   ├── auth/           # JWT, register, login, MFA
│   │   │   ├── users/          # Profile, roles, FCM, Telegram
│   │   │   ├── applications/   # Submit, review, fees
│   │   │   ├── chat/           # CRUD, messages, media
│   │   │   ├── notifications/  # CRUD, FCM, Telegram
│   │   │   ├── announcements/  # Rich media, targeting
│   │   │   ├── payments/       # Fee schedules, recording
│   │   │   ├── admin/          # Dashboard, broadcast, audit
│   │   │   ├── lodges/         # Multi-tenant management
│   │   │   └── media/          # R2 upload, signed URLs
│   │   ├── workers/            # Background tasks
│   │   └── ws/                 # Socket.io handlers
│   ├── alembic/                # Migrations
│   └── Dockerfile
├── flutter-app/                # Flutter Mobile App
│   ├── lib/
    │   ├── core/               # Config, DB, network, auth, sync, notifications, theme
    │   ├── features/           # Feature-first modules
    │   │   ├── auth/           # Login, register, biometric
    │   │   ├── dashboard/      # Profile, stats, announcements
    │   │   ├── requirements/   # Fees, currency, offline
    │   │   ├── application/    # Multi-step form, drafts
    │   │   ├── chat/           # List, conversation, media
    │   │   ├── notifications/  # List, filters, badges
    │   │   ├── members/        # Directory, profiles
    │   │   ├── payments/       # Fee tracking, receipts
    │   │   ├── documents/      # Vault, certificates
    │   │   ├── events/         # Calendar, reminders
    │   │   ├── polls/          # Surveys, voting
    │   │   ├── admin/          # Admin tab (lazy loaded)
    │   │   └── settings/       # Language, country, notifications
    │   └── shared/             # Models, widgets, providers
    ├── assets/                 # Fonts, icons, images
    └── android/ios/            # Native configs
├── shared/                     # Shared types (OpenAPI → Dart)
├── docker-compose.yml          # Local development
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Flutter 3.19+
- Python 3.11+
- Aiven PostgreSQL account
- Cloudflare R2 account
- Firebase project (FCM)
- Telegram Bot (@BotFather)

### Local Development

```bash
# 1. Clone and configure
git clone <repo>
cd familyman
cp backend/.env.example backend/.env
# Edit .env with your credentials

# 2. Start local stack
docker-compose up -d

# 3. Run backend
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# 4. Run Flutter app
cd ../flutter-app
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter run
```

### Environment Variables

See `backend/.env.example` for all required variables.

## 🧪 Testing

```bash
# Backend
cd backend
pytest -v --cov=app

# Flutter
cd flutter-app
flutter test --coverage
flutter analyze
```

## 🚢 Deployment

### Backend (Render.com)
1. Connect GitHub repo
2. Add environment variables
3. Auto-deploys on push to main

### Flutter App
- **Android**: GitHub Actions → Play Store Internal → Production
- **iOS**: GitHub Actions → TestFlight → App Store

## 📊 Monitoring

- **Sentry**: Error tracking (mobile + backend)
- **Prometheus/Grafana**: Metrics (Render provides)
- **UptimeRobot**: Uptime monitoring
- **Structured JSON logging** (Loki compatible)

## 🔐 Security

- Row-Level Security at database level
- JWT RS256 with short expiry + rotation
- Encrypted local storage (Flutter Secure Storage)
- TLS everywhere (Render + Cloudflare)
- Regular dependency scanning (Dependabot)

## 📝 License

Proprietary — Masonry Family Fraternity

---

**Built with ❤️ for the Brotherhood**