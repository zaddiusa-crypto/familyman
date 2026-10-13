import 'package:freezed_annotation/freezed_annotation.dart';

part 'user_model.freezed.dart';
part 'user_model.g.dart';

@freezed
class UserModel with _$UserModel {
  const factory UserModel({
    required String id,
    required String lodgeId,
    required String email,
    required String fullName,
    String? phone,
    String? countryCode,
    @Default('member') String role,
    @Default('pending') String status,
    @Default('en') String language,
    @Default([]) List<String> fcmTokens,
    String? telegramChatId,
    DateTime? lastLoginAt,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _UserModel;

  factory UserModel.fromJson(Map<String, dynamic> json) => _$UserModelFromJson(json);
}

@freezed
class LodgeModel with _$LodgeModel {
  const factory LodgeModel({
    required String id,
    required String name,
    required String code,
    required String country,
    @Default('KES') String currency,
    @Default('Africa/Nairobi') String timezone,
    @Default({}) Map<String, dynamic> settings,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _LodgeModel;

  factory LodgeModel.fromJson(Map<String, dynamic> json) => _$LodgeModelFromJson(json);
}

@freezed
class ApplicationModel with _$ApplicationModel {
  const factory ApplicationModel({
    required String id,
    required String lodgeId,
    required String userId,
    required String fullName,
    required DateTime dob,
    required String idNumber,
    required String gender,
    required String birthTown,
    String? nickname,
    required String country,
    required String phone,
    String? countryCode,
    String? businessType,
    String? businessLocation,
    required String nearestLodge,
    @Default('pending') String status,
    String? reviewedBy,
    DateTime? reviewedAt,
    String? reviewNotes,
    required DateTime submittedAt,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _ApplicationModel;

  factory ApplicationModel.fromJson(Map<String, dynamic> json) => _$ApplicationModelFromJson(json);
}

@freezed
class ChatModel with _$ChatModel {
  const factory ChatModel({
    required String id,
    required String lodgeId,
    required String memberId,
    String? adminId,
    String? subject,
    DateTime? lastMessageAt,
    String? lastMessagePreview,
    @Default(0) int unreadAdmin,
    @Default(0) int unreadMember,
    @Default(false) bool isArchived,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _ChatModel;

  factory ChatModel.fromJson(Map<String, dynamic> json) => _$ChatModelFromJson(json);
}

@freezed
class MessageModel with _$MessageModel {
  const factory MessageModel({
    required String id,
    required String lodgeId,
    required String chatId,
    required String senderId,
    String? content,
    String? mediaUrl,
    String? mediaType,
    String? replyToId,
    @Default('sent') String status,
    @Default(false) bool isDeleted,
    @Default([]) List<String> deletedFor,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _MessageModel;

  factory MessageModel.fromJson(Map<String, dynamic> json) => _$MessageModelFromJson(json);
}

@freezed
class NotificationModel with _$NotificationModel {
  const factory NotificationModel({
    required String id,
    required String lodgeId,
    required String userId,
    required String type,
    required String title,
    required String body,
    @Default({}) Map<String, dynamic> data,
    @Default('normal') String priority,
    @Default(false) bool isRead,
    DateTime? readAt,
    @Default([]) List<String> sentVia,
    required DateTime createdAt,
  }) = _NotificationModel;

  factory NotificationModel.fromJson(Map<String, dynamic> json) => _$NotificationModelFromJson(json);
}

@freezed
class AnnouncementModel with _$AnnouncementModel {
  const factory AnnouncementModel({
    required String id,
    required String lodgeId,
    required String authorId,
    required String title,
    required String content,
    @Default([]) List<String> mediaUrls,
    @Default(['member']) List<String> targetRoles,
    @Default(true) bool isPublished,
    DateTime? publishedAt,
    DateTime? expiresAt,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _AnnouncementModel;

  factory AnnouncementModel.fromJson(Map<String, dynamic> json) => _$AnnouncementModelFromJson(json);
}

@freezed
class FeeScheduleModel with _$FeeScheduleModel {
  const factory FeeScheduleModel({
    required String id,
    required String lodgeId,
    required String name,
    required String label,
    String? description,
    required double amount,
    required String currency,
    @Default(false) bool isRequired,
    @Default(0) int sortOrder,
    @Default(true) bool isActive,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _FeeScheduleModel;

  factory FeeScheduleModel.fromJson(Map<String, dynamic> json) => _$FeeScheduleModelFromJson(json);
}

@freezed
class PaymentModel with _$PaymentModel {
  const factory PaymentModel({
    required String id,
    required String lodgeId,
    required String userId,
    String? feeScheduleId,
    required double amount,
    required String currency,
    @Default('pending') String status,
    String? method,
    String? reference,
    DateTime? paidAt,
    required DateTime createdAt,
  }) = _PaymentModel;

  factory PaymentModel.fromJson(Map<String, dynamic> json) => _$PaymentModelFromJson(json);
}

@freezed
class ChatMessageModel with _$ChatMessageModel {
  const factory ChatMessageModel({
    required String id,
    required String chatId,
    required String senderId,
    String? content,
    String? mediaUrl,
    String? mediaType,
    String? replyToId,
    @Default('sent') String status,
    @Default(false) bool isDeleted,
    @Default([]) List<String> deletedFor,
    required DateTime createdAt,
    required DateTime updatedAt,
  }) = _ChatMessageModel;

  factory ChatMessageModel.fromJson(Map<String, dynamic> json) => _$ChatMessageModelFromJson(json);
}