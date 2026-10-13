import 'dart:io';
import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;
import 'package:sqlite3_flutter_libs/sqlite3_flutter_libs.dart';
import 'package:sqlite3/sqlite3.dart';

part 'database.g.dart';

// ============================================================
// TABLES
// ============================================================

class Users extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get email => text()();
  TextColumn get passwordHash => text()();
  TextColumn get fullName => text()();
  TextColumn get phone => text().nullable()();
  TextColumn get countryCode => text().nullable()();
  TextColumn get role => text().withDefault(const Constant('member'))();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  TextColumn get language => text().withDefault(const Constant('en'))();
  TextColumn get fcmTokens => text().map(const ListConverter()).withDefault(const Constant([]))();
  TextColumn get telegramChatId => text().nullable()();
  DateTimeColumn get lastLoginAt => dateTime().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Lodges extends Table {
  TextColumn get id => text()();
  TextColumn get name => text()();
  TextColumn get code => text()();
  TextColumn get country => text()();
  TextColumn get currency => text().withDefault(const Constant('KES'))();
  TextColumn get timezone => text().withDefault(const Constant('Africa/Nairobi'))();
  TextColumn get settings => text().map(const JsonMapConverter()).withDefault(const Constant({}))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Applications extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get userId => text()();
  TextColumn get fullName => text()();
  DateTimeColumn get dob => dateTime()();
  TextColumn get idNumber => text()();
  TextColumn get gender => text()();
  TextColumn get birthTown => text()();
  TextColumn get nickname => text().nullable()();
  TextColumn get country => text()();
  TextColumn get phone => text()();
  TextColumn get countryCode => text()();
  TextColumn get businessType => text().nullable()();
  TextColumn get businessLocation => text().nullable()();
  TextColumn get nearestLodge => text()();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  TextColumn get reviewedBy => text().nullable()();
  DateTimeColumn get reviewedAt => dateTime().nullable()();
  TextColumn get reviewNotes => text().nullable()();
  DateTimeColumn get submittedAt => dateTime()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Chats extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get memberId => text()();
  TextColumn get adminId => text().nullable()();
  TextColumn get subject => text().nullable()();
  DateTimeColumn get lastMessageAt => dateTime().nullable()();
  TextColumn get lastMessagePreview => text().nullable()();
  IntColumn get unreadAdmin => integer().withDefault(const Constant(0))();
  IntColumn get unreadMember => integer().withDefault(const Constant(0))();
  BoolColumn get isArchived => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Messages extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get chatId => text()();
  TextColumn get senderId => text()();
  TextColumn get content => text().nullable()();
  TextColumn get mediaUrl => text().nullable()();
  TextColumn get mediaType => text().nullable()();
  TextColumn get replyToId => text().nullable()();
  TextColumn get status => text().withDefault(const Constant('sent'))();
  BoolColumn get isDeleted => boolean().withDefault(const Constant(false))();
  TextColumn get deletedFor => text().map(const ListConverter()).withDefault(const Constant([]))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Notifications extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get userId => text()();
  TextColumn get type => text()();
  TextColumn get title => text()();
  TextColumn get body => text()();
  TextColumn get data => text().map(const JsonMapConverter()).withDefault(const Constant({}))();
  TextColumn get priority => text().withDefault(const Constant('normal'))();
  BoolColumn get isRead => boolean().withDefault(const Constant(false))();
  DateTimeColumn get readAt => dateTime().nullable()();
  TextColumn get sentVia => text().map(const ListConverter()).withDefault(const Constant([]))();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Announcements extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get authorId => text()();
  TextColumn get title => text()();
  TextColumn get content => text()();
  TextColumn get mediaUrls => text().map(const ListConverter()).withDefault(const Constant([]))();
  TextColumn get targetRoles => text().map(const ListConverter()).withDefault(const Constant(['member']))();
  BoolColumn get isPublished => boolean().withDefault(const Constant(true))();
  DateTimeColumn get publishedAt => dateTime().nullable()();
  DateTimeColumn get expiresAt => dateTime().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class FeeSchedules extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get name => text()();
  TextColumn get label => text()();
  TextColumn get description => text().nullable()();
  RealColumn get amount => real()();
  TextColumn get currency => text()();
  BoolColumn get isRequired => boolean().withDefault(const Constant(false))();
  IntColumn get sortOrder => integer().withDefault(const Constant(0))();
  BoolColumn get isActive => boolean().withDefault(const Constant(true))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class Payments extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get userId => text()();
  TextColumn get feeScheduleId => text().nullable()();
  RealColumn get amount => real()();
  TextColumn get currency => text()();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  TextColumn get method => text().nullable()();
  TextColumn get reference => text().nullable()();
  DateTimeColumn get paidAt => dateTime().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class SyncOutbox extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get userId => text()();
  TextColumn get tableName => text()();
  TextColumn get operation => text()();
  TextColumn get payload => text().map(const JsonMapConverter())();
  TextColumn get idempotencyKey => text()();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  IntColumn get attempts => integer().withDefault(const Constant(0))();
  TextColumn get lastError => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get processedAt => dateTime().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class AuditLogs extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get actorId => text()();
  TextColumn get action => text()();
  TextColumn get targetType => text().nullable()();
  TextColumn get targetId => text().nullable()();
  TextColumn get oldValues => text().map(const JsonMapConverter()).nullable()();
  TextColumn get newValues => text().map(const JsonMapConverter()).nullable()();
  TextColumn get ipAddress => text().nullable()();
  TextColumn get userAgent => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class FeeSchedules extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get name => text()();
  TextColumn get label => text()();
  TextColumn get description => text().nullable()();
  RealColumn get amount => real()();
  TextColumn get currency => text()();
  BoolColumn get isRequired => boolean().withDefault(const Constant(false))();
  IntColumn get sortOrder => integer().withDefault(const Constant(0))();
  BoolColumn get isActive => boolean().withDefault(const Constant(true))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

class FeeSchedulesAlias extends Table {
  TextColumn get id => text()();
  TextColumn get lodgeId => text()();
  TextColumn get name => text()();
  TextColumn get label => text()();
  TextColumn get description => text().nullable()();
  RealColumn get amount => real()();
  TextColumn get currency => text()();
  BoolColumn get isRequired => boolean().withDefault(const Constant(false))();
  IntColumn get sortOrder => integer().withDefault(const Constant(0))();
  BoolColumn get isActive => boolean().withDefault(const Constant(true))();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

// ============================================================
// CONVERTERS
// ============================================================

class ListConverter extends TypeConverter<List<String>, String> {
  const ListConverter();
  @override
  List<String> fromSql(String fromDb) {
    if (fromDb.isEmpty) return [];
    return fromDb.split(',').where((s) => s.isNotEmpty).toList();
  }

  @override
  String toSql(List<String> value) => value.join(',');
}

class JsonMapConverter extends TypeConverter<Map<String, dynamic>, String> {
  const JsonMapConverter();
  @override
  Map<String, dynamic> fromSql(String fromDb) {
    if (fromDb.isEmpty) return {};
    return json.decode(fromDb) as Map<String, dynamic>;
  }

  @override
  String toSql(Map<String, dynamic> value) => json.encode(value);
}

// ============================================================
// DATABASE CLASS
// ============================================================

@DriftDatabase(tables: [
  Users, Lodges, Applications, Chats, Messages,
  Notifications, Announcements, FeeSchedules, Payments,
  SyncOutbox, AuditLogs,
])
class AppDatabase extends _$AppDatabase {
  static AppDatabase? _instance;

  static Future<void> initialize() async {
    if (_instance != null) return;
    _instance = AppDatabase._();
    await _instance!.customSelect('PRAGMA foreign_keys = ON').get();
  }

  static AppDatabase get instance {
    if (_instance == null) {
      throw StateError('Database not initialized. Call AppDatabase.initialize() first.');
    }
    return _instance!;
  }

  AppDatabase._() : super(_openConnection());

  @override
  int get schemaVersion => 1;

  @override
  MigrationStrategy get migration => MigrationStrategy(
    onCreate: (Migrator m) async {
      await m.createAll();
    },
    onUpgrade: (Migrator m, int from, int to) async {
      // Handle migrations here
    },
  );
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'familyman.db'));
    if (Platform.isAndroid) {
      await applyWorkaroundToOpenSqlite3OnAndroid();
    }
    final cachebase = (await getTemporaryDirectory()).path;
    sqlite3.tempDirectory = cachebase;
    return NativeDatabase.createInBackground(file);
  });
}