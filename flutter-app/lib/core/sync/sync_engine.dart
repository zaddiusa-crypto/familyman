import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:drift/drift.dart';
import 'package:familyman/core/database/database.dart';
import 'package:familyman/core/network/dio_client.dart';
import 'package:familyman/core/auth/token_manager.dart';
import 'package:familyman/core/config/app_config.dart';

class SyncEngine {
  final Ref ref;
  bool _isSyncing = false;

  SyncEngine(this.ref);

  Future<void> syncAll() async {
    if (_isSyncing) return;
    _isSyncing = true;

    try {
      await _pushLocalChanges();
      await _pullRemoteChanges();
      await _resolveConflicts();
    } finally {
      _isSyncing = false;
    }
  }

  Future<void> _pushLocalChanges() async {
    final db = AppDatabase.instance;
    final dio = DioClient.instance;

    // Get pending sync entries
    final pending = await db.customSelect('''
      SELECT * FROM sync_outbox 
      WHERE status = 'pending' 
      ORDER BY created_at ASC 
      LIMIT 50
    ''').get();

    for (var entry in pending) {
      try {
        await _pushEntry(entry);
      } catch (e) {
        // Handle error, increment attempts
        print('Sync failed for ${entry.id}: $e');
      }
    }
  }

  Future<void> _pushEntry(Map<String, dynamic> entry) async {
    final dio = DioClient.instance;
    final table = entry['table_name'] as String;
    final operation = entry['operation'] as String;
    final payload = entry['payload'] as Map<String, dynamic>;
    final idempotencyKey = entry['idempotency_key'] as String;

    String endpoint;
    String method;

    switch (operation) {
      case 'INSERT':
        method = 'POST';
        endpoint = '/${table}s';
        break;
      case 'UPDATE':
        method = 'PATCH';
        endpoint = '/${table}s/${payload['id']}';
        break;
      case 'DELETE':
        method = 'DELETE';
        endpoint = '/${table}s/${payload['id']}';
        break;
      default:
        return;
    }

    try {
      await DioClient.instance.request(
        endpoint,
        options: Options(method: method),
        data: payload,
      );

      // Mark as completed
      await AppDatabase.instance.into(AppDatabase.instance.syncOutbox).insert(
        SyncOutboxCompanion(
          id: Value(entry['id']),
          status: const Value('completed'),
          processedAt: Value(DateTime.now()),
        ),
        mode: InsertMode.insertOrReplace,
      );
    } catch (e) {
      // Increment attempts
      // Handle error
    }
  }

  Future<void> _pullRemoteChanges() async {
    // Pull latest data from server
    // This would typically be done via a /sync endpoint
  }

  Future<void> _resolveConflicts() async {
    // Handle conflict resolution
    // Strategy: Last-write-wins with vector clocks
  }

  // Queue local changes for sync
  Future<void> queueChange({
    required String tableName,
    required String operation,
    required Map<String, dynamic> payload,
  }) async {
    final db = AppDatabase.instance;
    await db.into(db.syncOutbox).insert(SyncOutboxCompanion(
      id: Value(const Uuid().v4()),
      lodgeId: Value(await TokenManager.getLodgeId() ?? ''),
      userId: Value(await TokenManager.getUserId() ?? ''),
      tableName: Value(tableName),
      operation: Value(operation),
      payload: Value(payload),
      idempotencyKey: Value(const Uuid().v4()),
      status: const Value('pending'),
    ));
  }
}